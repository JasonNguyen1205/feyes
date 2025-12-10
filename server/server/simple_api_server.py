#!/usr/bin/env python3
"""
Simplified Visual AOI API Server
RESTful API server that handles inspection processing logic.
"""

import os
import sys
import json
import time
import uuid
import base64
import logging
import threading
import glob
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from werkzeug.serving import make_server
import cv2
import numpy as np
# from flask_cors import CORS  # Commented out - not available
from PIL import Image

# Try to import flasgger for Swagger documentation
try:
    from flasgger import Swagger
    SWAGGER_AVAILABLE = True
except ImportError:
    print("Flasgger not available - Swagger documentation will be disabled")
    SWAGGER_AVAILABLE = False
    Swagger = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import Visual AOI modules
try:
    from src.roi import get_rois
    from src.config import get_config_filename, set_product_name, get_product_name
    from src.inspection import capture_and_update, initialize_system
    from src.barcode_linking import get_linked_barcode_with_fallback
    MODULES_AVAILABLE = True
    logger.info("Visual AOI modules loaded successfully")
except ImportError as e:
    logger.warning(f"Some modules not available: {e}")
    MODULES_AVAILABLE = False

app = Flask(__name__)
# CORS(app)  # Enable CORS for cross-origin requests - commented out

# Configure shared folder path dynamically based on where server is running
SERVER_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SHARED_FOLDER_PATH = os.path.join(SERVER_BASE_DIR, 'shared')
logger.info(f"Server base directory: {SERVER_BASE_DIR}")
logger.info(f"Shared folder path: {SHARED_FOLDER_PATH}")

def validate_and_normalize_roi_for_save(roi):
    """
    Validate and normalize ROI configuration before saving to ensure correct v3.2 format.
    
    For Color ROIs (type 4), ensures all required fields are present:
    - expected_color: [R, G, B] array (required)
    - color_tolerance: int (default 10)
    - min_pixel_percentage: float (default 5.0)
    
    For other ROI types (1-3), ensures standard fields are present.
    
    Args:
        roi: ROI configuration dict from client
        
    Returns:
        Normalized ROI dict in v3.2 format
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    if not isinstance(roi, dict):
        raise ValueError("ROI must be a dictionary")
    
    # Required fields for all ROI types
    required_fields = ['idx', 'type', 'coords', 'focus', 'exposure', 'device_location']
    for field in required_fields:
        if field not in roi:
            raise ValueError(f"Missing required field: {field}")
    
    roi_type = roi['type']
    
    # Validate and normalize based on ROI type
    if roi_type == 4:
        # Color ROI - validate color configuration
        if 'expected_color' not in roi:
            raise ValueError("Color ROI (type 4) must have 'expected_color' field")
        
        expected_color = roi['expected_color']
        if not isinstance(expected_color, (list, tuple)) or len(expected_color) != 3:
            raise ValueError("'expected_color' must be an array of 3 RGB values [R, G, B]")
        
        # Ensure color values are integers 0-255
        try:
            expected_color = [int(c) for c in expected_color]
            if not all(0 <= c <= 255 for c in expected_color):
                raise ValueError("Color values must be between 0 and 255")
            roi['expected_color'] = expected_color
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid color values: {e}")
        
        # Set defaults for optional Color ROI fields
        roi.setdefault('color_tolerance', 10)
        roi.setdefault('min_pixel_percentage', 5.0)
        
        # Validate tolerance and percentage
        try:
            roi['color_tolerance'] = int(roi['color_tolerance'])
            if roi['color_tolerance'] < 0:
                raise ValueError("color_tolerance must be non-negative")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid color_tolerance: {e}")
        
        try:
            roi['min_pixel_percentage'] = float(roi['min_pixel_percentage'])
            if not 0 <= roi['min_pixel_percentage'] <= 100:
                raise ValueError("min_pixel_percentage must be between 0 and 100")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid min_pixel_percentage: {e}")
        
        # Color ROIs should have null for fields used by other types
        roi['ai_threshold'] = None
        roi['feature_method'] = None
        roi['expected_text'] = None
        roi['is_device_barcode'] = None
        
    elif roi_type in [1, 2, 3]:
        # Barcode, Compare, or OCR ROI
        # Set defaults for standard fields
        roi.setdefault('rotation', 0)
        roi.setdefault('ai_threshold', 0.85 if roi_type == 2 else None)
        roi.setdefault('feature_method', 'mobilenet' if roi_type == 2 else None)
        roi.setdefault('expected_text', None)
        roi.setdefault('is_device_barcode', None)
        
        # Ensure Color ROI fields are not present
        for color_field in ['expected_color', 'color_tolerance', 'min_pixel_percentage', 'color_ranges']:
            if color_field in roi:
                del roi[color_field]
    else:
        raise ValueError(f"Invalid ROI type: {roi_type}. Must be 1 (Barcode), 2 (Compare), 3 (OCR), or 4 (Color)")
    
    # Validate common fields
    try:
        roi['idx'] = int(roi['idx'])
        roi['type'] = int(roi['type'])
        roi['focus'] = int(roi['focus'])
        roi['exposure'] = int(roi['exposure'])
        roi['device_location'] = int(roi['device_location'])
        roi['rotation'] = int(roi.get('rotation', 0))
        
        # Validate coords
        coords = roi['coords']
        if not isinstance(coords, (list, tuple)) or len(coords) != 4:
            raise ValueError("'coords' must be an array of 4 values [x1, y1, x2, y2]")
        roi['coords'] = [int(c) for c in coords]
        
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid field value: {e}")
    
    return roi

def normalize_device_barcodes(device_barcodes):
    """
    Normalize device_barcodes to dict format.
    
    Accepts:
    - Dict format: {'1': 'barcode1', '2': 'barcode2'}
    - List format: [{'device_id': 1, 'barcode': 'barcode1'}, {'device_id': 2, 'barcode': 'barcode2'}]
    
    Returns: Dict format with string keys
    """
    if not device_barcodes:
        return {}
    
    if isinstance(device_barcodes, dict):
        # Already in dict format, just ensure string keys
        return {str(k): v for k, v in device_barcodes.items()}
    
    if isinstance(device_barcodes, list):
        # Convert list format to dict format
        result = {}
        for item in device_barcodes:
            if isinstance(item, dict) and 'device_id' in item and 'barcode' in item:
                result[str(item['device_id'])] = item['barcode']
        return result
    
    logger.warning(f"Unexpected device_barcodes format: {type(device_barcodes)}")
    return {}

# Swagger configuration
if SWAGGER_AVAILABLE:
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    # Get server hostname/IP dynamically
    # This allows Swagger UI to work correctly for both local and external access
    import socket
    
    def get_network_ip():
        """Get the actual network IP address (not localhost)."""
        try:
            # Create a socket to determine the actual network IP
            # This works by connecting to an external address (doesn't actually send data)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                # Fallback: try to get hostname's IP
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                # Avoid returning localhost
                if ip != "127.0.0.1" and not ip.startswith("127."):
                    return ip
            except Exception:
                pass
            return None
    
    network_ip = get_network_ip()
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Visual AOI Server API",
            "description": "RESTful API server for Visual AOI inspection processing",
            "contact": {
                "responsibleOrganization": "Visual AOI Team",
                "responsibleDeveloper": "Development Team",
                "email": "support@visualaoi.com",
                "url": "https://visualaoi.com",
            },
            "termsOfService": "https://visualaoi.com/terms",
            "version": "1.0.0"
        },
        # Don't set host - let Swagger UI use the browser's current host
        # This makes it work correctly for both local and external access
        # "host": f"{network_ip}:5000" if network_ip else "localhost:5000",
        "basePath": "/",
        "schemes": ["http", "https"],
        "consumes": ["application/json"],
        "produces": ["application/json"]
    }

    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    print(f"Swagger documentation enabled at /apidocs/")
    if network_ip:
        print(f"Server network IP: {network_ip} (Swagger will use browser's hostname)")
    else:
        print(f"Swagger will use browser's current hostname dynamically")
else:
    print("Swagger documentation disabled - flasgger not available")

# Global state for the server
server_state = {
    'initialized': False,
    'current_product': None,
    'inspection_in_progress': False,
    'sessions': {}
}

class InspectionSession:
    """Represents an inspection session."""
    
    def __init__(self, session_id: str, product_name: str, client_info: dict = None):
        self.session_id = session_id
        self.product_name = product_name
        self.client_info = client_info or {}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.inspection_count = 0
        self.last_results = None
        
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'product_name': self.product_name,
            'client_info': self.client_info,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'inspection_count': self.inspection_count
        }

def decode_base64_image(base64_data: str) -> np.ndarray:
    """Decode base64 image data to OpenCV format."""
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:image/'):
            base64_data = base64_data.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(base64_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image data")
            
        return image
        
    except Exception as e:
        logger.error(f"Failed to decode base64 image: {e}")
        raise ValueError(f"Invalid image data: {e}")

def load_image_from_request(data: dict, session_id: str) -> Tuple[np.ndarray, str]:
    """
    Load image from request data, prioritizing file paths over Base64.
    
    This function supports two methods:
    1. **File path (PREFERRED)**: Client saves image to shared folder and sends filename
       - Faster (no Base64 encoding overhead)
       - Smaller payload (99% reduction)
       - Better for large images
    2. **Base64 (LEGACY)**: Client sends Base64 encoded image data
       - Backward compatibility
       - Easier for clients without shared folder access
    
    Args:
        data: Request JSON data containing either 'image_filename' or 'image'
        session_id: Session UUID for constructing file paths
    
    Returns:
        Tuple of (cv_image, source_method) where source_method is 'file' or 'base64'
    
    Raises:
        ValueError: If neither valid file path nor Base64 data provided
    """
    # Method 1: Try file path first (PREFERRED)
    if 'image_filename' in data:
        image_filename = data['image_filename']
        
        # Construct path to shared input directory
        session_dir = os.path.join(SHARED_FOLDER_PATH, "sessions", session_id)
        input_dir = os.path.join(session_dir, "input")
        image_path = os.path.join(input_dir, image_filename)
        
        # Validate file exists
        if not os.path.exists(image_path):
            raise ValueError(f"Image file not found: {image_filename} (expected at {image_path})")
        
        # Read image
        cv_image = cv2.imread(image_path)
        if cv_image is None:
            raise ValueError(f"Failed to read image file: {image_filename}")
        
        logger.info(f"✓ Loaded image from file path: {image_filename} (size: {cv_image.shape})")
        return cv_image, 'file'
    
    # Method 2: Fall back to Base64 (LEGACY)
    elif 'image' in data:
        image_data = data['image']
        cv_image = decode_base64_image(image_data)
        
        logger.info(f"⚠ Loaded image from Base64 data (size: {cv_image.shape}) - Consider using file paths for better performance")
        return cv_image, 'base64'
    
    else:
        raise ValueError("No image data provided. Send either 'image_filename' (preferred) or 'image' (Base64)")

def encode_image_to_base64(image: np.ndarray, format: str = 'JPEG') -> str:
    """Encode OpenCV image to base64."""
    try:
        # Encode image to bytes
        if format.upper() == 'PNG':
            _, buffer = cv2.imencode('.png', image)
            mime_type = 'image/png'
        else:
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            mime_type = 'image/jpeg'
        
        # Convert to base64
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:{mime_type};base64,{image_base64}"
        
    except Exception as e:
        logger.error(f"Failed to encode image to base64: {e}")
        raise ValueError(f"Image encoding failed: {e}")

def get_available_products() -> List[Dict]:
    """Get list of available products from config directory."""
    try:
        products = []
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config', 'products')
        
        if os.path.exists(config_dir):
            # Look for direct JSON files in the products directory
            for product_file in glob.glob(os.path.join(config_dir, '*.json')):
                product_name = os.path.splitext(os.path.basename(product_file))[0]
                
                try:
                    with open(product_file, 'r') as f:
                        config_data = json.load(f)
                    
                    products.append({
                        'product_name': product_name,
                        'config_file': product_file,
                        'description': config_data.get('description', f'Product configuration for {product_name}')
                    })
                except Exception as e:
                    logger.warning(f"Failed to read product config {product_file}: {e}")
            
            # Look for subdirectories containing rois_config_<name>.json files
            for item in os.listdir(config_dir):
                item_path = os.path.join(config_dir, item)
                if os.path.isdir(item_path):
                    # Look for rois_config_<name>.json file in the subdirectory
                    config_file = os.path.join(item_path, f'rois_config_{item}.json')
                    if os.path.exists(config_file):
                        try:
                            with open(config_file, 'r') as f:
                                config_data = json.load(f)
                            
                            # Handle different config formats
                            if isinstance(config_data, list):
                                # Current format: list of ROI objects with property names
                                # Each ROI is {"idx": 1, "type": 2, "coords": [...], ...}
                                description = f'Product configuration for {item}'
                            elif isinstance(config_data, dict):
                                # Alternative format: dict wrapper with description field (not currently used)
                                description = config_data.get('description', f'Product configuration for {item}')
                            else:
                                # Unknown format
                                description = f'Product configuration for {item}'
                            
                            products.append({
                                'product_name': item,
                                'config_file': config_file,
                                'description': description
                            })
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON in {config_file}: {e}")
                        except Exception as e:
                            logger.warning(f"Failed to read product config {config_file}: {e}")
        
        # If no products found, create a default one
        if not products:
            products.append({
                'product_name': 'default',
                'config_file': None,
                'description': 'Default product configuration'
            })
            
        logger.info(f"Found {len(products)} products: {[p['product_name'] for p in products]}")
        return products
        
    except Exception as e:
        logger.error(f"Failed to get available products: {e}")
        return [{'product_name': 'default', 'config_file': None, 'description': 'Default product'}]

def simulate_inspection(image: np.ndarray, device_barcode: Optional[str] = None, device_barcodes: Optional[Dict] = None) -> Dict:
    """Simulate inspection when real modules are not available."""
    logger.info("Running simulated inspection")
    print(f"DEBUG simulate_inspection: device_barcode={device_barcode}, device_barcodes={device_barcodes}")
    
    # Simulate processing time
    time.sleep(1)
    
    # Create mock results
    roi_results = []
    device_summaries = {}
    
    # Mock ROI results
    has_barcode_roi = False
    for i in range(4):  # Simulate 4 ROIs
        # Skip barcode ROI when manual barcodes are provided to test manual input
        if (device_barcode or device_barcodes) and i % 3 == 1:  # Skip barcode ROI type when manual barcode provided
            roi_type = 'compare'  # Use compare instead of barcode
        else:
            roi_type = ['compare', 'barcode', 'ocr'][i % 3]
        passed = True  # All pass for simulation
        
        # Assign device ID (alternate between devices 1 and 2)
        device_id = (i % 2) + 1
        
        if roi_type == 'barcode':
            has_barcode_roi = True
            result = {
                'roi_id': i + 1,
                'device_id': device_id,
                'roi_type_name': roi_type,
                'passed': passed,
                'barcode_values': f"TEST{123456 + i}",
                'coordinates': [100 + i*200, 100, 150 + i*200, 150]
            }
        elif roi_type == 'ocr':
            result = {
                'roi_id': i + 1,
                'device_id': device_id,
                'roi_type_name': roi_type,
                'passed': passed,
                'ocr_text': f"Text {i+1}",
                'coordinates': [100 + i*200, 200, 200 + i*200, 250]
            }
        else:  # compare
            result = {
                'roi_id': i + 1,
                'device_id': device_id,
                'roi_type_name': roi_type,
                'passed': passed,
                'match_result': 'MATCH',
                'ai_similarity': 0.95 + i*0.01,
                'coordinates': [100 + i*200, 300, 200 + i*200, 400]
            }
            
        roi_results.append(result)
    
    # Create device summaries based on actual ROI assignment
    for device_id in [1, 2]:
        print(f"DEBUG: Processing device {device_id}")
        
        # Initialize with default
        barcode_value = 'N/A'
        
        # First try to use simulated ROI barcode (if no manual barcodes skip barcode ROI)
        if has_barcode_roi and not (device_barcode or device_barcodes):
            # Simulate ROI-detected barcode
            barcode_value = f"ROI_DETECTED_{123456 + device_id}"
            print(f"DEBUG: Using simulated ROI barcode for device {device_id}: {barcode_value}")
        else:
            # Check for manual device barcodes first
            if device_barcodes:
                print(f"DEBUG: device_barcodes provided: {device_barcodes}")
                # Normalize device_barcodes format
                normalized_barcodes = normalize_device_barcodes(device_barcodes)
                for key, value in normalized_barcodes.items():
                    print(f"DEBUG: Checking key={key} (type={type(key)}), value={value}")
                    if int(key) == device_id:
                        barcode_value = value
                        logger.info(f"Using multi-device barcode for device {device_id}: {barcode_value}")
                        print(f"DEBUG: Found multi-device barcode for device {device_id}: {barcode_value}")
                        break
            # Legacy single barcode fallback
            elif device_barcode:
                barcode_value = device_barcode
                logger.info(f"Using legacy single barcode for device {device_id}: {barcode_value}")
                print(f"DEBUG: Using legacy single barcode for device {device_id}: {barcode_value}")
            # Default simulated barcode if no manual input and no ROI
            elif not has_barcode_roi:
                barcode_value = f"TEST{123456 + device_id}"
                print(f"DEBUG: Using default simulated barcode for device {device_id}: {barcode_value}")
        
        print(f"DEBUG: Final barcode_value for device {device_id}: {barcode_value}")
        
        # Get ROIs for this device
        device_rois = [roi for roi in roi_results if roi.get('device_id') == device_id]
        passed_rois = sum(1 for roi in device_rois if roi.get('passed', False))
        
        device_summaries[device_id] = {
            'total_rois': len(device_rois),
            'passed_rois': passed_rois,
            'failed_rois': len(device_rois) - passed_rois,
            'device_passed': passed_rois == len(device_rois),
            'barcode': barcode_value,
            'results': device_rois
        }
    
    return {
        'roi_results': roi_results,
        'device_summaries': device_summaries,
        'overall_result': {
            'passed': True,
            'total_rois': len(roi_results),
            'passed_rois': len(roi_results),
            'failed_rois': 0
        },
        'processing_time': 1.0
    }

def determine_ocr_passed_status(ocr_text: str) -> bool:
    """Determine if OCR result should be considered passed based on our substring matching logic."""
    if not ocr_text:
        return False
    
    # Import the inspection module's is_roi_passed function
    try:
        from src.inspection import is_roi_passed
        # Create a mock ROI result tuple for OCR type (type 3)
        # Format: (roi_id, roi_type, golden_img, roi_img, coordinates, type_name, data, ...)
        mock_roi_result = (1, 3, None, None, [0, 0, 0, 0], 'ocr', ocr_text)
        return is_roi_passed(mock_roi_result)
    except ImportError:
        # Fallback: check for PASS/FAIL markers in the OCR text
        ocr_text = ocr_text.strip()
        if "[FAIL:" in ocr_text:
            return False
        elif "[PASS:" in ocr_text:
            return True
        else:
            # For OCR without sample text comparison, just check if text was detected
            return bool(ocr_text)

def process_roi_wrapper(roi_data: Tuple) -> Optional[Tuple]:
    """Wrapper function to process a single ROI in parallel execution.
    
    Args:
        roi_data: Tuple of (roi, image, product_name, process_roi_func)
        
    Returns:
        Result tuple from process_roi or None on error
    """
    roi, image, product_name, process_roi_func = roi_data
    try:
        result = process_roi_func(roi, image, product_name)
        return result
    except Exception as e:
        roi_id = roi[0] if roi and len(roi) > 0 else 'unknown'
        logger.error(f"Error processing ROI {roi_id} in parallel: {e}")
        return None

def run_real_inspection(image: np.ndarray, product_name: Optional[str] = None, device_barcode: Optional[str] = None, device_barcodes: Optional[Dict] = None, session_id: Optional[str] = None, filter_focus: Optional[int] = None, filter_exposure: Optional[int] = None) -> Dict:
    """Run real Visual AOI inspection using src modules with parallel ROI processing.
    
    Args:
        image: Input image as numpy array
        product_name: Name of the product configuration
        device_barcode: Legacy single barcode
        device_barcodes: Dictionary of barcodes per device
        session_id: Session identifier
        filter_focus: If specified, only process ROIs with this focus value
        filter_exposure: If specified, only process ROIs with this exposure value
    """
    logger.info(f"Running real inspection for product: {product_name}, session: {session_id}")
    if filter_focus is not None or filter_exposure is not None:
        logger.info(f"Filtering ROIs by focus={filter_focus}, exposure={filter_exposure}")
    
    try:
        # Import the inspection modules
        from src.inspection import process_roi, initialize_system
        from src.roi import get_rois, load_rois_from_config
        from src.config import PRODUCT_NAME, set_product_name
        
        # Set the product if specified
        if product_name:
            try:
                set_product_name(product_name)
            except Exception as e:
                logger.warning(f"Could not set product name: {e}")
            # Load ROI configuration for this product
            load_rois_from_config(product_name)
        
        # Initialize system if needed
        if not initialize_system():
            logger.warning("System initialization failed, using placeholder results")
            return simulate_inspection(image, device_barcode, device_barcodes)
        
        # Get ROI configuration
        all_rois = get_rois()
        if not all_rois:
            logger.warning(f"No ROIs configured for product {product_name or 'unknown'}, using simulation results")
            return simulate_inspection(image, device_barcode, device_barcodes)
        
        # Filter ROIs by focus and exposure if specified (for grouped inspection)
        rois = []
        if filter_focus is not None or filter_exposure is not None:
            for roi in all_rois:
                if roi is None or not isinstance(roi, (list, tuple)) or len(roi) < 5:
                    continue
                
                # ROI structure: (idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, ...)
                roi_focus = roi[3]
                roi_exposure = roi[4]
                
                # Match both focus and exposure if both filters are specified
                if filter_focus is not None and filter_exposure is not None:
                    if roi_focus == filter_focus and roi_exposure == filter_exposure:
                        rois.append(roi)
                # Match only focus if only focus filter is specified
                elif filter_focus is not None and roi_focus == filter_focus:
                    rois.append(roi)
                # Match only exposure if only exposure filter is specified
                elif filter_exposure is not None and roi_exposure == filter_exposure:
                    rois.append(roi)
            
            logger.info(f"Filtered to {len(rois)} ROIs matching focus={filter_focus}, exposure={filter_exposure} (from {len(all_rois)} total)")
        else:
            rois = all_rois
        
        if not rois:
            logger.warning(f"No ROIs match the filter criteria (focus={filter_focus}, exposure={filter_exposure})")
            return {'roi_results': [], 'overall_result': {'passed': True, 'total_rois': 0, 'passed_rois': 0, 'failed_rois': 0}}
        
        logger.info(f"Processing {len(rois)} ROIs in parallel")
        
        # Process ROIs in parallel using ThreadPoolExecutor
        roi_results = []
        total_passed = 0
        
        # Determine optimal number of workers (min of ROI count and CPU count)
        max_workers = min(len(rois), os.cpu_count() or 4)
        logger.info(f"Using {max_workers} parallel workers for {len(rois)} ROIs")
        
        # Prepare data for parallel processing
        roi_data_list = [(roi, image, product_name or PRODUCT_NAME, process_roi) for roi in rois]
        
        # Process all ROIs in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all ROI processing tasks
            future_to_roi = {executor.submit(process_roi_wrapper, roi_data): roi_data[0] for roi_data in roi_data_list}
            
            # Collect results as they complete
            for future in as_completed(future_to_roi):
                roi = future_to_roi[future]
                try:
                    result = future.result()
                    
                    if result:
                        # Parse the result tuple based on ROI type
                        # Barcode: (idx, 1, roi_img, None, coords, "Barcode", data)
                        # OCR: (idx, 3, roi_img, None, coords, "OCR", data, rotation)
                        # Compare: (idx, 2, roi_img, golden_img, coords, "Compare", result, color, similarity, threshold)
                        roi_id, roi_type, roi_img, golden_img, coordinates, type_name, data, *extra = result
                        
                        # Get device information from the original ROI
                        device_id = 1  # Default device
                        try:
                            # ROI structure: (idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location)
                            for roi_data in rois:
                                if roi_data is not None and len(roi_data) >= 9 and roi_data[0] == roi_id:
                                    device_id = roi_data[8]  # device_location is at index 8
                                    break
                        except Exception as e:
                            logger.warning(f"Failed to extract device info for ROI {roi_id}: {e}")
                        
                        # Convert to consistent format
                        roi_result = {
                            'roi_id': roi_id,
                            'device_id': device_id,
                            'roi_type_name': type_name.lower() if type_name else 'unknown',
                            'coordinates': list(coordinates) if coordinates else [0, 0, 0, 0]
                        }
                        
                        # Save ROI and golden images to shared folder and return paths
                        # IMPORTANT: These are the EXACT images used for comparison (roi_img = captured crop, golden_img = resized golden)
                        if roi_img is not None and session_id:
                            try:
                                # Save the EXACT captured ROI image used for comparison
                                session_dir = os.path.join(SHARED_FOLDER_PATH, "sessions", session_id)
                                output_dir = os.path.join(session_dir, "output")
                                os.makedirs(output_dir, exist_ok=True)
                                
                                roi_image_filename = f"roi_{roi_id}.jpg"
                                roi_image_path = os.path.join(output_dir, roi_image_filename)
                                cv2.imwrite(roi_image_path, roi_img)  # roi_img is the exact crop used for comparison
                                
                                # Return full client-accessible path with mount prefix
                                roi_result['roi_image_path'] = f"/mnt/visual-aoi-shared/sessions/{session_id}/output/{roi_image_filename}"
                                logger.debug(f"Saved exact captured ROI image for ROI {roi_id}: {roi_image_filename}")
                            except Exception as e:
                                logger.warning(f"Failed to save ROI image for {roi_id}: {e}")
                                roi_result['roi_image_path'] = None
                        else:
                            roi_result['roi_image_path'] = None
                            
                        if golden_img is not None and session_id:
                            try:
                                # Save the EXACT golden image used for comparison (already resized to match ROI)
                                golden_image_filename = f"golden_{roi_id}.jpg"
                                golden_image_path = os.path.join(output_dir, golden_image_filename)
                                cv2.imwrite(golden_image_path, golden_img)  # golden_img is the exact resized golden used
                                
                                # Return full client-accessible path with mount prefix
                                roi_result['golden_image_path'] = f"/mnt/visual-aoi-shared/sessions/{session_id}/output/{golden_image_filename}"
                                logger.debug(f"Saved exact golden image for ROI {roi_id}: {golden_image_filename}")
                            except Exception as e:
                                logger.warning(f"Failed to save golden image for {roi_id}: {e}")
                                roi_result['golden_image_path'] = None
                        else:
                            roi_result['golden_image_path'] = None
                    
                        # Parse results based on ROI type
                        if roi_type == 1:  # Barcode
                            # Ensure barcode_values is sent as a list for client compatibility
                            # Handle both list and string inputs
                            if isinstance(data, list):
                                barcode_list = [str(b).strip() for b in data if b]
                            elif data:
                                barcode_list = [str(data).strip()]
                            else:
                                barcode_list = []
                            roi_result.update({
                                'barcode_values': barcode_list,
                                'passed': bool(barcode_list)
                            })
                        elif roi_type == 2:  # Compare
                            # data is now the match result ("Match"/"Different"), extra contains [color, similarity, threshold]
                            color = extra[0] if extra and len(extra) > 0 else (0, 0, 0)
                            similarity = extra[1] if extra and len(extra) > 1 else 0.0
                            threshold = extra[2] if extra and len(extra) > 2 else 0.9
                            roi_result.update({
                                'match_result': str(data) if data else "No Match",
                                'ai_similarity': float(similarity),
                                'threshold': float(threshold),
                                'passed': float(similarity) >= float(threshold)
                            })
                        elif roi_type == 3:  # OCR
                            ocr_text = str(data) if data else ""
                            roi_result.update({
                                'ocr_text': ocr_text,
                                'passed': determine_ocr_passed_status(ocr_text)
                            })
                        elif roi_type == 4:  # Color Check
                            # data is a dict with color check results
                            if isinstance(data, dict):
                                roi_result.update({
                                    'detected_color': data.get('detected_color', 'Unknown'),
                                    'match_percentage': data.get('match_percentage', 0.0),
                                    'dominant_color': data.get('dominant_color', [0, 0, 0]),
                                    'threshold': data.get('threshold', 50.0),
                                    'passed': data.get('passed', False)
                                })
                            else:
                                roi_result.update({
                                    'detected_color': 'Error',
                                    'match_percentage': 0.0,
                                    'dominant_color': [0, 0, 0],
                                    'passed': False
                                })
                        else:
                            roi_result.update({
                                'result': str(data) if data else "",
                                'passed': bool(data)
                            })
                        
                        roi_results.append(roi_result)
                        if roi_result.get('passed', False):
                            total_passed += 1
                            
                    else:
                        # Failed to process ROI - result is None
                        roi_results.append({
                            'roi_id': roi[0] if roi else len(roi_results) + 1,
                            'roi_type_name': 'unknown',
                            'passed': False,
                            'error': 'Processing failed',
                            'coordinates': [0, 0, 0, 0]
                        })
                        
                except Exception as roi_error:
                    logger.error(f"Error processing ROI {roi[0] if roi else 'unknown'}: {roi_error}")
                    roi_results.append({
                        'roi_id': roi[0] if roi else len(roi_results) + 1,
                        'roi_type_name': 'error',
                        'passed': False,
                        'error': str(roi_error),
                        'coordinates': [0, 0, 0, 0]
                    })
        
        # Group results by device ID
        device_summaries = {}
        for roi_result in roi_results:
            device_id = roi_result.get('device_id', 1)
            
            if device_id not in device_summaries:
                device_summaries[device_id] = {
                    'total_rois': 0,
                    'passed_rois': 0,
                    'failed_rois': 0,
                    'device_passed': True,
                    'results': []
                }
            
            device_summaries[device_id]['results'].append(roi_result)
            device_summaries[device_id]['total_rois'] += 1
            
            if roi_result.get('passed', False):
                device_summaries[device_id]['passed_rois'] += 1
            else:
                device_summaries[device_id]['failed_rois'] += 1
                device_summaries[device_id]['device_passed'] = False
        
        # Add barcode info to device summaries
        barcode_results = [r for r in roi_results if r.get('roi_type_name') == 'barcode']
        has_barcode_rois = len(barcode_results) > 0
        
        # Initialize all device summaries with default barcode values first
        for device_id in device_summaries:
            device_summaries[device_id]['barcode'] = 'N/A'
        
        # Priority 0: Check for barcode ROIs with is_device_barcode=True (HIGHEST PRIORITY)
        for barcode_result in barcode_results:
            device_id = barcode_result.get('device_id', 1)
            roi_id = barcode_result.get('roi_id')
            if device_id in device_summaries and roi_id:
                # Check if this ROI has is_device_barcode=True
                is_device_barcode = False
                try:
                    for roi_data in rois:
                        if roi_data is not None and len(roi_data) >= 11 and roi_data[0] == roi_id:
                            is_device_barcode = roi_data[10] if roi_data[10] is not None else False
                            break
                except Exception as e:
                    logger.warning(f"Failed to check is_device_barcode for ROI {roi_id}: {e}")
                
                if is_device_barcode:
                    barcode_values = barcode_result.get('barcode_values', [])
                    if barcode_values and isinstance(barcode_values, list) and len(barcode_values) > 0:
                        first_barcode = str(barcode_values[0]).strip()
                        if first_barcode and first_barcode != 'N/A':
                            # Call barcode linking API to get linked data
                            try:
                                from src.barcode_linking import get_linked_barcode_with_fallback
                                linked_barcode, is_linked = get_linked_barcode_with_fallback(first_barcode)
                                device_summaries[device_id]['barcode'] = linked_barcode
                                if is_linked:
                                    logger.info(f"[Priority 0] Using linked barcode for device {device_id}: {first_barcode} -> {linked_barcode}")
                                else:
                                    logger.info(f"[Priority 0] Using device main barcode ROI for device {device_id}: {first_barcode} (linking failed)")
                            except Exception as e:
                                logger.warning(f"Barcode linking failed for device {device_id}: {e}")
                                device_summaries[device_id]['barcode'] = first_barcode
                                logger.info(f"[Priority 0] Using device main barcode ROI for device {device_id}: {first_barcode}")
        
        # Priority 1: Use any barcode ROI results if device barcode not yet set
        for barcode_result in barcode_results:
            device_id = barcode_result.get('device_id', 1)
            if device_id in device_summaries and device_summaries[device_id]['barcode'] == 'N/A':
                barcode_values = barcode_result.get('barcode_values', [])
                # Only use ROI barcode if it's valid and not empty
                if barcode_values and isinstance(barcode_values, list) and len(barcode_values) > 0:
                    first_barcode = str(barcode_values[0]).strip()
                    if first_barcode and first_barcode != 'N/A':
                        # Call barcode linking API to get linked data
                        try:
                            from src.barcode_linking import get_linked_barcode_with_fallback
                            linked_barcode, is_linked = get_linked_barcode_with_fallback(first_barcode)
                            device_summaries[device_id]['barcode'] = linked_barcode
                            if is_linked:
                                logger.info(f"[Priority 1] Using linked barcode for device {device_id}: {first_barcode} -> {linked_barcode}")
                            else:
                                logger.info(f"[Priority 1] Using ROI barcode for device {device_id}: {first_barcode} (linking failed)")
                        except Exception as e:
                            logger.warning(f"Barcode linking failed for device {device_id}: {e}")
                            device_summaries[device_id]['barcode'] = first_barcode
                            logger.info(f"[Priority 1] Using ROI barcode for device {device_id}: {first_barcode}")
        
        # Priority 2: Then, use manual device barcodes as fallback for devices
        # that don't have valid ROI barcodes
        if device_barcodes:
            logger.info(f"Checking manual device barcodes: {device_barcodes}")
            # Normalize device_barcodes format
            normalized_barcodes = normalize_device_barcodes(device_barcodes)
            for device_id_str, manual_barcode in normalized_barcodes.items():
                device_id = int(device_id_str)  # Convert string key to int
                if device_id in device_summaries:
                    current_barcode = device_summaries[device_id]['barcode']
                    # Use manual barcode if no valid ROI barcode was found
                    if (current_barcode == 'N/A' and manual_barcode and
                            str(manual_barcode).strip()):
                        original_manual = str(manual_barcode).strip()
                        # Apply barcode linking to manual input
                        try:
                            from src.barcode_linking import get_linked_barcode_with_fallback
                            linked_barcode, is_linked = (
                                get_linked_barcode_with_fallback(original_manual)
                            )
                            device_summaries[device_id]['barcode'] = linked_barcode
                            if is_linked:
                                logger.info(
                                    f"[Priority 2] Using linked manual barcode "
                                    f"for device {device_id}: "
                                    f"{original_manual} -> {linked_barcode}"
                                )
                            else:
                                logger.info(
                                    f"[Priority 2] Using manual barcode for "
                                    f"device {device_id}: {linked_barcode} "
                                    f"(linking not applied)"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Barcode linking failed for device "
                                f"{device_id}: {e}"
                            )
                            device_summaries[device_id]['barcode'] = original_manual
                            logger.info(
                                f"[Priority 2] Using manual barcode for "
                                f"device {device_id}: {original_manual}"
                            )

        # Priority 3: Legacy single barcode support as final fallback
        elif device_barcode:
            logger.info(
                f"Using legacy single barcode for devices without "
                f"barcodes: {device_barcode}"
            )
            for device_id in device_summaries:
                if device_summaries[device_id]['barcode'] == 'N/A':
                    # Apply barcode linking to legacy input
                    try:
                        from src.barcode_linking import (
                            get_linked_barcode_with_fallback
                        )
                        linked_barcode, is_linked = (
                            get_linked_barcode_with_fallback(device_barcode)
                        )
                        device_summaries[device_id]['barcode'] = linked_barcode
                        if is_linked:
                            logger.info(
                                f"[Priority 3] Using linked legacy barcode "
                                f"for device {device_id}: "
                                f"{device_barcode} -> {linked_barcode}"
                            )
                        else:
                            logger.info(
                                f"[Priority 3] Using legacy barcode for "
                                f"device {device_id}: {linked_barcode} "
                                f"(linking not applied)"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Barcode linking failed for device "
                            f"{device_id}: {e}"
                        )
                        device_summaries[device_id]['barcode'] = device_barcode
                        logger.info(
                            f"[Priority 3] Using legacy barcode for device "
                            f"{device_id}: {device_barcode}"
                        )
        
        # Build result before cleanup
        result = {
            'roi_results': roi_results,
            'device_summaries': device_summaries,
            'overall_result': {
                'passed': total_passed == len(roi_results),
                'total_rois': len(roi_results),
                'passed_rois': total_passed,
                'failed_rois': len(roi_results) - total_passed
            }
        }
        
        # CRITICAL: Clear barcode variables after building result
        logger.info("[CLEANUP] Clearing barcode variables in run_real_inspection")
        try:
            # Clear input barcode parameters
            device_barcode = None
            device_barcodes = None
            
            # Clear barcode_results list
            if 'barcode_results' in locals():
                barcode_results = None
            
            logger.info("[CLEANUP] Barcode variables cleared in run_real_inspection")
        except Exception as cleanup_error:
            logger.warning(f"[CLEANUP] Error during cleanup: {cleanup_error}")
        
        return result
        
    except ImportError as e:
        logger.error(f"Could not import inspection modules: {e}")
        logger.info("Falling back to simulation mode")
        return simulate_inspection(image, device_barcode, device_barcodes)
        
    except Exception as e:
        logger.error(f"Real inspection failed: {e}")
        logger.info("Falling back to simulation mode")
        return simulate_inspection(image, device_barcode, device_barcodes)

@app.route('/', methods=['GET'])
@app.route('/api', methods=['GET'])
def api_home():
    """Serve API documentation home page.
    ---
    tags:
      - Documentation
    summary: API documentation home page
    description: Interactive landing page with links to all documentation
    produces:
      - text/html
    responses:
      200:
        description: HTML documentation page
    """
    try:
        template_path = os.path.join(
            os.path.dirname(__file__),
            'templates',
            'api_home.html'
        )
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            return jsonify({
                'message': 'Visual AOI Server API',
                'documentation': '/apidocs/',
                'api_docs': '/api/docs',
                'guide': '/api/docs/guide',
                'health': '/api/health'
            })
    except Exception as e:
        logger.error(f"Error serving API home: {e}")
        return jsonify({
            'error': 'Template not found',
            'documentation': '/apidocs/'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint.
    ---
    tags:
      - Health
    summary: Check server health status
    description: Returns the current health status of the Visual AOI server
    responses:
      200:
        description: Server health information
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
            timestamp:
              type: string
              format: date-time
            modules_available:
              type: boolean
            initialized:
              type: boolean
            active_sessions:
              type: integer
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'modules_available': MODULES_AVAILABLE,
        'initialized': server_state['initialized'],
        'active_sessions': len(server_state['sessions'])
    })


@app.route('/api/docs', methods=['GET'])
def api_documentation():
    """Get comprehensive API documentation for client integration.
    ---
    tags:
      - Documentation
    summary: Get API documentation
    description: Returns comprehensive list of all available API endpoints
    responses:
      200:
        description: API documentation
        schema:
          type: object
    """
    docs = {
        "api_version": "1.0.0",
        "server_name": "Visual AOI Server",
        "description": "RESTful API for Visual AOI inspection processing",
        "swagger_ui": "/apidocs/",
        "openapi_spec": "/apispec_1.json",
        "endpoints": {
            "system": {
                "health_check": {
                    "method": "GET",
                    "path": "/api/health",
                    "description": "Check server health status"
                },
                "initialize": {
                    "method": "POST",
                    "path": "/api/initialize",
                    "description": "Initialize AI models and system"
                }
            },
            "session": {
                "create": {
                    "method": "POST",
                    "path": "/api/session/create",
                    "description": "Create new inspection session",
                    "body": {
                        "product_name": "string (required)",
                        "client_info": "object (optional)"
                    }
                },
                "get": {
                    "method": "GET",
                    "path": "/api/session/{session_id}",
                    "description": "Get session information"
                },
                "list": {
                    "method": "GET",
                    "path": "/api/session/list",
                    "description": "List all active sessions"
                },
                "delete": {
                    "method": "DELETE",
                    "path": "/api/session/{session_id}",
                    "description": "Delete inspection session"
                },
                "inspect": {
                    "method": "POST",
                    "path": "/api/session/{session_id}/inspect",
                    "description": "Process image inspection (LEGACY)",
                    "body": {
                        "image": "base64 string (legacy) OR",
                        "image_path": "string (preferred)",
                        "image_filename": "string (relative path)"
                    }
                },
                "grouped_inspect": {
                    "method": "POST",
                    "path": "/api/session/{session_id}/grouped_inspect",
                    "description": "Process inspection with device grouping",
                    "note": "Returns results grouped by device_location"
                }
            },
            "products": {
                "list": {
                    "method": "GET",
                    "path": "/api/products",
                    "description": "List all available products"
                },
                "get_rois": {
                    "method": "GET",
                    "path": "/api/products/{product_name}/rois",
                    "description": "Get ROI configuration for product"
                },
                "save_rois": {
                    "method": "POST",
                    "path": "/api/products/{product_name}/rois",
                    "description": "Save ROI configuration",
                    "body": {"rois": "array of ROI objects"}
                },
                "get_colors": {
                    "method": "GET",
                    "path": "/api/products/{product_name}/colors",
                    "description": "Get color checking configuration (NEW)",
                    "note": "Returns color ranges for color ROI validation"
                },
                "save_colors": {
                    "method": "POST",
                    "path": "/api/products/{product_name}/colors",
                    "description": "Save color checking configuration (NEW)",
                    "body": {
                        "color_ranges": [
                            {
                                "name": "red",
                                "lower": "[r,g,b]",
                                "upper": "[r,g,b]",
                                "color_space": "RGB or HSV",
                                "threshold": 50.0
                            }
                        ]
                    }
                }
            },
            "golden_samples": {
                "list_products": {
                    "method": "GET",
                    "path": "/api/golden-sample/products",
                    "description": "List products with golden samples"
                },
                "get_samples": {
                    "method": "GET",
                    "path": "/api/golden-sample/{product}/{roi_id}",
                    "description": "Get golden samples (returns file paths)",
                    "query_params": {
                        "include_images": "true for base64 (backward compat)"
                    }
                },
                "get_metadata": {
                    "method": "GET",
                    "path": "/api/golden-sample/{product}/{roi_id}/metadata",
                    "description": "Get metadata without images (lightweight)"
                },
                "download": {
                    "method": "GET",
                    "path": "/api/golden-sample/{product}/{roi_id}/download/{filename}",
                    "description": "Download golden sample image"
                },
                "save": {
                    "method": "POST",
                    "path": "/api/golden-sample/save",
                    "content_type": "multipart/form-data",
                    "description": "Upload golden sample image"
                },
                "promote": {
                    "method": "POST",
                    "path": "/api/golden-sample/promote",
                    "description": "Promote alternative to best golden"
                },
                "restore": {
                    "method": "POST",
                    "path": "/api/golden-sample/restore",
                    "description": "Restore from backup"
                },
                "delete": {
                    "method": "DELETE",
                    "path": "/api/golden-sample/delete",
                    "description": "Delete golden sample"
                }
            }
        },
        "roi_types": {
            "1": {
                "name": "Barcode",
                "description": "Barcode detection using Dynamsoft SDK"
            },
            "2": {
                "name": "Compare",
                "description": "Image comparison with golden sample"
            },
            "3": {
                "name": "OCR",
                "description": "Text recognition using EasyOCR"
            },
            "4": {
                "name": "Color Check",
                "description": "Color validation (NEW FEATURE)",
                "note": "Validates ROI color against defined ranges"
            }
        },
        "image_transmission": {
            "input_methods": [
                {
                    "method": "image_path",
                    "priority": 1,
                    "description": "Absolute file path (PREFERRED)",
                    "example": "/path/to/image.jpg",
                    "benefits": "99% smaller payload, 195x faster"
                },
                {
                    "method": "image_filename",
                    "priority": 2,
                    "description": "Relative to shared/sessions/{uuid}/input/",
                    "example": "capture_001.jpg"
                },
                {
                    "method": "image",
                    "priority": 3,
                    "description": "Base64 encoded (LEGACY)",
                    "note": "Supported for backward compatibility only"
                }
            ],
            "output_format": {
                "roi_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_X.jpg",
                "golden_image_path": "/mnt/visual-aoi-shared/sessions/{uuid}/output/golden_X.jpg",
                "note": "Returns file paths, NOT base64 (99% smaller response)"
            }
        },
        "shared_folder": {
            "server_path": f"{SHARED_FOLDER_PATH}/",
            "client_mount": "/mnt/visual-aoi-shared/",
            "note": "Client accesses via CIFS mount or symlink (localhost)"
        },
        "links": {
            "swagger_ui": "http://{server_ip}:5000/apidocs/",
            "openapi_json": "http://{server_ip}:5000/apispec_1.json",
            "api_docs": "http://{server_ip}:5000/api/docs",
            "health": "http://{server_ip}:5000/api/health"
        }
    }
    return jsonify(docs)


@app.route('/api/docs/guide', methods=['GET'])
def api_guide():
    """Get client integration guide (markdown format).
    ---
    tags:
      - Documentation
    summary: Get client integration guide
    description: Returns comprehensive markdown guide for client developers
    produces:
      - text/markdown
      - text/plain
    responses:
      200:
        description: Client integration guide in markdown format
      404:
        description: Guide file not found
    """
    try:
        guide_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'docs', 
            'API_CLIENT_GUIDE.md'
        )
        
        if os.path.exists(guide_path):
            with open(guide_path, 'r') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/markdown; charset=utf-8'}
        else:
            return jsonify({
                'error': 'Guide not found',
                'tip': 'Use /api/docs for JSON format documentation'
            }), 404
    except Exception as e:
        logger.error(f"Error serving API guide: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/initialize', methods=['POST'])
def initialize_server():
    """Initialize the inspection system (AI models only, no camera).
    ---
    tags:
      - System
    summary: Initialize the inspection system
    description: Initialize AI models and system components (no camera initialization)
    responses:
      200:
        description: Initialization successful
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            modules_available:
              type: boolean
      500:
        description: Initialization failed
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    try:
        if MODULES_AVAILABLE:
            # Initialize only AI components, skip camera to avoid conflicts with client
            try:
                from src.ai import initialize_mobilenet_model
                from src.ocr import initialize_easyocr_reader
                from src.barcode import init_dynamsoft_router
                
                print("Starting system initialization...")
                print("Initializing AI models...")
                
                # Initialize PyTorch model
                print("Loading PyTorch MobileNetV2 model...")
                ai_model = initialize_mobilenet_model()
                print("✓ PyTorch MobileNetV2 model loaded successfully")
                
                # Initialize barcode reader
                print("Initializing barcode reader...")
                init_dynamsoft_router()
                
                # Initialize OCR reader  
                print("Initializing OCR reader...")
                ocr_success = initialize_easyocr_reader()
                if ocr_success:
                    print("✓ EasyOCR initialized successfully")
                else:
                    print("⚠ EasyOCR initialization had issues")
                
                print("System initialization complete.")
                server_state['initialized'] = True
                message = "System initialized successfully (AI models only)"
            except Exception as e:
                print(f"AI initialization failed: {e}")
                server_state['initialized'] = False
                message = f"System initialization failed: {e}"
        else:
            # Simulate initialization
            server_state['initialized'] = True
            message = "System initialized (simulation mode)"
        
        return jsonify({
            'success': server_state['initialized'],
            'message': message,
            'modules_available': MODULES_AVAILABLE
        })
        
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        return jsonify({
            'success': False,
            'message': f"Initialization failed: {e}"
        }), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get available products.
    ---
    tags:
      - Products
    summary: Get list of available products
    description: Retrieve all available product configurations
    responses:
      200:
        description: List of products
        schema:
          type: object
          properties:
            products:
              type: array
              items:
                type: object
                properties:
                  product_name:
                    type: string
                  config_file:
                    type: string
                  description:
                    type: string
            count:
              type: integer
      500:
        description: Error retrieving products
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        products = get_available_products()
        return jsonify({
            'products': products,
            'count': len(products)
        })
        
    except Exception as e:
        logger.error(f"Get products error: {e}")
        return jsonify({
            'error': f"Failed to get products: {e}"
        }), 500

@app.route('/api/products/create', methods=['POST'])
def create_product():
    """Create a new product configuration.
    ---
    tags:
      - Products
    summary: Create a new product
    description: Create a new product configuration with default ROIs
    parameters:
      - in: body
        name: product
        description: Product configuration data
        required: true
        schema:
          type: object
          required:
            - product_name
          properties:
            product_name:
              type: string
              description: Name of the product
            description:
              type: string
              description: Product description
    responses:
      200:
        description: Product created successfully
        schema:
          type: object
          properties:
            message:
              type: string
            product_name:
              type: string
            config_file:
              type: string
            success:
              type: boolean
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Creation failed
        schema:
          type: object
          properties:
            error:
              type: string
            success:
              type: boolean
    """
    try:
        data = request.get_json()
        product_name = data.get('product_name', '').strip()
        num_devices = data.get('num_devices', 1)  # Number of devices for multi-device support
        
        if not product_name:
            return jsonify({'error': 'Product name is required'}), 400
        
        # Sanitize product name
        import re
        product_name = re.sub(r'[^\w\-_]', '', product_name)
        
        if not product_name:
            return jsonify({'error': 'Invalid product name'}), 400
        
        # Check if product already exists (use new directory structure)
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config', 'products', product_name)
        product_file = os.path.join(config_dir, f"rois_config_{product_name}.json")
        
        if os.path.exists(product_file):
            return jsonify({'error': 'Product already exists'}), 400
        
        # Create default ROI configuration for multi-device support
        default_rois = []
        
        # Create default ROIs for each device
        for device_num in range(1, num_devices + 1):
            # Barcode ROI for this device
            default_rois.append({
                "idx": len(default_rois) + 1,
                "type": 1,  # barcode
                "coords": [100 * device_num, 50, 100 * device_num + 100, 100],
                "focus": 305,
                "exposure": 1200,
                "ai_threshold": 0.8,
                "feature_method": "opencv",
                "rotation": 0,
                "device_location": device_num,
                "expected_text": None,
                "is_device_barcode": True
            })
            
            # Compare ROI for this device
            default_rois.append({
                "idx": len(default_rois) + 1,
                "type": 2,  # compare
                "coords": [100 * device_num, 150, 100 * device_num + 100, 250],
                "focus": 305,
                "exposure": 1200,
                "ai_threshold": 0.93,
                "feature_method": "mobilenet",
                "rotation": 0,
                "device_location": device_num,
                "expected_text": None,
                "is_device_barcode": False
            })
            
            # OCR ROI for this device
            default_rois.append({
                "idx": len(default_rois) + 1,
                "type": 3,  # ocr
                "coords": [100 * device_num, 300, 100 * device_num + 100, 350],
                "focus": 305,
                "exposure": 1200,
                "ai_threshold": 0.8,
                "feature_method": "ocr",
                "rotation": 0,
                "device_location": device_num,
                "expected_text": "SAMPLE",
                "is_device_barcode": False
            })
        
        # Ensure product directory and golden_rois subdirectory exist
        os.makedirs(config_dir, exist_ok=True)
        golden_rois_dir = os.path.join(config_dir, 'golden_rois')
        os.makedirs(golden_rois_dir, exist_ok=True)
        
        # Save configuration using new format
        with open(product_file, 'w') as f:
            json.dump(default_rois, f, indent=2)
        
        logger.info(f"Created new product configuration: {product_name} with {num_devices} device(s)")
        
        return jsonify({
            'message': f'Product {product_name} created successfully with {num_devices} device(s)',
            'product_name': product_name,
            'config_file': product_file,
            'num_devices': num_devices,
            'total_rois': len(default_rois),
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Create product error: {e}")
        return jsonify({
            'error': f"Failed to create product: {e}",
            'success': False
        }), 500

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new inspection session.
    ---
    tags:
      - Sessions
    summary: Create a new inspection session
    description: Create a new inspection session for a specific product
    parameters:
      - in: body
        name: session
        description: Session configuration
        required: true
        schema:
          type: object
          required:
            - product_name
          properties:
            product_name:
              type: string
              description: Name of the product for this session
            client_info:
              type: object
              description: Optional client information
    responses:
      200:
        description: Session created successfully
        schema:
          type: object
          properties:
            session_id:
              type: string
            product_name:
              type: string
            created_at:
              type: string
              format: date-time
            message:
              type: string
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Session creation failed
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        data = request.get_json()
        
        if not data or 'product_name' not in data:
            return jsonify({'error': 'Product name is required'}), 400
        
        product_name = data['product_name']
        client_info = data.get('client_info', {})
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Clean up old session directories if they exist
        session_dir = os.path.join(SHARED_FOLDER_PATH, "sessions", session_id)
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                logger.info(f"Cleaned up existing session directory: {session_id}")
            except Exception as e:
                logger.warning(f"Failed to clean up existing session directory {session_id}: {e}")
        
        # Create fresh session directories
        input_dir = os.path.join(session_dir, "input")
        output_dir = os.path.join(session_dir, "output")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created fresh session directories for {session_id}")
        
        # Create session
        session = InspectionSession(session_id, product_name, client_info)
        server_state['sessions'][session_id] = session
        
        # Set current product
        server_state['current_product'] = product_name
        if MODULES_AVAILABLE:
            try:
                from src.config import set_product_name
                set_product_name(product_name)
            except Exception as e:
                logger.warning(f"Failed to set product name in real system: {e}")
        
        logger.info(f"Created session {session_id} for product {product_name}")
        
        return jsonify({
            'session_id': session_id,
            'product_name': product_name,
            'created_at': session.created_at.isoformat(),
            'message': f'Session created for product: {product_name}'
        })
        
    except Exception as e:
        logger.error(f"Create session error: {e}")
        return jsonify({
            'error': f"Failed to create session: {e}"
        }), 500

@app.route('/api/session/<session_id>/inspect', methods=['POST'])
def run_inspection(session_id):
    """Run inspection on uploaded image.
    ---
    tags:
      - Inspection
    summary: Run AOI inspection
    description: Process an uploaded image through the Visual AOI inspection pipeline
    parameters:
      - in: path
        name: session_id
        type: string
        required: true
        description: UUID of the inspection session
      - in: body
        name: inspection_data
        description: Image and barcode data for inspection
        required: true
        schema:
          type: object
          properties:
            image_filename:
              type: string
              description: |
                (PREFERRED) Filename of image in shared/sessions/{session_id}/input/ directory.
                Performance: 99% smaller payload, no encoding overhead.
                Example: "captured_305_1200.jpg"
            image:
              type: string
              description: |
                (LEGACY) Base64 encoded image data. Supported for backward compatibility.
                Use image_filename instead for better performance.
                Example: "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
            device_barcode:
              type: string
              description: |
                (LEGACY) Single barcode applied to all devices.
                Priority 3: Used only if no ROI barcode detected.
                NOTE: Barcode will be validated/transformed via external API.
                Example: "1897848 S/N: 65514 3969 1006 V" → "1897848-0001555-118714"
            device_barcodes:
              type: object
              description: |
                (RECOMMENDED) Dictionary mapping device IDs to barcodes.
                Priority 2: Used only if no ROI barcode detected for that device.
                NOTE: All barcodes will be validated/transformed via external API.
                Supports both dict format {"1": "barcode"} and list format
                [{"device_id": 1, "barcode": "..."}].
                Example: {"1": "1897848 S/N: 65514 3969 1006 V"} 
                Returns: {"1": {"barcode": "1897848-0001555-118714"}}
              additionalProperties:
                type: string
          note: |
            Either image_filename (preferred) or image (legacy) must be provided.
            
            BARCODE PROCESSING (Priority Order):
            - Priority 0: ROI with is_device_barcode=true (scanned from image) → Linked
            - Priority 1: Any barcode ROI (fallback) → Linked
            - Priority 2: device_barcodes parameter (manual input) → Linked
            - Priority 3: device_barcode parameter (legacy) → Linked
            
            All barcodes are validated/transformed via external linking API:
            POST http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData
            
            The linked barcode is returned in device_summaries[device_id]["barcode"].
            Original scanned barcode (if any) is preserved in roi_results[]["barcode_values"].
    responses:
      200:
        description: Inspection completed successfully
        schema:
          type: object
          properties:
            roi_results:
              type: array
              description: |
                Individual ROI inspection results.
                For barcode ROIs, barcode_values contains original scanned data.
              items:
                type: object
                properties:
                  roi_id:
                    type: integer
                  roi_type_name:
                    type: string
                  passed:
                    type: boolean
                  barcode_values:
                    type: array
                    description: |
                      Original barcode values scanned from ROI (if barcode ROI).
                      Note: This is the raw scanned value, NOT the linked barcode.
                      Use device_summaries[device_id]["barcode"] for linked value.
                    items:
                      type: string
            device_summaries:
              type: object
              description: |
                Summary per device with linked barcodes.
                Key is device ID (e.g., "1", "2"), value is device summary object.
              additionalProperties:
                type: object
                properties:
                  device_id:
                    type: integer
                  barcode:
                    type: string
                    description: |
                      LINKED/VALIDATED barcode for this device.
                      This is the transformed barcode from external API.
                      Example: "1897848-0001555-118714"
                      Use this field for device identification/tracking.
                  device_passed:
                    type: boolean
                  passed_rois:
                    type: integer
                  total_rois:
                    type: integer
            overall_result:
              type: object
              properties:
                passed:
                  type: boolean
                total_rois:
                  type: integer
                passed_rois:
                  type: integer
                failed_rois:
                  type: integer
            processing_time:
              type: number
      400:
        description: Invalid input data
        schema:
          type: object
          properties:
            error:
              type: string
      404:
        description: Session not found
        schema:
          type: object
          properties:
            error:
              type: string
      409:
        description: Another inspection is in progress
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Inspection failed
        schema:
          type: object
          properties:
            error:
              type: string
    example:
      request:
        image_filename: "device_image.jpg"
        device_barcodes:
          "1": "1897848 S/N: 65514 3969 1006 V"
      response:
        roi_results:
          - roi_id: 3
            roi_type_name: "barcode"
            passed: true
            barcode_values:
              - "1897848 S/N: 65514 3969 1006 V"
        device_summaries:
          "1":
            device_id: 1
            barcode: "1897848-0001555-118714"
            device_passed: true
            passed_rois: 17
            total_rois: 17
        overall_result:
          passed: true
          total_rois: 17
          passed_rois: 17
          failed_rois: 0
        processing_time: 2.45
      note: |
        Notice how the client sent "1897848 S/N: 65514 3969 1006 V" but received
        "1897848-0001555-118714" in device_summaries. This is the linked barcode
        from the external API. Always use device_summaries[device_id]["barcode"]
        for device tracking/identification.
    """
    try:
        # Check if session exists
        if session_id not in server_state['sessions']:
            return jsonify({'error': 'Session not found'}), 404
        
        session = server_state['sessions'][session_id]
        session.update_activity()
        
        # Check if inspection is in progress
        if server_state['inspection_in_progress']:
            return jsonify({'error': 'Another inspection is in progress'}), 409
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Check that at least one image input method is provided
        if 'image' not in data and 'image_filename' not in data:
            return jsonify({'error': 'Image data is required (either image_filename or image)'}), 400
        
        # Mark inspection as in progress
        server_state['inspection_in_progress'] = True
        
        try:
            # Load image using new helper (supports both file paths and Base64)
            cv_image, source_method = load_image_from_request(data, session_id)
            logger.info(f"Image loaded via {source_method} method for session {session_id}")
            
            # Get device barcodes if provided (can be single barcode or dictionary of barcodes)
            device_barcode = data.get('device_barcode', None)  # Legacy single barcode
            device_barcodes = data.get('device_barcodes', {})   # New multi-device barcodes
            
            start_time = time.time()
            
            # Get product name from session if available
            product_name = session.product_name if hasattr(session, 'product_name') else None
            
            if MODULES_AVAILABLE:
                # Use real inspection
                try:
                    inspection_results = run_real_inspection(cv_image, product_name, device_barcode, device_barcodes, session_id)
                except Exception as real_error:
                    logger.error(f"Real inspection failed: {real_error}")
                    logger.info("Falling back to simulation")
                    inspection_results = simulate_inspection(cv_image, device_barcode, device_barcodes)
            else:
                # Use simulation
                inspection_results = simulate_inspection(cv_image, device_barcode, device_barcodes)
            
            processing_time = time.time() - start_time
            inspection_results['processing_time'] = processing_time
            
            # Update session
            session.inspection_count += 1
            session.last_results = inspection_results
            
            logger.info(f"Inspection completed for session {session_id} in {processing_time:.2f}s")
            
            return jsonify(inspection_results)
            
        finally:
            server_state['inspection_in_progress'] = False
            
    except Exception as e:
        server_state['inspection_in_progress'] = False
        logger.error(f"Inspection error: {e}")
        return jsonify({
            'error': f"Inspection failed: {e}"
        }), 500

@app.route('/api/session/<session_id>/close', methods=['POST'])
def close_session(session_id):
    """Close an inspection session."""
    try:
        if session_id not in server_state['sessions']:
            return jsonify({'error': 'Session not found'}), 404
        
        session = server_state['sessions'][session_id]
        duration = (datetime.now() - session.created_at).total_seconds()
        
        # Remove session from memory
        del server_state['sessions'][session_id]
        
        # Clean up session directory
        session_dir = os.path.join(SHARED_FOLDER_PATH, "sessions", session_id)
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                logger.info(f"Closed session {session_id} and removed its directory after {duration:.1f} seconds")
            except Exception as e:
                logger.warning(f"Failed to remove directory for session {session_id}: {e}")
                logger.info(f"Closed session {session_id} after {duration:.1f} seconds")
        else:
            logger.info(f"Closed session {session_id} after {duration:.1f} seconds")
        
        return jsonify({
            'message': f'Session {session_id} closed',
            'duration_seconds': duration,
            'inspection_count': session.inspection_count,
            'directory_cleaned': os.path.exists(session_dir) == False
        })
        
    except Exception as e:
        logger.error(f"Close session error: {e}")
        return jsonify({
            'error': f"Failed to close session: {e}"
        }), 500

@app.route('/api/session/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """Get session status.
    ---
    tags:
      - Sessions
    summary: Get inspection session status
    description: Retrieve the current status and details of an inspection session
    parameters:
      - in: path
        name: session_id
        type: string
        required: true
        description: UUID of the inspection session
    responses:
      200:
        description: Session status information
        schema:
          type: object
          properties:
            session_id:
              type: string
            product_name:
              type: string
            client_info:
              type: object
            created_at:
              type: string
              format: date-time
            last_activity:
              type: string
              format: date-time
            inspection_count:
              type: integer
      404:
        description: Session not found
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Error retrieving session status
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        if session_id not in server_state['sessions']:
            return jsonify({'error': 'Session not found'}), 404
        
        session = server_state['sessions'][session_id]
        return jsonify(session.to_dict())
        
    except Exception as e:
        logger.error(f"Get session status error: {e}")
        return jsonify({
            'error': f"Failed to get session status: {e}"
        }), 500

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions.
    ---
    tags:
      - Sessions
    summary: List all active inspection sessions
    description: Retrieve a list of all currently active inspection sessions
    responses:
      200:
        description: List of active sessions
        schema:
          type: object
          properties:
            sessions:
              type: array
              items:
                type: object
                properties:
                  session_id:
                    type: string
                  product_name:
                    type: string
                  created_at:
                    type: string
                    format: date-time
                  last_activity:
                    type: string
                    format: date-time
                  inspection_count:
                    type: integer
            count:
              type: integer
      500:
        description: Error listing sessions
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        sessions = [session.to_dict() for session in server_state['sessions'].values()]
        return jsonify({
            'sessions': sessions,
            'count': len(sessions)
        })
        
    except Exception as e:
        logger.error(f"List sessions error: {e}")
        return jsonify({
            'error': f"Failed to list sessions: {e}"
        }), 500

@app.route('/api/status', methods=['GET'])
def get_server_status():
    """Get server status.
    ---
    tags:
      - System
    summary: Get server status information
    description: Retrieve comprehensive server status including initialization state and session count
    responses:
      200:
        description: Server status information
        schema:
          type: object
          properties:
            initialized:
              type: boolean
              description: Whether the system is initialized
            current_product:
              type: string
              description: Currently selected product
            inspection_in_progress:
              type: boolean
              description: Whether an inspection is currently running
            active_sessions:
              type: integer
              description: Number of active sessions
            modules_available:
              type: boolean
              description: Whether real inspection modules are available
            uptime:
              type: number
              description: Server uptime in seconds
      500:
        description: Error retrieving server status
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        return jsonify({
            'initialized': server_state['initialized'],
            'current_product': server_state['current_product'],
            'inspection_in_progress': server_state['inspection_in_progress'],
            'active_sessions': len(server_state['sessions']),
            'modules_available': MODULES_AVAILABLE,
            'uptime': time.time()  # Simple uptime
        })
        
    except Exception as e:
        logger.error(f"Get status error: {e}")
        return jsonify({
            'error': f"Failed to get status: {e}"
        }), 500

@app.route('/get_roi_groups/<product_name>', methods=['GET'])
def get_roi_groups(product_name):
    """Get ROI groups organized by capture conditions (focus, exposure)."""
    try:
        from src.roi import load_rois_from_config, get_rois
        from collections import defaultdict
        
        # Load ROIs for the specified product
        load_rois_from_config(product_name)
        rois = get_rois()
        
        if not rois:
            return jsonify({
                'error': f"No ROIs found for product: {product_name}"
            }), 404
        
        # Group ROIs by (focus, exposure) pairs
        group_dict = defaultdict(list)
        
        for roi in rois:
            # Skip None ROIs
            if roi is None or not isinstance(roi, (list, tuple)) or len(roi) < 5:
                continue
                
            # Extract focus and exposure from ROI
            idx, typ, coords, focus, exposure = roi[:5]
            group_key = f"{focus},{exposure}"
            
            # Create ROI info for this group
            roi_info = {
                'idx': idx,
                'type': typ,
                'coords': coords,
                'focus': focus,
                'exposure': exposure
            }
            
            # Add additional fields if available
            if len(roi) >= 6:
                roi_info['ai_threshold'] = roi[5]
            if len(roi) >= 7:
                roi_info['feature_method'] = roi[6]
            if len(roi) >= 8:
                roi_info['rotation'] = roi[7]
            if len(roi) >= 9:
                roi_info['device_location'] = roi[8]
                
            group_dict[group_key].append(roi_info)
        
        # Convert to regular dict for JSON serialization
        roi_groups = {}
        for group_key, rois in group_dict.items():
            focus, exposure = group_key.split(',')
            roi_groups[group_key] = {
                'focus': int(focus),
                'exposure': int(exposure),
                'rois': rois,
                'count': len(rois)
            }
        
        logger.info(f"Retrieved {len(roi_groups)} ROI groups for product {product_name}")
        
        return jsonify({
            'product_name': product_name,
            'roi_groups': roi_groups,
            'total_groups': len(roi_groups),
            'total_rois': sum(len(group['rois']) for group in roi_groups.values())
        })
        
    except Exception as e:
        logger.error(f"Get ROI groups error for product {product_name}: {e}")
        return jsonify({
            'error': f"Failed to get ROI groups: {e}"
        }), 500

@app.route('/process_grouped_inspection', methods=['POST'])
def process_grouped_inspection():
    """Process inspection using grouped captured images."""
    try:
        # DEBUG: Log RAW request body BEFORE parsing
        raw_data = request.get_data(as_text=True)
        if 'device_barcode' in raw_data.lower():
            logger.info(f"[RAW BODY] Request contains 'device_barcode' string in body")
            # Show snippet around device_barcode
            idx = raw_data.lower().find('device_barcode')
            snippet_start = max(0, idx - 50)
            snippet_end = min(len(raw_data), idx + 200)
            logger.info(f"[RAW BODY SNIPPET] ...{raw_data[snippet_start:snippet_end]}...")
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # DEBUG: Log RAW request to see exactly what client sent
        logger.info(f"[RAW REQUEST DEBUG] Keys in request: {list(data.keys())}")
        logger.info(f"[RAW REQUEST DEBUG] 'device_barcodes' in request: {'device_barcodes' in data}")
        if 'device_barcodes' in data:
            logger.info(f"[RAW REQUEST DEBUG] Raw value: {repr(data['device_barcodes'])}")
            logger.info(f"[RAW REQUEST DEBUG] Is empty: {not data['device_barcodes']}")
            logger.info(f"[RAW REQUEST DEBUG] Length: {len(data['device_barcodes']) if isinstance(data['device_barcodes'], (list, dict)) else 'N/A'}")
        else:
            logger.info(f"[RAW REQUEST DEBUG] Key 'device_barcodes' NOT in request - will use default empty dict")
        
        session_id = data.get('session_id')
        captured_images = data.get('captured_images', {})
        device_barcodes = data.get('device_barcodes', {})  # Extract device barcodes from payload
        
        # DEBUG: Log exactly what was received from client
        logger.info(f"[REQUEST DEBUG] Raw device_barcodes from client: {device_barcodes}")
        logger.info(f"[REQUEST DEBUG] device_barcodes type: {type(device_barcodes)}")
        logger.info(f"[REQUEST DEBUG] device_barcodes empty check: {bool(device_barcodes)}")
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
            
        if session_id not in server_state['sessions']:
            return jsonify({'error': 'Invalid session ID'}), 404
            
        if not captured_images:
            return jsonify({'error': 'No captured images provided'}), 400
        
        session = server_state['sessions'][session_id]
        product_name = session.product_name  # Use attribute access for InspectionSession object
        
        logger.info(f"Processing grouped inspection for session {session_id}, product {product_name}")
        logger.info(f"Received {len(captured_images)} image groups")
        
        # Log device barcodes if provided
        if device_barcodes:
            logger.info(f"Device barcodes provided: {device_barcodes}")

        # Prepare the inspection results - FRESH for each request
        all_results = []
        group_results = {}
        device_summaries = {}  # CRITICAL: Fresh dictionary for each inspection request
        
        logger.info(f"[INIT] Created fresh device_summaries (id={id(device_summaries)}) for inspection request")

        # Process each group
        for group_key, group_data in captured_images.items():
            logger.info(f"[GROUP DEBUG] Processing group {group_key}")
            logger.info(f"[GROUP DEBUG] device_barcodes at start of loop: {device_barcodes}")
            focus = None
            exposure = None
            try:
                # Validate group_data structure
                if not isinstance(group_data, dict):
                    logger.error(f"Invalid group_data type for group {group_key}: {type(group_data)}")
                    continue
                
                # Check required keys - prioritize file paths over Base64
                has_image_path = 'image_path' in group_data  # Absolute path (PREFERRED)
                has_image_filename = 'image_filename' in group_data  # Relative path to input folder (PREFERRED)
                has_image_base64 = 'image' in group_data  # Base64 data (LEGACY)
                
                if not (has_image_path or has_image_filename or has_image_base64):
                    logger.error(f"Group {group_key} missing image data. Available keys: {list(group_data.keys())}")
                    logger.error(f"Required: 'image_path' (absolute) OR 'image_filename' (relative) OR 'image' (base64)")
                    continue
                
                required_keys = ['focus', 'exposure', 'rois']
                missing_keys = [key for key in required_keys if key not in group_data]
                if missing_keys:
                    logger.error(f"Group {group_key} missing required keys: {missing_keys}. Available keys: {list(group_data.keys())}")
                    continue
                
                focus = group_data['focus']
                exposure = group_data['exposure']
                rois = group_data['rois']

                # Construct paths
                session_dir = os.path.join(SHARED_FOLDER_PATH, "sessions", session_id)
                input_dir = os.path.join(session_dir, "input")
                output_dir = os.path.join(session_dir, "output")
                
                # Ensure output directory exists
                os.makedirs(output_dir, exist_ok=True)
                
                # Handle image loading - prioritize file paths over Base64
                # Method 1: Absolute path (PREFERRED for client control)
                if has_image_path:
                    image_path = group_data['image_path']
                    
                    # Convert client mount path to server path if needed
                    # Client sends: /mnt/visual-aoi-shared/sessions/{uuid}/captures/image.jpg
                    # Server needs: {SHARED_FOLDER_PATH}/sessions/{uuid}/captures/image.jpg
                    if image_path.startswith('/mnt/visual-aoi-shared/'):
                        # Convert client mount path to server path
                        server_path = image_path.replace('/mnt/visual-aoi-shared/', f'{SHARED_FOLDER_PATH}/')
                        logger.debug(f"Converted client path to server path: {image_path} → {server_path}")
                        image_path = server_path
                    
                    if not os.path.exists(image_path):
                        logger.error(f"Input image not found at absolute path: {image_path}")
                        continue
                    
                    image = cv2.imread(image_path)
                    if image is None:
                        logger.error(f"Failed to read image from absolute path: {image_path}")
                        continue
                    
                    image_filename = os.path.basename(image_path)
                    logger.info(f"✓ Processing group {group_key} with {len(rois)} ROIs from absolute path: {image_path}")
                
                # Method 2: Relative filename (PREFERRED for session isolation)
                elif has_image_filename:
                    image_filename = group_data['image_filename']
                    input_image_path = os.path.join(input_dir, image_filename)
                    
                    if not os.path.exists(input_image_path):
                        logger.error(f"Input image not found: {input_image_path}")
                        continue
                        
                    image = cv2.imread(input_image_path)
                    if image is None:
                        logger.error(f"Failed to read image: {input_image_path}")
                        continue
                    
                    logger.info(f"✓ Processing group {group_key} with {len(rois)} ROIs from file: {image_filename}")
                
                # Method 3: Base64 data (LEGACY - backward compatibility)
                else:
                    try:
                        image_data = group_data['image']
                        # Handle data URL format (data:image/jpeg;base64,...)
                        if isinstance(image_data, str) and image_data.startswith('data:'):
                            image_data = image_data.split(',', 1)[1]
                        
                        # Decode base64 to image
                        img_bytes = base64.b64decode(image_data)
                        nparr = np.frombuffer(img_bytes, np.uint8)
                        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if image is None:
                            logger.error(f"Failed to decode base64 image for group {group_key}")
                            continue
                        
                        image_filename = f"group_{group_key.replace(',', '_')}.jpg"
                        logger.info(f"⚠ Processing group {group_key} with {len(rois)} ROIs from Base64 (size: {len(image_data)} bytes)")
                        logger.info(f"⚠ Consider using 'image_path' or 'image_filename' for better performance")
                    except Exception as e:
                        logger.error(f"Error decoding base64 image for group {group_key}: {e}")
                        continue

                # Run inspection on this image with ONLY the ROIs from this group
                # Important: Filter ROIs to only process those matching this group's focus/exposure
                results = run_real_inspection(image, product_name, device_barcodes=device_barcodes, session_id=session_id, 
                                             filter_focus=focus, filter_exposure=exposure)
                
                if results:
                    # Process and save ROI images to output directory
                    roi_results_with_images = []
                    
                    # Group ROI results by device
                    for roi_result in results.get('roi_results', []):
                        device_id = roi_result.get('device_id', 1)  # Default to device 1
                        logger.info(f"DEBUG: ROI {roi_result.get('roi_id')} has device_id: {device_id}")
                        
                        # Create fresh device entry if not exists
                        if device_id not in device_summaries:
                            logger.info(f"[DEVICE INIT] Creating fresh device_summaries entry for device {device_id}")
                            device_summaries[device_id] = {
                                'device_id': device_id,
                                'roi_results': [],  # Fresh list for this inspection
                                'passed_rois': 0,
                                'total_rois': 0,
                                'device_passed': True,
                                'barcode': 'N/A'  # ALWAYS start with N/A - will be set by barcode logic later
                            }
                        
                        # Save ROI and golden images to output directory for client access
                        roi_id = roi_result.get('roi_id', 'unknown')
                        
                        # Images are already saved by run_real_inspection, just update paths
                        # Convert absolute paths to client-accessible paths (relative to mount point)
                        if roi_result.get('roi_image_path'):
                            # Path is already in correct format: sessions/{session_id}/output/roi_X.jpg
                            pass
                        
                        if roi_result.get('golden_image_path'):
                            # Path is already in correct format: sessions/{session_id}/output/golden_X.jpg
                            pass
                        
                        # Remove base64 data if present (shouldn't be anymore)
                        roi_result.pop('roi_image', None)
                        roi_result.pop('golden_image', None)
                        
                        device_summaries[device_id]['roi_results'].append(roi_result)
                        device_summaries[device_id]['total_rois'] += 1
                        
                        if roi_result.get('passed', False):
                            device_summaries[device_id]['passed_rois'] += 1
                        else:
                            device_summaries[device_id]['device_passed'] = False
                    
                    group_results[group_key] = results
                    all_results.extend(results.get('roi_results', []))
                else:
                    logger.error(f"No results returned for group {group_key}")
                    
            except KeyError as e:
                logger.error(f"Error processing group {group_key}: Missing key {e}")
                logger.error(f"Group data structure: {group_data}")
                import traceback
                logger.error(traceback.format_exc())
                group_results[group_key] = {
                    'error': f"Missing required field: {e}",
                    'focus': focus,
                    'exposure': exposure
                }
            except Exception as e:
                logger.error(f"Error processing group {group_key}: {e}")
                logger.error(f"Group data: {group_data}")
                import traceback
                logger.error(traceback.format_exc())
                group_results[group_key] = {
                    'error': f"Processing failed: {e}",
                    'focus': focus,
                    'exposure': exposure
                }
        
        # Deduplicate ROI results within each device (keep only latest result for each ROI)
        for device_id in device_summaries:
            roi_dict = {}  # {roi_id: roi_result}
            for roi_result in device_summaries[device_id]['roi_results']:
                roi_id = roi_result.get('roi_id')
                # Keep the latest result for each ROI (last one wins)
                roi_dict[roi_id] = roi_result
            
            # Replace roi_results with deduplicated list
            device_summaries[device_id]['roi_results'] = list(roi_dict.values())
            
            # Recalculate passed/total counts after deduplication
            device_summaries[device_id]['total_rois'] = len(roi_dict)
            device_summaries[device_id]['passed_rois'] = sum(1 for r in roi_dict.values() if r.get('passed', False))
            device_summaries[device_id]['device_passed'] = (
                device_summaries[device_id]['passed_rois'] == device_summaries[device_id]['total_rois']
                and device_summaries[device_id]['total_rois'] > 0
            )
        
        # Calculate overall results from deduplicated device summaries
        total_rois = sum(dev['total_rois'] for dev in device_summaries.values())
        passed_rois = sum(dev['passed_rois'] for dev in device_summaries.values())
        overall_passed = passed_rois == total_rois and total_rois > 0
        
        # Add barcode info to device summaries - using the same logic as regular inspection
        barcode_results = [r for dev in device_summaries.values() for r in dev['roi_results'] if r.get('roi_type_name') == 'barcode']
        has_barcode_rois = len(barcode_results) > 0
        
        # CRITICAL: Reset ALL device barcodes to 'N/A' before barcode assignment logic
        # This ensures no barcode data carries over from previous groups or requests
        logger.info(f"[Barcode Debug] Resetting barcodes for devices: {list(device_summaries.keys())}")
        for device_id in device_summaries:
            current_barcode = device_summaries[device_id].get('barcode', 'UNSET')
            logger.info(f"[Barcode Debug] Device {device_id} barcode before reset: {current_barcode}")
            device_summaries[device_id]['barcode'] = 'N/A'  # FORCE reset to N/A
            logger.info(f"[Barcode Debug] Device {device_id} barcode after FORCED reset: N/A")
        
        # First, try to use barcode ROI results if available
        logger.info(f"[Barcode Debug] Found {len(barcode_results)} barcode ROI results")
        for barcode_result in barcode_results:
            device_id = barcode_result.get('device_id', 1)
            roi_id = barcode_result.get('roi_id', 'unknown')
            if device_id in device_summaries:
                barcode_values = barcode_result.get('barcode_values', [])
                logger.info(f"[Barcode Debug] ROI {roi_id} for device {device_id}: barcode_values = {barcode_values}")
                # Only use ROI barcode if it's valid and not empty
                if barcode_values and isinstance(barcode_values, list) and len(barcode_values) > 0:
                    first_barcode = str(barcode_values[0]).strip()
                    if first_barcode and first_barcode != 'N/A':
                        # Apply barcode linking for grouped inspection
                        try:
                            from src.barcode_linking import get_linked_barcode_with_fallback
                            linked_barcode, is_linked = get_linked_barcode_with_fallback(first_barcode)
                            device_summaries[device_id]['barcode'] = linked_barcode
                            if is_linked:
                                logger.info(f"[Grouped] Using linked barcode for device {device_id}: {first_barcode} -> {linked_barcode}")
                            else:
                                logger.info(f"[Grouped] Using ROI barcode for device {device_id}: {first_barcode} (linking failed)")
                        except Exception as e:
                            logger.warning(f"Barcode linking failed for grouped device {device_id}: {e}")
                            device_summaries[device_id]['barcode'] = first_barcode
                            logger.info(f"[Grouped] Using ROI barcode for device {device_id}: {first_barcode}")
        
        # Then, use manual device barcodes as fallback for devices that don't have valid ROI barcodes
        logger.info(f"[CRITICAL DEBUG] device_barcodes before if check: {device_barcodes}, type: {type(device_barcodes)}, bool: {bool(device_barcodes)}")
        if device_barcodes:
            logger.info(f"Checking manual device barcodes for grouped inspection: {device_barcodes}")
            # Normalize device_barcodes format
            normalized_barcodes = normalize_device_barcodes(device_barcodes)
            for device_id_str, manual_barcode in normalized_barcodes.items():
                device_id = int(device_id_str)  # Convert string key to int
                if device_id in device_summaries:
                    current_barcode = device_summaries[device_id]['barcode']
                    # Use manual barcode if no valid ROI barcode was found
                    if current_barcode == 'N/A' and manual_barcode and str(manual_barcode).strip():
                        original_manual = str(manual_barcode).strip()
                        # Apply barcode linking to manual input
                        try:
                            from src.barcode_linking import (
                                get_linked_barcode_with_fallback
                            )
                            linked_barcode, is_linked = (
                                get_linked_barcode_with_fallback(
                                    original_manual
                                )
                            )
                            device_summaries[device_id]['barcode'] = (
                                linked_barcode
                            )
                            if is_linked:
                                logger.info(
                                    f"[Grouped Priority 2] Using linked "
                                    f"manual barcode for device {device_id}: "
                                    f"{original_manual} -> {linked_barcode}"
                                )
                            else:
                                logger.info(
                                    f"[Grouped Priority 2] Using manual "
                                    f"barcode for device {device_id}: "
                                    f"{linked_barcode} (linking not applied)"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Barcode linking failed for device "
                                f"{device_id}: {e}"
                            )
                            device_summaries[device_id]['barcode'] = (
                                original_manual
                            )
                            logger.info(
                                f"[Grouped Priority 2] Using manual barcode "
                                f"for device {device_id}: {original_manual}"
                            )
        
        # Build deduplicated all_results from device_summaries
        deduplicated_all_results = []
        for device_id in sorted(device_summaries.keys()):
            deduplicated_all_results.extend(device_summaries[device_id]['roi_results'])
        
        # Log final barcode values before returning
        logger.info("[Barcode Debug] FINAL device barcodes:")
        for device_id in sorted(device_summaries.keys()):
            final_barcode = device_summaries[device_id].get('barcode', 'MISSING')
            logger.info(f"  Device {device_id}: {final_barcode}")
        
        final_result = {
            'session_id': session_id,
            'product_name': product_name,
            'overall_result': {
                'passed': overall_passed,
                'total_rois': total_rois,
                'passed_rois': passed_rois,
                'failed_rois': total_rois - passed_rois
            },
            'group_results': group_results,
            'roi_results': deduplicated_all_results,  # Use deduplicated results
            'device_summaries': device_summaries,  # Add device summaries to response
            'processing_time': time.time() - session.created_at.timestamp(),
            'timestamp': time.time()
        }
        
        # Update session (store a copy of result)
        session.last_results = final_result.copy()  # Store copy to prevent reference issues
        session.inspection_count += 1
        session.update_activity()
        
        logger.info(f"Grouped inspection completed: {passed_rois}/{total_rois} ROIs passed")
        logger.info(f"DEBUG: Built device summaries: {device_summaries}")
        
        # Store response before cleanup
        response = jsonify(final_result)
        
        # CRITICAL: Clear all barcode-related variables after building response
        logger.info("[CLEANUP] Clearing all barcode variables")
        try:
            # Clear device_barcodes
            if device_barcodes:
                device_barcodes.clear()
                device_barcodes = None
            
            # Clear barcode results
            if barcode_results:
                barcode_results.clear()
                barcode_results = None
            
            # Clear barcodes from device_summaries
            for device_id in device_summaries:
                if 'barcode' in device_summaries[device_id]:
                    device_summaries[device_id]['barcode'] = None
            
            # Clear barcode_values from all ROI results
            for device_id in device_summaries:
                for roi_result in device_summaries[device_id].get('roi_results', []):
                    if 'barcode_values' in roi_result:
                        roi_result['barcode_values'] = None
            
            # Clear local variables
            has_barcode_rois = None
            normalized_barcodes = None
            
            logger.info("[CLEANUP] All barcode variables cleared successfully")
        except Exception as cleanup_error:
            logger.warning(f"[CLEANUP] Error: {cleanup_error}")
        
        return response
        
    except Exception as e:
        logger.error(f"Process grouped inspection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f"Inspection processing failed: {e}"
        }), 500

def cleanup_expired_sessions():
    """Clean up expired sessions (older than 1 hour) and their directories."""
    try:
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in server_state['sessions'].items():
            if (current_time - session.last_activity).total_seconds() > 3600:  # 1 hour
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            # Remove session from memory
            del server_state['sessions'][session_id]
            
            # Clean up session directory
            session_dir = os.path.join(SHARED_FOLDER_PATH, "sessions", session_id)
            if os.path.exists(session_dir):
                try:
                    shutil.rmtree(session_dir)
                    logger.info(f"Cleaned up expired session {session_id} and its directory")
                except Exception as e:
                    logger.warning(f"Failed to remove directory for expired session {session_id}: {e}")
            else:
                logger.info(f"Cleaned up expired session: {session_id}")
            
    except Exception as e:
        logger.error(f"Session cleanup error: {e}")

@app.route('/api/products/<product_name>/rois', methods=['GET'])
def get_product_rois(product_name):
    """Get ROIs configuration for a product.
    ---
    tags:
      - Products
    summary: Get ROI configuration for a product
    description: Retrieve the complete ROI configuration for a specific product
    parameters:
      - in: path
        name: product_name
        type: string
        required: true
        description: Name of the product
    responses:
      200:
        description: ROI configuration retrieved successfully
        schema:
          type: object
          properties:
            rois:
              type: array
              description: Array of ROI configurations (v3.2 format with color support)
              items:
                type: object
                properties:
                  idx:
                    type: integer
                  type:
                    type: integer
                    description: "1=Barcode, 2=Compare, 3=OCR, 4=Color"
                  coords:
                    type: array
                    items:
                      type: integer
                  focus:
                    type: integer
                  exposure:
                    type: integer
                  ai_threshold:
                    type: number
                  feature_method:
                    type: string
                  rotation:
                    type: integer
                  device_location:
                    type: integer
                  expected_text:
                    type: string
                  is_device_barcode:
                    type: boolean
                  expected_color:
                    type: array
                    description: "For Color ROIs (type 4): Target RGB color"
                    items:
                      type: integer
                  color_tolerance:
                    type: integer
                    description: "For Color ROIs (type 4): Deviation allowed (default: 10)"
                  min_pixel_percentage:
                    type: number
                    description: "For Color ROIs (type 4): Minimum match percentage (default: 5.0)"
                  color_ranges:
                    type: array
                    description: "For Color ROIs (type 4): Legacy format with manual bounds"
                    items:
                      type: object
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        config_path = os.path.join('config', 'products', product_name, f'rois_config_{product_name}.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                rois = json.load(f)
            return jsonify({'rois': rois})
        else:
            return jsonify({'rois': []})
            
    except Exception as e:
        logger.error(f"Get ROIs error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_name>/rois', methods=['POST'])
def save_product_rois(product_name):
    """Save ROI configuration for a product.
    ---
    tags:
      - Products
    summary: Save ROI configuration for a product
    description: Save or update the complete ROI configuration for a product. Automatically cleans up golden sample folders for deleted ROIs.
    parameters:
      - in: path
        name: product_name
        type: string
        required: true
        description: Name of the product
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - rois
          properties:
            rois:
              type: array
              description: Array of ROI configurations (supports v3.2 format with Color ROIs)
              items:
                type: object
                properties:
                  idx:
                    type: integer
                  type:
                    type: integer
                    description: "1=Barcode, 2=Compare, 3=OCR, 4=Color"
                  coords:
                    type: array
                    items:
                      type: integer
                  focus:
                    type: integer
                  exposure:
                    type: integer
                  ai_threshold:
                    type: number
                  feature_method:
                    type: string
                  rotation:
                    type: integer
                  device_location:
                    type: integer
                  expected_text:
                    type: string
                  is_device_barcode:
                    type: boolean
                  expected_color:
                    type: array
                    description: "For Color ROIs: Target RGB [R,G,B]"
                    items:
                      type: integer
                  color_tolerance:
                    type: integer
                    description: "For Color ROIs: Tolerance (default 10)"
                  min_pixel_percentage:
                    type: number
                    description: "For Color ROIs: Min match % (default 5.0)"
                  color_ranges:
                    type: array
                    description: "For Color ROIs: Legacy format"
    responses:
      200:
        description: ROI configuration saved successfully
        schema:
          type: object
          properties:
            message:
              type: string
            deleted_roi_folders:
              type: array
              items:
                type: string
            deleted_roi_indices:
              type: array
              items:
                type: integer
      400:
        description: Invalid input
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        data = request.get_json()
        new_rois = data.get('rois', [])
        
        # Create product directory if it doesn't exist
        product_dir = os.path.join('config', 'products', product_name)
        os.makedirs(product_dir, exist_ok=True)
        
        # Load existing ROIs to detect deletions
        config_path = os.path.join(product_dir, f'rois_config_{product_name}.json')
        old_roi_indices = set()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    old_rois = json.load(f)
                    # Extract ROI indices from old configuration
                    for roi in old_rois:
                        if isinstance(roi, dict) and 'idx' in roi:
                            old_roi_indices.add(roi['idx'])
                        elif isinstance(roi, (list, tuple)) and len(roi) > 0:
                            old_roi_indices.add(roi[0])  # Legacy format
            except Exception as e:
                logger.warning(f"Could not load old ROI configuration: {e}")
        
        # Extract new ROI indices
        new_roi_indices = set()
        for roi in new_rois:
            if isinstance(roi, dict) and 'idx' in roi:
                new_roi_indices.add(roi['idx'])
            elif isinstance(roi, (list, tuple)) and len(roi) > 0:
                new_roi_indices.add(roi[0])  # Legacy format
        
        # Find deleted ROI indices
        deleted_roi_indices = old_roi_indices - new_roi_indices
        
        # Delete golden ROI folders for deleted ROIs
        deleted_folders = []
        if deleted_roi_indices:
            golden_rois_dir = os.path.join(product_dir, 'golden_rois')
            for roi_idx in deleted_roi_indices:
                roi_folder = os.path.join(golden_rois_dir, f'roi_{roi_idx}')
                if os.path.exists(roi_folder):
                    try:
                        shutil.rmtree(roi_folder)
                        deleted_folders.append(f'roi_{roi_idx}')
                        logger.info(f"Deleted golden ROI folder: {roi_folder}")
                    except Exception as e:
                        logger.error(f"Failed to delete golden ROI folder {roi_folder}: {e}")
        
        # Validate and normalize each ROI before saving
        validated_rois = []
        validation_errors = []
        for i, roi in enumerate(new_rois):
            try:
                validated_roi = validate_and_normalize_roi_for_save(roi)
                validated_rois.append(validated_roi)
            except ValueError as e:
                validation_errors.append(f"ROI {i} (idx={roi.get('idx', 'unknown')}): {str(e)}")
                logger.error(f"ROI validation error for ROI {i}: {e}")
        
        # If any validation errors, return error response
        if validation_errors:
            return jsonify({
                'error': 'ROI validation failed',
                'validation_errors': validation_errors
            }), 400
        
        # Save validated ROIs configuration
        with open(config_path, 'w') as f:
            json.dump(validated_rois, f, indent=2)
        
        response_message = f'Saved {len(validated_rois)} ROIs successfully (all validated)'
        if deleted_folders:
            response_message += f'. Deleted {len(deleted_folders)} golden ROI folder(s): {", ".join(deleted_folders)}'
        
        logger.info(f"Saved {len(new_rois)} ROIs for product {product_name}. Deleted ROIs: {deleted_roi_indices}")
        
        return jsonify({
            'message': response_message,
            'deleted_roi_folders': deleted_folders,
            'deleted_roi_indices': list(deleted_roi_indices)
        })
        
    except Exception as e:
        logger.error(f"Save ROIs error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_name>/colors', methods=['GET'])
def get_color_config(product_name):
    """Get color configuration for a product.
    ---
    tags:
      - Color Configuration
    summary: Get color ranges for a product
    description: Retrieve color range definitions for color checking ROIs
    parameters:
      - in: path
        name: product_name
        type: string
        required: true
        description: Name of the product
    responses:
      200:
        description: Color configuration retrieved successfully
        schema:
          type: object
          properties:
            product_name:
              type: string
            color_ranges:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  lower:
                    type: array
                    items:
                      type: integer
                  upper:
                    type: array
                    items:
                      type: integer
                  color_space:
                    type: string
      404:
        description: Product or color config not found
      500:
        description: Server error
    """
    try:
        # Get color config path
        project_root = os.path.join(os.path.dirname(__file__), '..')
        config_path = os.path.join(
            project_root, 'config', 'products', product_name,
            f'colors_config_{product_name}.json'
        )
        
        # Check if config file exists
        if not os.path.exists(config_path):
            return jsonify({
                'product_name': product_name,
                'color_ranges': [],
                'message': 'No color configuration found for this product'
            }), 200
        
        # Load and return color config
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        logger.info(f"Retrieved color config for product {product_name}")
        return jsonify({
            'product_name': product_name,
            'color_ranges': config_data.get('color_ranges', [])
        })
        
    except Exception as e:
        logger.error(f"Get color config error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_name>/colors', methods=['POST'])
def save_color_config(product_name):
    """Save color configuration for a product.
    ---
    tags:
      - Color Configuration
    summary: Save color ranges for a product
    description: Update color range definitions for color checking ROIs
    parameters:
      - in: path
        name: product_name
        type: string
        required: true
        description: Name of the product
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            color_ranges:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  lower:
                    type: array
                    items:
                      type: integer
                  upper:
                    type: array
                    items:
                      type: integer
                  color_space:
                    type: string
    responses:
      200:
        description: Color configuration saved successfully
        schema:
          type: object
          properties:
            message:
              type: string
            color_ranges_count:
              type: integer
      400:
        description: Invalid input
      500:
        description: Server error
    """
    try:
        data = request.get_json()
        
        if not data or 'color_ranges' not in data:
            return jsonify({'error': 'color_ranges field is required'}), 400
        
        color_ranges = data['color_ranges']
        
        # Validate color ranges format
        for idx, color_range in enumerate(color_ranges):
            if not isinstance(color_range, dict):
                return jsonify({
                    'error': f'Color range {idx} must be an object'
                }), 400
            
            required_fields = ['name', 'lower', 'upper', 'color_space']
            for field in required_fields:
                if field not in color_range:
                    return jsonify({
                        'error': f'Color range {idx} missing field: {field}'
                    }), 400
            
            # Validate color space
            if color_range['color_space'] not in ['RGB', 'HSV']:
                return jsonify({
                    'error': f'Invalid color_space for range {idx}. Must be RGB or HSV'
                }), 400
            
            # Validate color values are arrays of 3 numbers
            if not isinstance(color_range['lower'], list) or len(color_range['lower']) != 3:
                return jsonify({
                    'error': f'Color range {idx} lower must be array of 3 numbers'
                }), 400
            
            if not isinstance(color_range['upper'], list) or len(color_range['upper']) != 3:
                return jsonify({
                    'error': f'Color range {idx} upper must be array of 3 numbers'
                }), 400
        
        # Get color config path
        project_root = os.path.join(os.path.dirname(__file__), '..')
        product_dir = os.path.join(project_root, 'config', 'products', product_name)
        os.makedirs(product_dir, exist_ok=True)
        
        config_path = os.path.join(product_dir, f'colors_config_{product_name}.json')
        
        # Save color config
        config_data = {
            'product_name': product_name,
            'color_ranges': color_ranges,
            'updated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Saved {len(color_ranges)} color ranges for product {product_name}")
        return jsonify({
            'message': f'Saved {len(color_ranges)} color ranges successfully',
            'color_ranges_count': len(color_ranges)
        })
        
    except Exception as e:
        logger.error(f"Save color config error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/golden-sample/save', methods=['POST'])
def save_golden_sample_enhanced():
    """Save a ROI image as golden sample with enhanced golden matching format.
    ---
    tags:
      - Golden Samples
    summary: Save a golden sample image
    description: Upload and save a ROI image as a golden sample for comparison
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: product_name
        type: string
        required: true
        description: Name of the product
      - in: formData
        name: roi_id
        type: string
        required: true
        description: ROI identifier
      - in: formData
        name: golden_image
        type: file
        required: true
        description: Golden sample image file
    responses:
      200:
        description: Golden sample saved successfully
        schema:
          type: object
          properties:
            message:
              type: string
            backup_info:
              type: string
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Save failed
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        # Get form data and file
        product_name = request.form.get('product_name')
        roi_id = request.form.get('roi_id')
        
        if not product_name or not roi_id:
            return jsonify({'error': 'Product name and ROI ID are required'}), 400
        
        # Get uploaded image file
        if 'golden_image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['golden_image']
        if file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # Create golden ROI directory following enhanced golden matching structure (relative to project root)
        project_root = os.path.join(os.path.dirname(__file__), '..')
        golden_roi_dir = os.path.join(project_root, 'config', 'products', product_name, 'golden_rois', f'roi_{roi_id}')
        os.makedirs(golden_roi_dir, exist_ok=True)
        
        # Check if best_golden.jpg already exists
        best_golden_path = os.path.join(golden_roi_dir, 'best_golden.jpg')
        backup_message = ""
        
        if os.path.exists(best_golden_path):
            # Backup existing best golden with timestamp
            timestamp = int(time.time())
            backup_name = f'original_{timestamp}_old_best.jpg'
            backup_path = os.path.join(golden_roi_dir, backup_name)
            os.rename(best_golden_path, backup_path)
            backup_message = f"Old golden sample backed up as '{backup_name}'"
            logger.info(f"Backed up existing best golden for ROI {roi_id} as {backup_name}")
        
        # Save new image as best_golden.jpg
        file.save(best_golden_path)
        
        message = f"Golden sample saved as 'best_golden.jpg' for ROI {roi_id}"
        if backup_message:
            message += f". {backup_message}"
        
        logger.info(f"Saved enhanced golden sample for product {product_name}, ROI {roi_id}")
        return jsonify({'message': message, 'backup_info': backup_message})
        
    except Exception as e:
        logger.error(f"Save enhanced golden sample error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/golden-sample/<product_name>/<int:roi_id>', methods=['GET'])
def get_golden_samples_enhanced(product_name, roi_id):
    """Get all golden samples for a specific ROI with file paths.
    ---
    tags:
      - Golden Samples
    summary: Get golden samples for ROI (returns file paths)
    description: Retrieve all golden sample images for a specific ROI. Returns file paths for client access (99% smaller than Base64).
    parameters:
      - in: path
        name: product_name
        type: string
        required: true
        description: Name of the product
      - in: path
        name: roi_id
        type: integer
        required: true
        description: ROI identifier
      - in: query
        name: include_images
        type: boolean
        required: false
        description: Include Base64 image data (default false, use download endpoint instead)
    responses:
      200:
        description: List of golden samples with file paths
        schema:
          type: object
          properties:
            golden_samples:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  type:
                    type: string
                  is_best:
                    type: boolean
                  created_time:
                    type: string
                  file_size:
                    type: integer
                  file_path:
                    type: string
                    description: Client-accessible file path with /mnt/visual-aoi-shared prefix
                  image_data:
                    type: string
                    description: Base64 image data (only if include_images=true)
      500:
        description: Error retrieving golden samples
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        # Golden ROI directory path (relative to project root)
        project_root = os.path.join(os.path.dirname(__file__), '..')
        golden_roi_dir = os.path.join(project_root, 'config', 'products', product_name, 'golden_rois', f'roi_{roi_id}')
        
        if not os.path.exists(golden_roi_dir):
            return jsonify({'golden_samples': []})
        
        # Check if client wants Base64 data (backward compatibility)
        include_images = request.args.get('include_images', 'false').lower() == 'true'
        
        golden_samples = []
        
        # Find all .jpg files in the ROI directory
        jpg_files = glob.glob(os.path.join(golden_roi_dir, '*.jpg'))
        
        for file_path in jpg_files:
            filename = os.path.basename(file_path)
            
            # Get file stats
            stat = os.stat(file_path)
            created_time = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            file_size = stat.st_size
            
            # Determine type and if it's the best golden
            is_best = filename == 'best_golden.jpg'
            sample_type = 'best_golden' if is_best else 'alternative'
            
            # Construct client-accessible file path
            # Server path: config/products/{product}/golden_rois/roi_{id}/{filename}
            # Client mount: /mnt/visual-aoi-shared/golden/{product}/roi_{id}/{filename}
            client_path = f"/mnt/visual-aoi-shared/golden/{product_name}/roi_{roi_id}/{filename}"
            
            sample_info = {
                'name': filename,
                'type': sample_type,
                'is_best': is_best,
                'created_time': created_time,
                'file_size': file_size,
                'file_path': client_path
            }
            
            # Only include Base64 data if explicitly requested (backward compatibility)
            if include_images:
                try:
                    with open(file_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode()
                        sample_info['image_data'] = f'data:image/jpeg;base64,{image_data}'
                except Exception as e:
                    logger.warning(f"Failed to read golden sample image {filename}: {e}")
                    sample_info['image_data'] = None
            
            golden_samples.append(sample_info)
        
        # Sort so best golden appears first
        golden_samples.sort(key=lambda x: (not x['is_best'], x['name']))
        
        return jsonify({'golden_samples': golden_samples})
        
    except Exception as e:
        logger.error(f"Get enhanced golden samples error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/golden-sample/<product_name>/<int:roi_id>/metadata', methods=['GET'])
def get_golden_samples_metadata(product_name, roi_id):
    """Get metadata for golden samples without image data (lightweight).
    ---
    tags:
      - Golden Samples
    summary: Get golden sample metadata only
    description: Retrieve metadata for golden samples without downloading image data. Much faster and lighter than the full GET endpoint.
    parameters:
      - in: path
        name: product_name
        type: string
        required: true
        description: Name of the product
      - in: path
        name: roi_id
        type: integer
        required: true
        description: ROI identifier
    responses:
      200:
        description: Metadata for all golden samples
        schema:
          type: object
          properties:
            product_name:
              type: string
            roi_id:
              type: integer
            golden_samples:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  type:
                    type: string
                  is_best:
                    type: boolean
                  created_time:
                    type: string
                  file_size:
                    type: integer
            total_samples:
              type: integer
            total_size:
              type: integer
      500:
        description: Error retrieving metadata
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        # Golden ROI directory path (relative to project root)
        project_root = os.path.join(os.path.dirname(__file__), '..')
        golden_roi_dir = os.path.join(project_root, 'config', 'products', product_name, 'golden_rois', f'roi_{roi_id}')
        
        if not os.path.exists(golden_roi_dir):
            return jsonify({
                'product_name': product_name,
                'roi_id': roi_id,
                'golden_samples': [],
                'total_samples': 0,
                'total_size': 0
            })
        
        golden_samples = []
        total_size = 0
        
        # Find all .jpg files in the ROI directory
        jpg_files = glob.glob(os.path.join(golden_roi_dir, '*.jpg'))
        
        for file_path in jpg_files:
            filename = os.path.basename(file_path)
            
            # Get file stats
            stat = os.stat(file_path)
            created_time = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            file_size = stat.st_size
            total_size += file_size
            
            # Determine type and if it's the best golden
            is_best = filename == 'best_golden.jpg'
            sample_type = 'best_golden' if is_best else 'alternative'
            
            golden_samples.append({
                'name': filename,
                'type': sample_type,
                'is_best': is_best,
                'created_time': created_time,
                'file_size': file_size
            })
        
        # Sort so best golden appears first
        golden_samples.sort(key=lambda x: (not x['is_best'], x['name']))
        
        return jsonify({
            'product_name': product_name,
            'roi_id': roi_id,
            'golden_samples': golden_samples,
            'total_samples': len(golden_samples),
            'total_size': total_size
        })
        
    except Exception as e:
        logger.error(f"Get golden samples metadata error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/golden-sample/<product_name>/<int:roi_id>/download/<filename>', methods=['GET'])
def download_golden_sample(product_name, roi_id, filename):
    """Download a specific golden sample image file.
    ---
    tags:
      - Golden Samples
    summary: Download golden sample image
    description: Stream a specific golden sample image file for download.
    parameters:
      - in: path
        name: product_name
        type: string
        required: true
        description: Name of the product
      - in: path
        name: roi_id
        type: integer
        required: true
        description: ROI identifier
      - in: path
        name: filename
        type: string
        required: true
        description: Golden sample filename (e.g., best_golden.jpg)
    responses:
      200:
        description: Image file
        content:
          image/jpeg:
            schema:
              type: string
              format: binary
      404:
        description: File not found
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Download error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        # Golden ROI directory path (relative to project root)
        project_root = os.path.join(os.path.dirname(__file__), '..')
        golden_roi_dir = os.path.join(project_root, 'config', 'products', product_name, 'golden_rois', f'roi_{roi_id}')
        file_path = os.path.join(golden_roi_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Golden sample file not found'}), 404
        
        # Security check: ensure filename doesn't contain path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        # Stream the file
        from flask import send_file
        return send_file(file_path, mimetype='image/jpeg', as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Download golden sample error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/golden-sample/promote', methods=['POST'])
def promote_golden_sample():
    """Promote an alternative golden sample to be the best golden."""
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        roi_id = data.get('roi_id')
        sample_name = data.get('sample_name')
        
        if not all([product_name, roi_id, sample_name]):
            return jsonify({'error': 'Product name, ROI ID, and sample name are required'}), 400
        
        # Golden ROI directory path (relative to project root)
        project_root = os.path.join(os.path.dirname(__file__), '..')
        golden_roi_dir = os.path.join(project_root, 'config', 'products', product_name, 'golden_rois', f'roi_{roi_id}')
        
        if not os.path.exists(golden_roi_dir):
            return jsonify({'error': 'Golden ROI directory not found'}), 404
        
        sample_path = os.path.join(golden_roi_dir, sample_name)
        best_golden_path = os.path.join(golden_roi_dir, 'best_golden.jpg')
        
        if not os.path.exists(sample_path):
            return jsonify({'error': 'Sample file not found'}), 404
        
        # Backup current best golden if it exists
        if os.path.exists(best_golden_path):
            timestamp = int(time.time())
            backup_name = f'original_{timestamp}_old_best.jpg'
            backup_path = os.path.join(golden_roi_dir, backup_name)
            os.rename(best_golden_path, backup_path)
            logger.info(f"Backed up previous best golden as {backup_name}")
        
        # Copy the promoted sample to become best golden
        import shutil
        shutil.copy2(sample_path, best_golden_path)
        
        logger.info(f"Promoted {sample_name} to best golden for product {product_name}, ROI {roi_id}")
        return jsonify({'message': f"'{sample_name}' promoted to best golden sample"})
        
    except Exception as e:
        logger.error(f"Promote golden sample error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/golden-sample/restore', methods=['POST'])
def restore_golden_sample():
    """Restore a backed-up golden sample (original_*_old_best.jpg) to best_golden.jpg.
    ---
    tags:
      - Golden Samples
    summary: Restore backed-up golden sample
    description: Restore a previous best golden sample from backup (original_*_old_best.jpg files).
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - product_name
            - roi_id
            - backup_filename
          properties:
            product_name:
              type: string
              description: Name of the product
            roi_id:
              type: integer
              description: ROI identifier
            backup_filename:
              type: string
              description: Backup filename to restore (e.g., original_1696377600_old_best.jpg)
    responses:
      200:
        description: Golden sample restored successfully
        schema:
          type: object
          properties:
            message:
              type: string
            restored_from:
              type: string
            backed_up_current:
              type: string
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
      404:
        description: Backup file not found
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Restore failed
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        roi_id = data.get('roi_id')
        backup_filename = data.get('backup_filename')
        
        if not all([product_name, roi_id, backup_filename]):
            return jsonify({'error': 'Product name, ROI ID, and backup filename are required'}), 400
        
        # Security check: ensure filename is a valid backup file
        if not backup_filename.startswith('original_') or not backup_filename.endswith('_old_best.jpg'):
            return jsonify({'error': 'Invalid backup filename format. Must be original_*_old_best.jpg'}), 400
        
        if '..' in backup_filename or '/' in backup_filename or '\\' in backup_filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        # Golden ROI directory path (relative to project root)
        project_root = os.path.join(os.path.dirname(__file__), '..')
        golden_roi_dir = os.path.join(project_root, 'config', 'products', product_name, 'golden_rois', f'roi_{roi_id}')
        
        if not os.path.exists(golden_roi_dir):
            return jsonify({'error': 'Golden ROI directory not found'}), 404
        
        backup_path = os.path.join(golden_roi_dir, backup_filename)
        best_golden_path = os.path.join(golden_roi_dir, 'best_golden.jpg')
        
        if not os.path.exists(backup_path):
            return jsonify({'error': f"Backup file '{backup_filename}' not found"}), 404
        
        # Backup current best golden if it exists
        backup_message = ""
        if os.path.exists(best_golden_path):
            timestamp = int(time.time())
            current_backup_name = f'original_{timestamp}_old_best.jpg'
            current_backup_path = os.path.join(golden_roi_dir, current_backup_name)
            os.rename(best_golden_path, current_backup_path)
            backup_message = f"Current best golden backed up as '{current_backup_name}'"
            logger.info(f"Backed up current best golden as {current_backup_name}")
        
        # Copy the backup file to become best golden
        shutil.copy2(backup_path, best_golden_path)
        
        logger.info(f"Restored {backup_filename} to best golden for product {product_name}, ROI {roi_id}")
        return jsonify({
            'message': f"Successfully restored '{backup_filename}' to best golden sample",
            'restored_from': backup_filename,
            'backed_up_current': backup_message
        })
        
    except Exception as e:
        logger.error(f"Restore golden sample error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/golden-sample/delete', methods=['DELETE'])
def delete_golden_sample_enhanced():
    """Delete a specific golden sample."""
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        roi_id = data.get('roi_id')
        sample_name = data.get('sample_name')
        
        if not all([product_name, roi_id, sample_name]):
            return jsonify({'error': 'Product name, ROI ID, and sample name are required'}), 400
        
        # Golden ROI directory path (relative to project root)
        project_root = os.path.join(os.path.dirname(__file__), '..')
        golden_roi_dir = os.path.join(project_root, 'config', 'products', product_name, 'golden_rois', f'roi_{roi_id}')
        
        # Prevent deletion of best_golden.jpg if it's the only sample
        if sample_name == 'best_golden.jpg':
            jpg_files = glob.glob(os.path.join(golden_roi_dir, '*.jpg'))
            if len(jpg_files) <= 1:
                return jsonify({'error': 'Cannot delete the only golden sample. Add alternatives first.'}), 400
        sample_path = os.path.join(golden_roi_dir, sample_name)
        
        if not os.path.exists(sample_path):
            return jsonify({'error': 'Sample file not found'}), 404
        
        # Delete the sample
        os.remove(sample_path)
        
        logger.info(f"Deleted golden sample {sample_name} for product {product_name}, ROI {roi_id}")
        return jsonify({'message': f"Golden sample '{sample_name}' deleted successfully"})
        
    except Exception as e:
        logger.error(f"Delete enhanced golden sample error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_name>/golden/<int:roi_id>', methods=['GET'])
def get_golden_sample(product_name, roi_id):
    """Get golden sample for a specific ROI."""
    try:
        # Create golden samples directory path
        golden_dir = os.path.join('config', 'products', product_name, 'golden')
        golden_path = os.path.join(golden_dir, f'roi_{roi_id}_golden.jpg')
        
        if os.path.exists(golden_path):
            with open(golden_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            return jsonify({'image': image_data})
        else:
            return jsonify({'error': 'Golden sample not found'}), 404
            
    except Exception as e:
        logger.error(f"Get golden sample error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_name>/golden/<int:roi_id>', methods=['POST'])
def save_golden_sample(product_name, roi_id):
    """Save golden sample for a specific ROI."""
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
            
        # Create golden samples directory
        golden_dir = os.path.join('config', 'products', product_name, 'golden')
        os.makedirs(golden_dir, exist_ok=True)
        
        # Save golden sample image
        golden_path = os.path.join(golden_dir, f'roi_{roi_id}_golden.jpg')
        with open(golden_path, 'wb') as f:
            f.write(base64.b64decode(image_data))
            
        logger.info(f"Saved golden sample for product {product_name}, ROI {roi_id}")
        return jsonify({'message': 'Golden sample saved successfully'})
        
    except Exception as e:
        logger.error(f"Save golden sample error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<product_name>/golden/<int:roi_id>', methods=['DELETE'])
def delete_golden_sample(product_name, roi_id):
    """Delete golden sample for a specific ROI."""
    try:
        golden_dir = os.path.join('config', 'products', product_name, 'golden')
        golden_path = os.path.join(golden_dir, f'roi_{roi_id}_golden.jpg')
        
        if os.path.exists(golden_path):
            os.remove(golden_path)
            logger.info(f"Deleted golden sample for product {product_name}, ROI {roi_id}")
            return jsonify({'message': 'Golden sample deleted successfully'})
        else:
            return jsonify({'error': 'Golden sample not found'}), 404
            
    except Exception as e:
        logger.error(f"Delete golden sample error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/golden-sample/products', methods=['GET'])
def list_products_with_golden_samples():
    """List all products that have golden samples with summary statistics.
    ---
    tags:
      - Golden Samples
    summary: List all products with golden samples
    description: Get a list of all products that have golden sample configurations with summary statistics.
    responses:
      200:
        description: List of products with golden samples
        schema:
          type: object
          properties:
            products:
              type: array
              items:
                type: object
                properties:
                  product_name:
                    type: string
                  total_rois:
                    type: integer
                    description: Number of ROIs with golden samples
                  total_samples:
                    type: integer
                    description: Total number of golden sample images
                  total_size:
                    type: integer
                    description: Total size of all golden samples in bytes
                  rois:
                    type: array
                    description: List of ROI IDs with golden samples
                    items:
                      type: integer
            total_products:
              type: integer
      500:
        description: Error listing products
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        # Products directory path (relative to project root)
        project_root = os.path.join(os.path.dirname(__file__), '..')
        products_dir = os.path.join(project_root, 'config', 'products')
        
        if not os.path.exists(products_dir):
            return jsonify({'products': [], 'total_products': 0})
        
        products = []
        
        # Iterate through all product directories
        for product_name in os.listdir(products_dir):
            product_path = os.path.join(products_dir, product_name)
            
            # Skip if not a directory
            if not os.path.isdir(product_path):
                continue
            
            golden_rois_dir = os.path.join(product_path, 'golden_rois')
            
            # Skip if no golden_rois directory
            if not os.path.exists(golden_rois_dir):
                continue
            
            # Get all ROI directories
            roi_dirs = [d for d in os.listdir(golden_rois_dir) 
                       if os.path.isdir(os.path.join(golden_rois_dir, d)) and d.startswith('roi_')]
            
            if not roi_dirs:
                continue
            
            # Calculate statistics
            total_samples = 0
            total_size = 0
            roi_ids = []
            
            for roi_dir in roi_dirs:
                roi_path = os.path.join(golden_rois_dir, roi_dir)
                jpg_files = glob.glob(os.path.join(roi_path, '*.jpg'))
                
                if jpg_files:
                    # Extract ROI ID from directory name (e.g., roi_5 -> 5)
                    try:
                        roi_id = int(roi_dir.split('_')[1])
                        roi_ids.append(roi_id)
                    except (IndexError, ValueError):
                        continue
                    
                    total_samples += len(jpg_files)
                    
                    # Calculate total size
                    for jpg_file in jpg_files:
                        try:
                            total_size += os.path.getsize(jpg_file)
                        except OSError:
                            pass
            
            if roi_ids:  # Only add product if it has valid ROIs
                roi_ids.sort()
                products.append({
                    'product_name': product_name,
                    'total_rois': len(roi_ids),
                    'total_samples': total_samples,
                    'total_size': total_size,
                    'rois': roi_ids
                })
        
        # Sort products by name
        products.sort(key=lambda x: x['product_name'])
        
        return jsonify({
            'products': products,
            'total_products': len(products)
        })
        
    except Exception as e:
        logger.error(f"List products with golden samples error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/golden-sample/rename-folders', methods=['POST'])
def rename_golden_sample_folders():
    """Rename golden sample folders when ROI indices change after deletion."""
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        roi_mapping = data.get('roi_mapping')  # {old_roi_id: new_roi_id}
        
        if not product_name or not roi_mapping:
            return jsonify({'error': 'Product name and ROI mapping are required'}), 400
        
        golden_rois_dir = os.path.join('config', 'products', product_name, 'golden_rois')
        
        if not os.path.exists(golden_rois_dir):
            logger.info(f"No golden ROIs directory found for product {product_name}")
            return jsonify({'message': 'No golden samples to rename'})
        
        renamed_count = 0
        temp_suffix = "_temp_rename"
        
        # Get all current folders
        existing_folders = set()
        if os.path.exists(golden_rois_dir):
            existing_folders = {f for f in os.listdir(golden_rois_dir) 
                             if os.path.isdir(os.path.join(golden_rois_dir, f)) and f.startswith('roi_')}
        
        # First pass: rename to temporary names to avoid conflicts
        temp_renames = {}
        for old_roi_id, new_roi_id in roi_mapping.items():
            if old_roi_id == new_roi_id:
                continue  # No change needed
                
            old_folder_name = f'roi_{old_roi_id}'
            old_folder = os.path.join(golden_rois_dir, old_folder_name)
            temp_folder = os.path.join(golden_rois_dir, f'roi_{old_roi_id}{temp_suffix}')
            
            if old_folder_name in existing_folders and os.path.exists(old_folder):
                os.rename(old_folder, temp_folder)
                temp_renames[temp_folder] = new_roi_id
                logger.info(f"Temporarily renamed {old_folder} to {temp_folder}")
        
        # Remove destination folders that will be overwritten
        for old_roi_id, new_roi_id in roi_mapping.items():
            if old_roi_id == new_roi_id:
                continue
                
            new_folder_name = f'roi_{new_roi_id}'
            new_folder = os.path.join(golden_rois_dir, new_folder_name)
            
            # Only remove if it's not being renamed from a temp folder
            if new_folder_name in existing_folders and os.path.exists(new_folder):
                # Check if this folder is the destination of any mapping
                is_destination = any(roi_mapping[k] == new_roi_id for k in roi_mapping if k != old_roi_id)
                if not is_destination or f'roi_{old_roi_id}' not in [f'roi_{k}' for k in roi_mapping.keys()]:
                    shutil.rmtree(new_folder)
                    logger.info(f"Removed existing folder {new_folder} to make way for rename")
        
        # Second pass: rename from temporary names to final names
        for temp_folder, new_roi_id in temp_renames.items():
            new_folder = os.path.join(golden_rois_dir, f'roi_{new_roi_id}')
            
            # Remove destination if it still exists
            if os.path.exists(new_folder):
                shutil.rmtree(new_folder)
                logger.info(f"Removed existing folder {new_folder}")
            
            # Rename from temp to final name
            os.rename(temp_folder, new_folder)
            renamed_count += 1
            logger.info(f"Renamed {temp_folder} to {new_folder}")
        
        message = f"Renamed {renamed_count} golden sample folders"
        logger.info(f"Golden folder renaming complete for product {product_name}: {message}")
        return jsonify({'message': message, 'renamed_count': renamed_count})
        
    except Exception as e:
        logger.error(f"Rename golden sample folders error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schema/roi', methods=['GET'])
def get_roi_structure_schema():
    """Get ROI structure specification.
    ---
    tags:
      - Schema
    summary: Get ROI structure specification
    description: Returns the current ROI structure format, field definitions, and version information
    responses:
      200:
        description: ROI structure specification
        schema:
          type: object
          properties:
            version:
              type: string
              example: "3.0"
            format:
              type: string
              example: "11-field"
            updated:
              type: string
              format: date
            fields:
              type: array
            backward_compatible:
              type: array
            priority_logic:
              type: object
    """
    try:
        schema = {
            'version': '3.2',
            'format': '12-field',
            'updated': '2025-11-01',
            'description': 'ROI (Region of Interest) structure specification with simplified color checking',
            'fields': [
                {
                    'index': 0,
                    'name': 'idx',
                    'type': 'int',
                    'required': True,
                    'description': 'ROI index (1-based)',
                    'constraints': 'Must be unique, positive integer'
                },
                {
                    'index': 1,
                    'name': 'type',
                    'type': 'int',
                    'required': True,
                    'description': 'ROI type',
                    'constraints': '1=Barcode, 2=Compare, 3=OCR, 4=Color'
                },
                {
                    'index': 2,
                    'name': 'coords',
                    'type': 'tuple[int, int, int, int]',
                    'required': True,
                    'description': 'Coordinates (x1, y1, x2, y2)',
                    'constraints': 'x1 < x2, y1 < y2, all non-negative'
                },
                {
                    'index': 3,
                    'name': 'focus',
                    'type': 'int',
                    'required': True,
                    'description': 'Focus value',
                    'constraints': 'Positive integer, typically 100-500',
                    'default': 305
                },
                {
                    'index': 4,
                    'name': 'exposure',
                    'type': 'int',
                    'required': True,
                    'description': 'Exposure time in microseconds',
                    'constraints': 'Positive integer',
                    'default': 3000
                },
                {
                    'index': 5,
                    'name': 'ai_threshold',
                    'type': 'float | None',
                    'required': True,
                    'description': 'AI similarity threshold (0.0-1.0)',
                    'constraints': 'Only for Compare ROIs, None for Barcode/OCR',
                    'default': 0.85
                },
                {
                    'index': 6,
                    'name': 'feature_method',
                    'type': 'str',
                    'required': True,
                    'description': 'Feature extraction method',
                    'constraints': 'mobilenet, sift, orb, opencv, barcode, ocr',
                    'default': 'mobilenet (Type 2), barcode (Type 1), ocr (Type 3)'
                },
                {
                    'index': 7,
                    'name': 'rotation',
                    'type': 'int',
                    'required': True,
                    'description': 'Rotation angle in degrees',
                    'constraints': '0, 90, 180, 270',
                    'default': 0
                },
                {
                    'index': 8,
                    'name': 'device_location',
                    'type': 'int',
                    'required': True,
                    'description': 'Device identifier (1-4)',
                    'constraints': '1, 2, 3, or 4',
                    'default': 1
                },
                {
                    'index': 9,
                    'name': 'expected_text',
                    'type': 'str | None',
                    'required': False,
                    'description': 'Expected text for OCR comparison',
                    'constraints': 'Only for OCR ROIs with validation',
                    'default': None
                },
                {
                    'index': 10,
                    'name': 'is_device_barcode',
                    'type': 'bool | None',
                    'required': False,
                    'description': 'Device main barcode flag (NEW in v3.0)',
                    'constraints': 'Only meaningful for Barcode ROIs (Type 1)',
                    'default': None,
                    'added_in': '3.0'
                },
                {
                    'index': 11,
                    'name': 'color_config',
                    'type': 'dict | None',
                    'required': False,
                    'description': 'Color configuration for color validation (UPDATED in v3.2)',
                    'constraints': 'Only for Color ROIs (Type 4). Supports two formats',
                    'default': None,
                    'added_in': '3.1',
                    'updated_in': '3.2',
                    'formats': {
                        'simple': {
                            'description': 'Simple color checking with tolerance (NEW in v3.2)',
                            'fields': {
                                'expected_color': 'array[int, int, int] - Target RGB color (e.g., [255, 0, 0] for red)',
                                'color_tolerance': 'int - Deviation allowed (default: 10). Creates range [expected ± tolerance]',
                                'min_pixel_percentage': 'float - Minimum match percentage for pass (default: 5.0)'
                            },
                            'example': {
                                'expected_color': [255, 0, 0],
                                'color_tolerance': 10,
                                'min_pixel_percentage': 5.0
                            },
                            'logic': 'Creates color range from expected_color ± color_tolerance. Pass if >= min_pixel_percentage pixels match.'
                        },
                        'legacy': {
                            'description': 'Multiple color ranges with manual bounds (v3.1)',
                            'fields': {
                                'color_ranges': 'array[object] - Array of {name, lower, upper, color_space, threshold}'
                            },
                            'format': {
                                'name': 'str - Color name (e.g., "red", "blue")',
                                'lower': 'array[int, int, int] - Lower bound RGB/HSV values',
                                'upper': 'array[int, int, int] - Upper bound RGB/HSV values',
                                'color_space': 'str - "RGB" or "HSV"',
                                'threshold': 'float - Match percentage threshold (0-100)'
                            },
                            'note': 'Multiple ranges can have same name - matches are aggregated'
                        }
                    },
                    'note': 'Priority: embedded config > product-level config file. One ROI checks one color only.'
                }
            ],
            'backward_compatible': [
                {'version': '3.0', 'fields': 11, 'migration': 'Add color_ranges=None'},
                {'version': '2.0', 'fields': 10, 'migration': 'Add is_device_barcode=None, color_ranges=None'},
                {'version': '1.9', 'fields': 9, 'migration': 'Add expected_text=None, is_device_barcode=None, color_ranges=None'},
                {'version': '1.8', 'fields': 8, 'migration': 'Add device_location=1, expected_text=None, is_device_barcode=None, color_ranges=None'},
                {'version': '1.7', 'fields': 7, 'migration': 'Add rotation=0, device_location=1, expected_text=None, is_device_barcode=None, color_ranges=None'},
                {'version': '1.6', 'fields': 6, 'migration': 'Infer feature_method, add rotation=0, device_location=1, expected_text=None, is_device_barcode=None, color_ranges=None'},
                {'version': '1.5', 'fields': 5, 'migration': 'Add exposure=3000, infer feature_method, add rotation=0, device_location=1, expected_text=None, is_device_barcode=None, color_ranges=None'}
            ],
            'roi_types': {
                '1': {
                    'name': 'Barcode',
                    'description': 'Barcode detection and reading',
                    'relevant_fields': ['idx', 'type', 'coords', 'focus', 'exposure', 'feature_method', 'rotation', 'device_location', 'is_device_barcode'],
                    'ignored_fields': ['ai_threshold', 'expected_text']
                },
                '2': {
                    'name': 'Compare',
                    'description': 'AI-based image comparison with golden samples',
                    'relevant_fields': ['idx', 'type', 'coords', 'focus', 'exposure', 'ai_threshold', 'feature_method', 'rotation', 'device_location'],
                    'ignored_fields': ['expected_text', 'is_device_barcode']
                },
                '3': {
                    'name': 'OCR',
                    'description': 'Optical character recognition with optional validation',
                    'relevant_fields': ['idx', 'type', 'coords', 'focus', 'exposure', 'feature_method', 'rotation', 'device_location', 'expected_text'],
                    'ignored_fields': ['ai_threshold', 'is_device_barcode']
                },
                '4': {
                    'name': 'Color',
                    'description': 'Color validation with simple tolerance or multiple ranges',
                    'relevant_fields': ['idx', 'type', 'coords', 'focus', 'exposure', 'rotation', 'device_location', 'color_config'],
                    'ignored_fields': ['ai_threshold', 'feature_method', 'expected_text', 'is_device_barcode'],
                    'configuration': 'Embedded color_config in ROI (v3.2) or fallback to config/products/{product}/colors_config_{product}.json',
                    'note': 'One ROI checks one color only. Use simple format (expected_color + tolerance) for easier setup. Priority: ROI embedded config > product-level config file',
                    'updated_in': '3.2'
                }
            },
            'barcode_priority_logic': {
                'description': 'Priority order for selecting device barcode in results',
                'priorities': [
                    {
                        'priority': 0,
                        'source': 'ROI Barcode with is_device_barcode=True',
                        'description': 'Explicitly marked device identifier (NEW in v3.0)',
                        'added_in': '3.0'
                    },
                    {
                        'priority': 1,
                        'source': 'Any ROI Barcode',
                        'description': 'First valid barcode detected from barcode ROIs'
                    },
                    {
                        'priority': 2,
                        'source': 'Manual Multi-Device (device_barcodes[device_id])',
                        'description': 'Manually provided per-device barcode'
                    },
                    {
                        'priority': 3,
                        'source': 'Legacy Single (device_barcode)',
                        'description': 'Legacy single barcode for all devices'
                    },
                    {
                        'priority': 4,
                        'source': 'Default',
                        'description': 'Fallback to "N/A"'
                    }
                ]
            },
            'example': {
                'barcode_roi': [1, 1, [50, 50, 150, 100], 305, 3000, None, 'barcode', 0, 1, None, True, None],
                'compare_roi': [2, 2, [200, 50, 300, 150], 305, 3000, 0.85, 'mobilenet', 0, 1, None, None, None],
                'ocr_roi': [3, 3, [350, 50, 450, 100], 305, 3000, None, 'ocr', 0, 1, 'EXPECTED_TEXT', None, None],
                'color_roi_simple_array': [4, 4, [500, 50, 600, 150], 305, 3000, None, None, 0, 1, None, None, {
                    'expected_color': [255, 0, 0],
                    'color_tolerance': 10,
                    'min_pixel_percentage': 5.0
                }],
                'color_roi_simple_object': {
                    'idx': 4,
                    'type': 4,
                    'coords': [500, 50, 600, 150],
                    'focus': 305,
                    'exposure': 3000,
                    'ai_threshold': None,
                    'feature_method': None,
                    'rotation': 0,
                    'device_location': 1,
                    'expected_text': None,
                    'is_device_barcode': None,
                    'expected_color': [255, 0, 0],
                    'color_tolerance': 10,
                    'min_pixel_percentage': 5.0
                },
                'color_roi_legacy_object': {
                    'idx': 5,
                    'type': 4,
                    'coords': [650, 50, 750, 150],
                    'focus': 305,
                    'exposure': 3000,
                    'ai_threshold': None,
                    'feature_method': None,
                    'rotation': 0,
                    'device_location': 1,
                    'expected_text': None,
                    'is_device_barcode': None,
                    'color_ranges': [
                        {'name': 'red', 'lower': [200, 0, 0], 'upper': [255, 50, 50], 'color_space': 'RGB', 'threshold': 50.0}
                    ]
                }
            },
            'documentation': '/docs/ROI_DEFINITION_SPECIFICATION.md'
        }
        
        return jsonify(schema)
    
    except Exception as e:
        logger.error(f"Get ROI schema error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schema/result', methods=['GET'])
def get_result_structure_schema():
    """Get inspection result structure specification.
    ---
    tags:
      - Schema
    summary: Get inspection result structure specification
    description: Returns the inspection result format, field definitions, and validation rules
    responses:
      200:
        description: Inspection result structure specification
        schema:
          type: object
          properties:
            version:
              type: string
            format:
              type: string
            updated:
              type: string
            structure:
              type: object
    """
    try:
        schema = {
            'version': '2.0',
            'format': 'JSON Object',
            'updated': '2025-10-03',
            'description': 'Inspection result structure specification',
            'top_level_fields': {
                'roi_results': {
                    'type': 'array',
                    'required': True,
                    'description': 'Array of individual ROI processing results',
                    'element_type': 'ROIResult object'
                },
                'device_summaries': {
                    'type': 'object',
                    'required': True,
                    'description': 'Dictionary of per-device summary statistics',
                    'key_type': 'string (device_id: "1", "2", "3", "4")',
                    'value_type': 'DeviceSummary object'
                },
                'overall_result': {
                    'type': 'object',
                    'required': True,
                    'description': 'Overall inspection pass/fail and statistics',
                    'structure': 'OverallResult object'
                },
                'processing_time': {
                    'type': 'float',
                    'required': True,
                    'description': 'Processing duration in seconds',
                    'unit': 'seconds'
                },
                'timestamp': {
                    'type': 'float',
                    'required': False,
                    'description': 'Unix timestamp when inspection completed',
                    'unit': 'seconds since epoch'
                },
                'session_id': {
                    'type': 'string',
                    'required': False,
                    'description': 'Session UUID (for grouped inspections)',
                    'format': 'UUID'
                },
                'product_name': {
                    'type': 'string',
                    'required': False,
                    'description': 'Product configuration name'
                }
            },
            'roi_result_structure': {
                'common_fields': {
                    'roi_id': {'type': 'int', 'required': True, 'description': 'ROI index (1-based)'},
                    'device_id': {'type': 'int', 'required': True, 'description': 'Device location (1-4)'},
                    'roi_type_name': {'type': 'string', 'required': True, 'description': 'barcode, compare, ocr, or color'},
                    'passed': {'type': 'bool', 'required': True, 'description': 'Pass/fail status'},
                    'coordinates': {'type': 'array[int]', 'required': True, 'description': '[x1, y1, x2, y2]'},
                    'roi_image_path': {'type': 'string', 'required': False, 'description': 'Path to ROI image in shared folder (relative to client mount point)'},
                    'golden_image_path': {'type': 'string', 'required': False, 'description': 'Path to golden image in shared folder (relative to client mount point)'},
                    'error': {'type': 'string', 'required': False, 'description': 'Error message if failed'}
                },
                'type_specific_fields': {
                    'barcode': {
                        'barcode_values': {
                            'type': 'array[string]',
                            'required': True,
                            'description': 'Array of detected barcodes',
                            'pass_condition': 'Array not empty and first element valid'
                        }
                    },
                    'compare': {
                        'match_result': {
                            'type': 'string',
                            'required': True,
                            'description': 'Match or Different',
                            'values': ['Match', 'Different']
                        },
                        'ai_similarity': {
                            'type': 'float',
                            'required': True,
                            'description': 'Similarity score (0.0-1.0)',
                            'range': [0.0, 1.0]
                        },
                        'threshold': {
                            'type': 'float',
                            'required': True,
                            'description': 'Threshold used (0.0-1.0)',
                            'range': [0.0, 1.0]
                        },
                        'pass_condition': 'ai_similarity >= threshold'
                    },
                    'ocr': {
                        'ocr_text': {
                            'type': 'string',
                            'required': True,
                            'description': 'Recognized text with validation result',
                            'pass_condition': 'Contains [PASS:] or no [FAIL:] and has text'
                        }
                    },
                    'color': {
                        'detected_color': {
                            'type': 'string',
                            'required': True,
                            'description': 'Name of detected color (from color_ranges configuration)'
                        },
                        'match_percentage': {
                            'type': 'float',
                            'required': True,
                            'description': 'Total match percentage (0.0-100.0)',
                            'range': [0.0, 100.0]
                        },
                        'match_percentage_raw': {
                            'type': 'float',
                            'required': False,
                            'description': 'Raw match sum (can exceed 100% with multiple ranges)'
                        },
                        'dominant_color': {
                            'type': 'array[int]',
                            'required': True,
                            'description': 'RGB values of dominant color [R, G, B]'
                        },
                        'threshold': {
                            'type': 'float',
                            'required': True,
                            'description': 'Threshold percentage used',
                            'range': [0.0, 100.0]
                        },
                        'pass_condition': 'match_percentage >= threshold',
                        'note': 'Supports multiple color ranges with same name (aggregated)'
                    }
                }
            },
            'device_summary_structure': {
                'total_rois': {'type': 'int', 'required': True, 'description': 'Total ROIs for this device'},
                'passed_rois': {'type': 'int', 'required': True, 'description': 'Number that passed'},
                'failed_rois': {'type': 'int', 'required': True, 'description': 'Number that failed'},
                'device_passed': {
                    'type': 'bool',
                    'required': True,
                    'description': 'Device overall pass/fail',
                    'logic': 'passed_rois == total_rois'
                },
                'barcode': {
                    'type': 'string',
                    'required': True,
                    'description': 'Device barcode identifier',
                    'default': 'N/A',
                    'priority_logic': 'See barcode_priority_logic'
                },
                'results': {
                    'type': 'array',
                    'required': True,
                    'description': 'ROI results for this device',
                    'element_type': 'ROIResult object'
                }
            },
            'overall_result_structure': {
                'passed': {
                    'type': 'bool',
                    'required': True,
                    'description': 'Overall inspection pass/fail',
                    'logic': 'passed_rois == total_rois AND total_rois > 0'
                },
                'total_rois': {'type': 'int', 'required': True, 'description': 'Total ROIs processed'},
                'passed_rois': {'type': 'int', 'required': True, 'description': 'Total ROIs that passed'},
                'failed_rois': {'type': 'int', 'required': True, 'description': 'Total ROIs that failed'}
            },
            'barcode_priority_logic': {
                'description': 'Priority order for device_summaries[device_id][\'barcode\'] selection',
                'priorities': [
                    {
                        'priority': 0,
                        'source': 'ROI Barcode with is_device_barcode=True',
                        'description': 'Highest priority - explicitly marked device identifier',
                        'added_in': 'v3.0'
                    },
                    {
                        'priority': 1,
                        'source': 'Any ROI Barcode',
                        'description': 'First valid barcode detected from barcode ROIs'
                    },
                    {
                        'priority': 2,
                        'source': 'Manual device_barcodes[device_id]',
                        'description': 'API parameter device_barcodes dictionary'
                    },
                    {
                        'priority': 3,
                        'source': 'Legacy device_barcode',
                        'description': 'API parameter device_barcode (single for all devices)'
                    },
                    {
                        'priority': 4,
                        'source': 'Default',
                        'description': 'Fallback to "N/A"'
                    }
                ]
            },
            'validation_rules': {
                'consistency': [
                    'total_rois must equal len(roi_results)',
                    'total_rois must equal passed_rois + failed_rois',
                    'overall.passed must equal (passed_rois == total_rois AND total_rois > 0)',
                    'For each device: total_rois must equal len(results)',
                    'For each device: device_passed must equal (passed_rois == total_rois)'
                ],
                'types': [
                    'roi_results must be array',
                    'device_summaries must be object with string keys',
                    'overall_result must be object',
                    'processing_time must be number >= 0',
                    'roi_id must be positive integer',
                    'device_id must be 1, 2, 3, or 4',
                    'coordinates must be array of 4 integers',
                    'passed must be boolean'
                ],
                'type_specific': [
                    'Barcode: barcode_values must be array',
                    'Compare: ai_similarity and threshold must be 0.0 to 1.0',
                    'Compare: match_result must be "Match" or "Different"',
                    'OCR: ocr_text must be string'
                ]
            },
            'example': {
                'roi_results': [
                    {
                        'roi_id': 1,
                        'device_id': 1,
                        'roi_type_name': 'barcode',
                        'passed': True,
                        'coordinates': [50, 50, 150, 100],
                        'barcode_values': ['ABC123456'],
                        'roi_image_path': '/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_1.jpg'
                    },
                    {
                        'roi_id': 2,
                        'device_id': 1,
                        'roi_type_name': 'compare',
                        'passed': True,
                        'coordinates': [200, 50, 300, 150],
                        'match_result': 'Match',
                        'ai_similarity': 0.92,
                        'threshold': 0.85,
                        'roi_image_path': '/mnt/visual-aoi-shared/sessions/{uuid}/output/roi_2.jpg',
                        'golden_image_path': '/mnt/visual-aoi-shared/sessions/{uuid}/output/golden_2.jpg'
                    }
                ],
                'device_summaries': {
                    '1': {
                        'total_rois': 2,
                        'passed_rois': 2,
                        'failed_rois': 0,
                        'device_passed': True,
                        'barcode': 'ABC123456',
                        'results': []
                    }
                },
                'overall_result': {
                    'passed': True,
                    'total_rois': 2,
                    'passed_rois': 2,
                    'failed_rois': 0
                },
                'processing_time': 1.234
            },
            'documentation': '/docs/INSPECTION_RESULT_SPECIFICATION.md'
        }
        
        return jsonify(schema)
    
    except Exception as e:
        logger.error(f"Get result schema error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schema/version', methods=['GET'])
def get_schema_version():
    """Get current schema versions.
    ---
    tags:
      - Schema
    summary: Get current schema versions
    description: Returns version information for ROI and result structures
    responses:
      200:
        description: Schema version information
        schema:
          type: object
          properties:
            roi_structure:
              type: object
            result_structure:
              type: object
            server_version:
              type: string
    """
    try:
        version_info = {
            'roi_structure': {
                'version': '3.0',
                'format': '11-field',
                'fields': 11,
                'updated': '2025-10-03',
                'backward_compatible_versions': ['1.0', '1.5', '1.6', '1.7', '1.8', '1.9', '2.0'],
                'changes': {
                    '3.0': 'Added is_device_barcode field for device main barcode identification',
                    '2.0': 'Added expected_text field for OCR validation',
                    '1.9': 'Added device_location field for multi-device support',
                    '1.8': 'Added rotation field for image rotation',
                    '1.7': 'Added feature_method field'
                }
            },
            'result_structure': {
                'version': '2.0',
                'format': 'JSON Object',
                'updated': '2025-10-03',
                'main_sections': ['roi_results', 'device_summaries', 'overall_result', 'processing_time'],
                'changes': {
                    '2.0': 'Enhanced barcode priority logic with is_device_barcode support',
                    '1.0': 'Initial structure with device_summaries and overall_result'
                }
            },
            'server_version': '3.0.0',
            'api_version': '1.0',
            'updated': '2025-10-03',
            'endpoints': {
                'roi_schema': '/api/schema/roi',
                'result_schema': '/api/schema/result',
                'version': '/api/schema/version'
            }
        }
        
        return jsonify(version_info)
    
    except Exception as e:
        logger.error(f"Get schema version error: {e}")
        return jsonify({'error': str(e)}), 500

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the API server."""
    logger.info(f"Starting Visual AOI API Server on {host}:{port}")
    logger.info(f"Modules available: {MODULES_AVAILABLE}")
    
    # Start cleanup thread
    def cleanup_thread():
        while True:
            try:
                cleanup_expired_sessions()
                time.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Cleanup thread error: {e}")
    
    cleanup_worker = threading.Thread(target=cleanup_thread, daemon=True)
    cleanup_worker.start()
    
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Visual AOI API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug)
