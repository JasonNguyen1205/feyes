from __future__ import annotations

import atexit
import base64
import json
import logging
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import requests
from flask import Flask, Response, jsonify, render_template, request, send_from_directory

from src import camera as tis_camera

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global lock for camera operations to prevent concurrent access
camera_lock = threading.Lock()


@dataclass
class DeviceBarcodeEntry:
    """Device barcode entry for inspection."""
    device_id: int
    barcode: str


@dataclass
class ROIGroup:
    """ROI group with camera settings and ROI list."""
    focus: int
    exposure: int
    rois: List[Dict[str, Any]]


@dataclass
class AOIState:
    """Track connection, session, and cached metadata for the AOI client."""

    server_url: str = "http://10.100.27.156:5000"
    connected: bool = False
    session_id: Optional[str] = None
    session_product: Optional[str] = None
    products_cache: List[Dict[str, Any]] = field(default_factory=list)
    last_result: Optional[Dict[str, Any]] = None
    camera_serial: Optional[str] = None
    camera_initialized: bool = False
    live_view_active: bool = False
    available_cameras: List[Dict[str, Any]] = field(default_factory=list)
    roi_groups_cache: Dict[str, ROIGroup] = field(default_factory=dict)
    first_roi_group_settings: Optional[Dict[str, Any]] = None
    device_barcodes: List[DeviceBarcodeEntry] = field(default_factory=list)


state = AOIState()


def make_server_url(path: str) -> str:
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{state.server_url.rstrip('/')}{path}"


def call_server(method: str, path: str, *, timeout: float = 10.0, **kwargs) -> requests.Response:
    if not state.server_url:
        raise ValueError("Server URL is not configured")

    url = make_server_url(path)
    response = requests.request(method, url, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response


def fetch_products_from_server() -> List[Dict[str, Any]]:
    """
    Fetch products list from server.
    
    Returns:
        List of product dictionaries
        
    Raises:
        RuntimeError: If server connection fails or no products are returned
    """
    try:
        response = call_server("GET", "/api/products", timeout=10)
        payload = response.json()
        if isinstance(payload, dict) and "products" in payload:
            products = payload["products"]
            if not products:
                error_msg = "Server returned empty products list"
                app.logger.error(error_msg)
                raise RuntimeError(error_msg)
            app.logger.info(f"✓ Fetched {len(products)} products from server")
            return products
        if isinstance(payload, list):
            products: List[Dict[str, Any]] = []
            for item in payload:
                if isinstance(item, str):
                    products.append({"product_name": item})
                elif isinstance(item, dict):
                    products.append(item)
            if not products:
                error_msg = "Server returned empty products list"
                app.logger.error(error_msg)
                raise RuntimeError(error_msg)
            app.logger.info(f"✓ Fetched {len(products)} products from server")
            return products
        error_msg = "Server returned invalid products format"
        app.logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as exc:
        error_msg = f"Failed to fetch products from server: {exc}"
        app.logger.error(error_msg)
        raise RuntimeError(error_msg) from exc


def analyze_devices_needing_barcodes(roi_groups: Dict[str, Any]) -> List[int]:
    """
    Analyze ROI groups to determine which devices need manual barcode input.
    A device needs manual barcode input if it has NO device barcode ROIs defined.
    
    Logic (Updated October 9, 2025):
    - Collect all unique device IDs from all ROI groups
    - Determine max device ID to ensure we check ALL devices (1 to max_device_id)
    - For each device, check if it has at least one device barcode ROI
    - A barcode ROI is considered "device barcode" if is_device_barcode field is True (or missing for backward compat)
    - Return list of device IDs that have NO device barcode ROIs
    
    IMPORTANT: Even if a device has NO ROIs defined at all, it will still be included
    in the list of devices needing manual barcode input, ensuring users can input
    barcodes for all devices in the product configuration.
    
    Args:
        roi_groups: Dictionary of ROI groups from server
        
    Returns:
        List of device IDs (integers) that need manual barcode input
    """
    device_has_device_barcode = {}  # {device_id: has_device_barcode_roi}
    max_device_id = 0
    
    # Analyze all ROI groups to find all device IDs and check for barcode ROIs
    for group_key, group_data in roi_groups.items():
        if not isinstance(group_data, dict) or 'rois' not in group_data:
            continue
            
        rois = group_data.get('rois', [])
        for roi in rois:
            # Handle both dict and array formats
            if isinstance(roi, dict):
                # Dictionary format (from server)
                # Server uses 'device_location' field, also check 'device' for backward compatibility
                device_id = roi.get('device_location') or roi.get('device', 1)
                roi_type = roi.get('type') or roi.get('roi_type') or roi.get('roi_type_name')
                is_barcode = roi_type in ['barcode', 1, '1']
                # Check is_device_barcode field (defaults to True for backward compatibility)
                is_device_barcode = roi.get('is_device_barcode', True)
            elif isinstance(roi, list):
                # Array format (from config files)
                device_id = roi[8] if len(roi) > 8 else 1
                roi_type = roi[1] if len(roi) > 1 else None
                is_barcode = roi_type in [1, '1'] or (len(roi) > 6 and roi[6] == 'barcode')
                # Check field [10] for is_device_barcode (defaults to True for backward compatibility)
                is_device_barcode = roi[10] if len(roi) > 10 else True
            else:
                continue
            
            # Track max device ID
            max_device_id = max(max_device_id, device_id)
            
            # Initialize device tracking
            if device_id not in device_has_device_barcode:
                device_has_device_barcode[device_id] = False
            
            # Only mark device as having barcode if it's a DEVICE barcode
            if is_barcode and is_device_barcode:
                device_has_device_barcode[device_id] = True
    
    # If no devices found in ROI groups, default to 1 device
    if max_device_id == 0:
        max_device_id = 1
        logger.info("No devices found in ROI groups, defaulting to 1 device")
    
    # Ensure ALL devices from 1 to max_device_id are tracked
    # This handles cases where some devices have NO ROIs defined at all
    for device_id in range(1, max_device_id + 1):
        if device_id not in device_has_device_barcode:
            device_has_device_barcode[device_id] = False
            logger.info(f"Device {device_id} has no ROIs defined - will need manual barcode input")
    
    # Return devices that do NOT have DEVICE barcode ROIs (need manual input)
    devices_need_manual = [dev_id for dev_id, has_barcode in device_has_device_barcode.items() if not has_barcode]
    
    logger.info(f"Device barcode analysis: {len(device_has_device_barcode)} total devices (1-{max_device_id}), {len(devices_need_manual)} need manual input: {devices_need_manual}")
    
    return sorted(devices_need_manual)


def fetch_roi_groups(product_name: str) -> Dict[str, Any]:
    """
    Fetch ROI groups from server.
    
    Args:
        product_name: Product identifier
        
    Returns:
        Dictionary of ROI groups
        
    Raises:
        RuntimeError: If server returns an error or ROI groups cannot be fetched
    """
    try:
        response = call_server("GET", f"/get_roi_groups/{product_name}", timeout=10)
        payload = response.json()
        roi_groups = payload.get("roi_groups", {}) if isinstance(payload, dict) else {}
        if roi_groups:
            app.logger.info(f"✓ Fetched {len(roi_groups)} ROI groups for product '{product_name}'")
            return roi_groups
        else:
            error_msg = f"No ROI groups returned from server for product '{product_name}'"
            app.logger.error(error_msg)
            raise RuntimeError(error_msg)
    except Exception as exc:
        error_msg = f"Failed to fetch ROI groups for product '{product_name}': {exc}"
        app.logger.error(error_msg)
        raise RuntimeError(error_msg) from exc


def ensure_connected() -> None:
    if not state.connected:
        raise RuntimeError("Server connection is not established")


def ensure_session() -> None:
    ensure_connected()
    if not state.session_id or not state.session_product:
        raise RuntimeError("No active session – create a session before inspecting")


def ensure_camera_initialized() -> None:
    tis_instance = tis_camera.get_camera_instance()
    if tis_instance is None:
        state.camera_initialized = False
    if not state.camera_initialized or tis_instance is None:
        raise RuntimeError("Camera is not initialized")


def close_active_session(silent: bool = True) -> None:
    """Close the active session with the server."""
    if not state.session_id:
        return

    try:
        call_server("POST", f"/api/session/{state.session_id}/close", timeout=10)
        logger.info(f"✓ Closed session {state.session_id}")
    except Exception as exc:  # noqa: BLE001
        if not silent:
            raise exc
        app.logger.warning("Failed to close remote session: %s", exc)
    finally:
        state.session_id = None
        state.session_product = None


def cleanup_on_shutdown() -> None:
    """Clean up resources when application shuts down."""
    logger.info("Application shutting down, cleaning up resources...")
    
    # Close active session
    if state.session_id:
        logger.info(f"Closing active session: {state.session_id}")
        close_active_session(silent=True)
    
    # Release camera resources
    try:
        if state.camera_initialized:
            logger.info("Releasing camera resources...")
            tis_camera.cleanup()
            state.camera_initialized = False
    except Exception as exc:
        logger.warning(f"Error during camera cleanup: {exc}")
    
    logger.info("✓ Cleanup completed")


def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name}, shutting down gracefully...")
    cleanup_on_shutdown()
    sys.exit(0)


def encode_image(image: np.ndarray) -> str:
    """Encode image to base64 (legacy method, prefer save_captured_image for new code)."""
    success, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not success:
        raise RuntimeError("Failed to encode captured image")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def save_captured_image(image: np.ndarray, group_key: str, session_id: str) -> str:
    """
    Save captured image to shared folder for inspection.
    
    Args:
        image: Captured image array
        group_key: ROI group key (e.g., "305,1200")
        session_id: Current session ID
        
    Returns:
        Absolute path to saved image file
    """
    # Create captures directory in session folder
    captures_dir = f"/mnt/visual-aoi-shared/sessions/{session_id}/captures"
    os.makedirs(captures_dir, exist_ok=True)
    
    # Generate filename from group key: group_305_1200.jpg
    filename = f"group_{group_key.replace(',', '_')}.jpg"
    filepath = os.path.join(captures_dir, filename)
    
    # Save image with high quality
    success = cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not success:
        raise RuntimeError(f"Failed to save image to {filepath}")
    
    logger.info(f"✓ Saved capture: {filepath} ({image.shape[1]}x{image.shape[0]})")
    
    return filepath


# ==================== ROI Normalization & Validation ====================

def roi_from_server_format(server_roi: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert ROI from server format to client format.
    
    Server format uses:
    - idx -> roi_id
    - type (int) -> roi_type_name (string)
    - coords -> coordinates
    - device_location -> device_id
    - feature_method -> detection_method
    - expected_text (for text/OCR ROIs)
    
    Args:
        server_roi: ROI in server format
        
    Returns:
        ROI in client format
    """
    roi_type_map = {
        1: "barcode",
        2: "compare",
        3: "ocr",
        4: "color"
    }
    
    roi_type = server_roi.get('type', 2)
    roi_type_name = roi_type_map.get(roi_type, "compare")
    
    client_roi = {
        "roi_id": int(server_roi.get('idx', 0)),
        "roi_type_name": roi_type_name,
        "device_id": int(server_roi.get('device_location', 1)),
        "coordinates": server_roi.get('coords', [0, 0, 0, 0]),
        "ai_threshold": float(server_roi.get('ai_threshold') or 0.8),
        "focus": int(server_roi.get('focus', 305)),
        "exposure": int(server_roi.get('exposure', 1200)),
        "detection_method": str(server_roi.get('feature_method', 'opencv')),  # Use detection_method (not model)
        "rotation": int(server_roi.get('rotation', 0)),
        "is_device_barcode": server_roi.get('is_device_barcode', True) if server_roi.get('is_device_barcode') is not None else True,
        "enabled": True,
        "notes": ""
    }
    
    # Add expected_text for text-type and OCR ROIs
    if 'expected_text' in server_roi and server_roi['expected_text']:
        client_roi['expected_text'] = server_roi['expected_text']
    
    # Add color-specific parameters for color ROI type (v3.2 schema)
    if roi_type_name == 'color':
        # Server v3.2 uses 'color_config' dict at field 11
        color_config = server_roi.get('color_config', {})
        
        if color_config:
            # Support simple format (v3.2)
            if 'expected_color' in color_config:
                client_roi['expected_color'] = color_config['expected_color']  # RGB array [r, g, b]
            if 'color_tolerance' in color_config:
                client_roi['color_tolerance'] = int(color_config['color_tolerance'])
            if 'min_pixel_percentage' in color_config:
                client_roi['min_pixel_percentage'] = float(color_config['min_pixel_percentage'])
            
            # Support legacy format (v3.1) - store full color_ranges if present
            if 'color_ranges' in color_config:
                client_roi['color_ranges'] = color_config['color_ranges']
    
    return client_roi


def roi_to_server_format(client_roi: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert ROI from client format to server format.
    
    Client format uses:
    - roi_id -> idx
    - roi_type_name (string) -> type (int)
    - coordinates -> coords
    - device_id -> device_location
    - detection_method -> feature_method
    - expected_text (for text/OCR ROIs)
    
    Args:
        client_roi: ROI in client format
        
    Returns:
        ROI in server format
    """
    roi_type_map = {
        "barcode": 1,
        "compare": 2,
        "ocr": 3,
        "color": 4
    }
    
    roi_type_name = client_roi.get('roi_type_name', 'compare')
    roi_type = roi_type_map.get(roi_type_name, 2)
    
    # Support both 'detection_method' (new) and 'model' (legacy) field names
    detection_method = client_roi.get('detection_method') or client_roi.get('model', 'opencv')
    
    server_roi = {
        "idx": int(client_roi.get('roi_id', 0)),
        "type": roi_type,
        "coords": client_roi.get('coordinates', [0, 0, 0, 0]),
        "focus": int(client_roi.get('focus', 305)),
        "exposure": int(client_roi.get('exposure', 1200)),
        "ai_threshold": float(client_roi['ai_threshold']) if client_roi.get('ai_threshold') is not None else None,
        "feature_method": str(detection_method),
        "rotation": int(client_roi.get('rotation', 0)),
        "device_location": int(client_roi.get('device_id', 1)),
        "expected_text": client_roi.get('expected_text', None),
        "is_device_barcode": client_roi.get('is_device_barcode', None)
    }
    
    # Add color-specific parameters for color ROI type (v3.2 schema)
    # Server v3.2 expects 'color_config' dict at field 11
    if roi_type_name == 'color':
        color_config = {}
        
        # Simple format (v3.2) - preferred
        if 'expected_color' in client_roi:
            color_config['expected_color'] = client_roi['expected_color']  # RGB array [r, g, b]
        if 'color_tolerance' in client_roi:
            color_config['color_tolerance'] = int(client_roi['color_tolerance'])
        if 'min_pixel_percentage' in client_roi:
            color_config['min_pixel_percentage'] = float(client_roi['min_pixel_percentage'])
        
        # Legacy format (v3.1) - if color_ranges provided directly
        if 'color_ranges' in client_roi:
            color_config['color_ranges'] = client_roi['color_ranges']
        
        # Only add color_config if not empty
        if color_config:
            server_roi['color_config'] = color_config
    
    return server_roi


def normalize_roi(roi_data: Any, product_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Normalize ROI data from various formats to unified client format.
    
    Supports:
    - Server format: {idx, type, coords, device_location, feature_method, ...}
    - Legacy array format: [roi_id, device_id, coords, focus, exposure, threshold, model, rotation, roi_type, ...]
    - Client dict format: {roi_id, roi_type_name, device_id, coordinates, ...}
    
    Returns standardized ROI dict with all required and optional fields.
    
    Client Format Fields:
    - roi_id (int): Unique ROI identifier
    - roi_type_name (str): Type name (barcode, compare, ocr, text)
    - device_id (int): Device number (1-4)
    - coordinates (list): Bounding box [x1, y1, x2, y2]
    - ai_threshold (float): AI similarity threshold (0.0-1.0)
    - focus (int): Camera focus value (0-1000)
    - exposure (int): Camera exposure time in microseconds
    - detection_method (str): AI detection method (mobilenet, opencv, histogram, structural)
    - rotation (int): Image rotation angle (0, 90, 180, 270)
    - is_device_barcode (bool): Whether barcode is device identifier
    - enabled (bool): Whether ROI is active
    - notes (str): Optional notes/description
    - expected_text (str, optional): Expected text for text-type/OCR ROIs
    
    Args:
        roi_data: ROI data in any supported format
        product_name: Optional product name for logging
        
    Returns:
        Normalized ROI dictionary in client format
        
    Raises:
        ValueError: If ROI data is invalid or missing required fields
    """
    roi_type_map = {
        1: "barcode",
        2: "compare",
        3: "ocr",
        4: "color",
        "1": "barcode",
        "2": "compare",
        "3": "ocr",
        "4": "color"
    }
    
    # Handle legacy array format
    if isinstance(roi_data, (list, tuple)):
        if len(roi_data) < 9:
            raise ValueError(f"Legacy ROI array must have at least 9 elements, got {len(roi_data)}")
        
        roi_type_num = roi_data[8]
        roi_type_name = roi_type_map.get(roi_type_num, "compare")
        
        normalized = {
            "roi_id": int(roi_data[0]),
            "roi_type_name": roi_type_name,
            "device_id": int(roi_data[1]),
            "coordinates": list(roi_data[2]) if isinstance(roi_data[2], (list, tuple)) else roi_data[2],
            "ai_threshold": float(roi_data[5]) if roi_data[5] is not None else 0.8,
            "focus": int(roi_data[3]),
            "exposure": int(roi_data[4]),
            "detection_method": str(roi_data[6]) if len(roi_data) > 6 and roi_data[6] else "opencv",
            "rotation": int(roi_data[7]) if len(roi_data) > 7 else 0,
            "is_device_barcode": bool(roi_data[10]) if len(roi_data) > 10 and roi_data[10] is not None else True,
            "enabled": True,
            "notes": f"Legacy: Model={roi_data[6]}, Rotation={roi_data[7]}" if len(roi_data) > 7 else ""
        }
        
        logger.debug(f"Normalized legacy array ROI {normalized['roi_id']} to client format")
        return normalized
    
    # Handle dict format
    elif isinstance(roi_data, dict):
        # Detect format: server format has 'idx', 'coords', 'device_location'
        is_server_format = 'idx' in roi_data or 'coords' in roi_data or 'device_location' in roi_data
        
        if is_server_format:
            # Convert from server format
            normalized = roi_from_server_format(roi_data)
            logger.debug(f"Normalized server format ROI {normalized['roi_id']} to client format")
            return normalized
        
        # Client format - normalize field names
        roi_type = (
            roi_data.get('roi_type_name') or 
            roi_data.get('roi_type') or 
            roi_data.get('type')
        )
        
        # Convert numeric roi_type to string if needed
        if isinstance(roi_type, (int, str)):
            roi_type = roi_type_map.get(roi_type, roi_type)
        
        if not roi_type:
            roi_type = 'compare'
        
        # Handle various field name variations
        roi_id = roi_data.get('roi_id') or roi_data.get('id', 0)
        device_id = roi_data.get('device_id') or roi_data.get('device', 1)
        coordinates = roi_data.get('coordinates') or roi_data.get('coords', [0, 0, 0, 0])
        # Support detection_method (new), model (legacy), or feature_method (server)
        detection_method = roi_data.get('detection_method') or roi_data.get('model') or roi_data.get('feature_method', 'opencv')
        
        normalized = {
            "roi_id": int(roi_id),
            "roi_type_name": str(roi_type),
            "device_id": int(device_id),
            "coordinates": coordinates,
            "ai_threshold": float(roi_data.get('ai_threshold') or 0.8),
            "focus": int(roi_data.get('focus', 305)),
            "exposure": int(roi_data.get('exposure', 1200)),
            "detection_method": str(detection_method),
            "rotation": int(roi_data.get('rotation', 0)),
            "is_device_barcode": roi_data.get('is_device_barcode', True) if roi_data.get('is_device_barcode') is not None else True,
            "enabled": bool(roi_data.get('enabled', True)),
            "notes": str(roi_data.get('notes', ''))
        }
        
        # Add optional expected_text for text/OCR ROIs
        if 'expected_text' in roi_data and roi_data['expected_text']:
            normalized['expected_text'] = str(roi_data['expected_text'])
        
        logger.debug(f"Normalized client dict ROI {normalized['roi_id']} with type {normalized['roi_type_name']}")
        return normalized
    
    else:
        raise ValueError(f"Unsupported ROI data type: {type(roi_data)}")


def validate_roi(roi: Dict[str, Any], format_type: str = 'client') -> tuple[bool, List[str]]:
    """
    Validate ROI data against schema requirements.
    
    Supports validation for both client and server formats.
    
    Checks:
    - Required fields present
    - Field types correct
    - Value ranges valid
    - Coordinates format valid
    
    Args:
        roi: ROI dictionary in client or server format
        format_type: 'client' or 'server' format
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if format_type == 'server':
        # Server format validation
        required_fields = ['idx', 'type', 'coords', 'focus', 'exposure', 'device_location']
        
        for field in required_fields:
            if field not in roi:
                errors.append(f"Missing required field: {field}")
        
        # Type validation for server format
        if 'idx' in roi and not isinstance(roi['idx'], int):
            errors.append(f"idx must be int, got {type(roi['idx']).__name__}")
        
        if 'type' in roi:
            if not isinstance(roi['type'], int):
                errors.append(f"type must be int, got {type(roi['type']).__name__}")
            elif roi['type'] not in [1, 2, 3, 4]:
                errors.append(f"type must be 1-4 (1=barcode, 2=compare, 3=ocr, 4=text), got {roi['type']}")
        
        if 'device_location' in roi:
            if not isinstance(roi['device_location'], int):
                errors.append(f"device_location must be int, got {type(roi['device_location']).__name__}")
            elif roi['device_location'] < 1 or roi['device_location'] > 4:
                errors.append(f"device_location must be 1-4, got {roi['device_location']}")
        
        if 'coords' in roi:
            coords = roi['coords']
            if not isinstance(coords, (list, tuple)) or len(coords) != 4:
                errors.append(f"coords must be list/tuple of 4 elements [x1,y1,x2,y2], got {coords}")
            else:
                try:
                    x1, y1, x2, y2 = [int(c) for c in coords]
                    if x1 >= x2 or y1 >= y2:
                        errors.append(f"Invalid coords: x1 < x2 and y1 < y2 required, got [{x1},{y1},{x2},{y2}]")
                except (ValueError, TypeError) as e:
                    errors.append(f"coords must be numeric: {e}")
        
        # ai_threshold can be null or float in server format
        if 'ai_threshold' in roi and roi['ai_threshold'] is not None:
            try:
                threshold = float(roi['ai_threshold'])
                if threshold < 0.0 or threshold > 1.0:
                    errors.append(f"ai_threshold must be 0.0-1.0 or null, got {threshold}")
            except (ValueError, TypeError):
                errors.append(f"ai_threshold must be numeric or null, got {type(roi['ai_threshold']).__name__}")
    
    else:
        # Client format validation
        required_fields = ['roi_id', 'roi_type_name', 'device_id', 'coordinates']
        
        for field in required_fields:
            if field not in roi:
                errors.append(f"Missing required field: {field}")
        
        # Type validation for client format
        if 'roi_id' in roi and not isinstance(roi['roi_id'], int):
            errors.append(f"roi_id must be int, got {type(roi['roi_id']).__name__}")
        
        if 'device_id' in roi:
            if not isinstance(roi['device_id'], int):
                errors.append(f"device_id must be int, got {type(roi['device_id']).__name__}")
            elif roi['device_id'] < 1 or roi['device_id'] > 4:
                errors.append(f"device_id must be 1-4, got {roi['device_id']}")
        
        if 'roi_type_name' in roi:
            valid_types = ['barcode', 'compare', 'ocr', 'color']
            if roi['roi_type_name'] not in valid_types:
                errors.append(f"roi_type_name must be one of {valid_types}, got '{roi['roi_type_name']}'")
        
        if 'coordinates' in roi:
            coords = roi['coordinates']
            if not isinstance(coords, (list, tuple)) or len(coords) != 4:
                errors.append(f"coordinates must be list/tuple of 4 elements [x1,y1,x2,y2], got {coords}")
            else:
                try:
                    x1, y1, x2, y2 = [int(c) for c in coords]
                    if x1 >= x2 or y1 >= y2:
                        errors.append(f"Invalid coordinates: x1 < x2 and y1 < y2 required, got [{x1},{y1},{x2},{y2}]")
                except (ValueError, TypeError) as e:
                    errors.append(f"Coordinates must be numeric: {e}")
        
        if 'ai_threshold' in roi and roi['ai_threshold'] is not None:
            threshold = roi['ai_threshold']
            try:
                threshold = float(threshold)
                if threshold < 0.0 or threshold > 1.0:
                    errors.append(f"ai_threshold must be 0.0-1.0 or None, got {threshold}")
            except (ValueError, TypeError):
                errors.append(f"ai_threshold must be numeric or None, got {type(threshold).__name__}")
    
    # Common validation for both formats
    if 'focus' in roi:
        focus = roi['focus']
        if not isinstance(focus, int) or focus < 0 or focus > 1000:
            errors.append(f"focus must be int 0-1000, got {focus}")
    
    if 'exposure' in roi:
        exposure = roi['exposure']
        if not isinstance(exposure, int) or exposure < 0 or exposure > 10000:
            errors.append(f"exposure must be int 0-10000, got {exposure}")
    
    return len(errors) == 0, errors


def normalize_roi_list(rois: List[Any], product_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Normalize a list of ROIs from various formats.
    
    Args:
        rois: List of ROI data in any supported format
        product_name: Optional product name for logging
        
    Returns:
        List of normalized ROI dictionaries
        
    Raises:
        ValueError: If any ROI is invalid
    """
    normalized_rois = []
    errors = []
    
    for i, roi_data in enumerate(rois):
        try:
            normalized = normalize_roi(roi_data, product_name)
            is_valid, validation_errors = validate_roi(normalized)
            
            if not is_valid:
                error_msg = f"ROI {i} validation failed: {', '.join(validation_errors)}"
                errors.append(error_msg)
                logger.warning(error_msg)
            
            normalized_rois.append(normalized)
            
        except Exception as e:
            error_msg = f"Failed to normalize ROI {i}: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
    
    if errors:
        logger.warning(f"ROI normalization completed with {len(errors)} errors")
    else:
        logger.info(f"Successfully normalized {len(normalized_rois)} ROIs")
    
    return normalized_rois


def send_grouped_inspection(
    product_name: str,
    captured_images: Dict[str, Any],
    capture_time: float,
    device_barcodes: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Send inspection request to server with image file paths.
    
    captured_images format:
    {
        "305,1200": {
            "focus": 305,
            "exposure": 1200,
            "rois": [...],
            "image_path": "/mnt/visual-aoi-shared/sessions/{session_id}/captures/group_305_1200.jpg",
            "image_width": 7716,
            "image_height": 5360
        }
    }
    """
    payload: Dict[str, Any] = {
        "session_id": state.session_id,
        "product": product_name,
        "captured_images": captured_images,
        "capture_time": capture_time,
    }
    if device_barcodes:
        payload["device_barcodes"] = device_barcodes

    # Log payload summary (without full image data)
    logger.info(f"Sending inspection request: {len(captured_images)} image paths")
    for group_key, group_data in captured_images.items():
        logger.info(f"  Group {group_key}: {group_data.get('image_path')}")

    try:
        # Increased timeout to 180 seconds (3 minutes) for PyTorch/EasyOCR processing
        # PyTorch model initialization and EasyOCR can take longer than the previous 60s timeout
        response = call_server("POST", "/process_grouped_inspection", json=payload, timeout=180)
        result = response.json()
        result.setdefault("source", "server")
        logger.info(f"✓ Inspection completed successfully for product '{product_name}'")
        return result
    except Exception as exc:
        error_msg = f"Inspection failed for product '{product_name}': {exc}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from exc


def perform_grouped_capture(product_name: str, roi_groups: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capture images for all ROI groups and save to shared folder.
    
    Returns dict with captured_images containing image paths instead of base64 data.
    """
    ensure_camera_initialized()
    ensure_session()  # Ensure we have a session ID for folder structure

    captured_images: Dict[str, Any] = {}
    capture_start = time.time()
    is_first_group = True

    for index, (group_key, group_info) in enumerate(roi_groups.items(), start=1):
        focus = int(getattr(group_info, "focus", None) or group_key.split(",")[0])
        exposure = int(getattr(group_info, "exposure", None) or group_key.split(",")[1])
        rois = getattr(group_info, "rois", [])

        app.logger.info("Capturing group %s/%s (focus=%s, exposure=%s)", index, len(roi_groups), focus, exposure)
        
        # For first group, use fast capture since camera is already initialized with these settings
        if is_first_group:
            app.logger.info("First group: using fast capture (camera already at these settings)")
            image = tis_camera.capture_image_fast()
            is_first_group = False
        else:
            # For subsequent groups, apply new settings and capture
            image = tis_camera.capture_image(focus=focus, exposure_time=exposure)
        
        if image is None:
            raise RuntimeError(f"Failed to capture image for group {group_key}")

        # Save image to shared folder instead of encoding to base64
        image_path = save_captured_image(image, group_key, state.session_id)

        captured_images[group_key] = {
            "focus": focus,
            "exposure": exposure,
            "rois": rois,
            "image_path": image_path,  # Store file path instead of base64
            "image_width": image.shape[1],
            "image_height": image.shape[0],
        }

    capture_time = time.time() - capture_start
    app.logger.info("✓ Captured and saved %s groups in %.2fs", len(captured_images), capture_time)

    return {
        "captured_images": captured_images,
        "capture_time": capture_time,
    }


@app.teardown_appcontext
def teardown_db(exception=None):
    """Clean up resources when request context ends."""
    if exception:
        logger.error(f"Request ended with exception: {exception}")
        # Note: We don't close sessions on every request, only on app shutdown
        # Sessions should be explicitly closed by the client or on disconnect


@app.route('/')
def index():
    return render_template('professional_index.html')


@app.route('/roi-editor')
def roi_editor():
    """ROI Configuration Editor page."""
    return render_template('roi_editor.html')


@app.route('/sw.js')
def service_worker():
    """Serve the service worker file from root path for proper scope."""
    response = send_from_directory('static', 'sw.js')
    # Service workers must have correct MIME type
    response.headers['Content-Type'] = 'application/javascript'
    # Disable caching for service worker to ensure updates
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/api/health", methods=["GET"])
def health_check():
    payload: Dict[str, Any] = {
        "application": "visual-aoi-web-client",
        "connected": state.connected,
    }

    if not state.connected:
        payload["server"] = {"status": "disconnected"}
        return jsonify(payload), 200

    try:
        response = call_server("GET", "/api/health", timeout=5)
        payload["server"] = {"status": "connected", "details": response.json()}
        return jsonify(payload), 200
    except Exception as exc:  # noqa: BLE001
        payload["server"] = {"status": "error", "error": str(exc)}
        return jsonify(payload), 503


@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify(
        {
            "connected": state.connected,
            "server_url": state.server_url,
            "session_id": state.session_id,
            "session_product": state.session_product,
            "products": state.products_cache,
            "last_result": state.last_result,
        }
    )


@app.route("/api/server/connect", methods=["POST"])
def connect_server():
    """Connect to AOI server with comprehensive initialization."""
    data = request.get_json(silent=True) or {}
    server_url = data.get("server_url") or data.get("serverUrl")
    if not server_url:
        return jsonify({"error": "server_url is required"}), 400

    state.server_url = server_url.rstrip("/")
    
    try:
        # Test connection
        health = call_server("GET", "/api/health", timeout=5).json()
        logger.info(f"Connected to server: {health}")
        
        # Initialize server with AI models
        try:
            init_payload = call_server("POST", "/api/initialize", timeout=30).json()
            logger.info(f"Server initialization: {init_payload}")
        except Exception as init_exc:
            logger.warning(f"Server initialization failed: {init_exc}")
            init_payload = {"warning": "Server initialization failed"}
        
        # Load available products
        state.products_cache = fetch_products_from_server()
        
        # Reset state for new connection
        state.connected = True
        state.session_id = None
        state.session_product = None
        state.last_result = None
        state.roi_groups_cache.clear()
        state.first_roi_group_settings = None
        state.device_barcodes.clear()

        return jsonify({
            "status": "connected",
            "health": health,
            "init": init_payload,
            "products": state.products_cache,
        }), 200
        
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to connect to server: {exc}")
        state.connected = False
        state.products_cache = []
        state.session_id = None
        state.session_product = None
        return jsonify({"error": str(exc)}), 502


@app.route("/api/server/disconnect", methods=["POST"])
def disconnect_server():
    close_active_session(silent=True)
    state.connected = False
    state.products_cache = []
    state.last_result = None
    return jsonify({"status": "disconnected"}), 200


@app.route("/api/products", methods=["GET"])
def get_products():
    """Get list of available products from server."""
    if not state.connected:
        return jsonify({"error": "Not connected to server"}), 503

    try:
        if not state.products_cache:
            state.products_cache = fetch_products_from_server()

        return jsonify({"products": state.products_cache, "source": "server"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch products: {str(e)}"}), 500


@app.route("/api/session", methods=["POST"])
def create_session():
    """Create inspection session (NEW FLOW: Camera must already be initialized).
    
    New initialization flow:
    1. Connect to server
    2. Select/create product
    3. Initialize camera with product settings
    4. Create session (this endpoint)
    """
    data = request.get_json(silent=True) or {}
    product_name = data.get("product")
    if not product_name:
        return jsonify({"error": "product is required"}), 400

    try:
        ensure_connected()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409

    # NEW: Validate camera is initialized before creating session
    if not state.camera_initialized:
        return jsonify({
            "error": "Camera must be initialized before creating session",
            "hint": "Please initialize camera with product settings first"
        }), 409

    # Close existing session if active
    if state.session_id:
        close_active_session(silent=True)

    payload = {
        "product_name": product_name,
        "client_info": {
            "client_id": "visual_aoi_web_client",
            "version": "2.0.0",
            "transport": "http",
            "location": "local"
        },
    }

    try:
        # Create session with server
        response = call_server("POST", "/api/session/create", json=payload, timeout=10)
        session_payload = response.json()
        state.session_id = session_payload.get("session_id")
        state.session_product = product_name
        
        logger.info(f"Created session {state.session_id} for product {product_name}")
        
        # Load ROI groups for inspection (camera already initialized with these settings)
        try:
            roi_groups = fetch_roi_groups(product_name)
            # Create ROIGroup objects with safe parameter extraction
            state.roi_groups_cache = {}
            for k, v in roi_groups.items():
                if isinstance(v, dict) and 'focus' in v and 'exposure' in v and 'rois' in v:
                    # Only pass the expected parameters
                    state.roi_groups_cache[k] = ROIGroup(
                        focus=v['focus'],
                        exposure=v['exposure'],
                        rois=v['rois']
                    )
                else:
                    logger.warning(f"Skipping invalid ROI group {k}: {v}")
            
            # Analyze which devices need manual barcode input (devices without main barcode ROI)
            devices_need_barcode = analyze_devices_needing_barcodes(roi_groups)
            
            logger.info(f"Session created with {len(state.roi_groups_cache)} ROI groups (camera already initialized)")
            
        except Exception as roi_exc:
            logger.warning(f"Failed to load ROI groups for product {product_name}: {roi_exc}")
            devices_need_barcode = []
        
        return jsonify({
            "session_id": state.session_id, 
            "product": product_name,
            "roi_groups_count": len(state.roi_groups_cache),
            "devices_need_barcode": devices_need_barcode,
            "camera_initialized": True
        }), 200
        
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Create session failed: {exc}")
        state.session_id = None
        state.session_product = None
        return jsonify({"error": str(exc)}), 502


@app.route("/api/session", methods=["DELETE"])
def close_session():
    """Close the current inspection session."""
    if not state.session_id:
        logger.info("No active session to close")
        return jsonify({"status": "no-session"}), 200

    session_to_close = state.session_id
    try:
        close_active_session(silent=False)
        logger.info(f"✓ Session {session_to_close} closed successfully via API")
        return jsonify({"status": "closed", "session_id": session_to_close}), 200
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to close session {session_to_close}: {exc}")
        return jsonify({"error": str(exc)}), 502


@app.route("/api/cameras", methods=["GET"])
def get_cameras():
    cameras = tis_camera.list_available_cameras()
    formatted = [
        {
            "name": camera_info.get("display_name") or camera_info.get("model") or "TIS Camera",
            "serial": camera_info.get("serial"),
            "type": camera_info.get("type", "tis"),
        }
        for camera_info in cameras
    ]

    if not formatted:
        app.logger.warning("No TIS cameras detected")

    return jsonify(formatted), 200


@app.route("/api/camera/status", methods=["GET"])
def get_camera_status():
    """Get current camera and pipeline status."""
    try:
        status = tis_camera.get_camera_status()
        
        # Add application-level status
        status['app_initialized'] = state.camera_initialized
        status['app_serial'] = state.camera_serial
        
        return jsonify(status), 200
    except Exception as exc:
        logger.error(f"Failed to get camera status: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/camera/reset", methods=["POST"])
def reset_camera():
    """Reset camera pipeline - stop existing pipeline and prepare for reinitialization."""
    try:
        logger.info("Resetting camera pipeline...")
        
        success = tis_camera.reset_camera_pipeline()
        
        if success:
            # Clear application state
            state.camera_initialized = False
            state.camera_serial = None
            state.live_view_active = False
            
            logger.info("✓ Camera pipeline reset successfully")
            return jsonify({
                "status": "reset",
                "message": "Camera pipeline reset successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to reset camera pipeline"}), 500
            
    except Exception as exc:
        logger.error(f"Camera reset failed: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/camera/initialize", methods=["POST"])
def init_camera():
    """Initialize camera with product-specific settings or defaults.
    
    Professional initialization flow:
    1. Check existing camera status
    2. Reset pipeline if already initialized (webpage refresh handling)
    3. Initialize camera with product-specific settings
    4. Verify pipeline state
    
    New flow: Camera initialization happens AFTER product selection.
    - If product_name provided: Use first ROI group's focus/exposure
    - If no product_name (new product): Use default camera settings
    """
    data = request.get_json(silent=True) or {}
    serial = data.get("serial")
    product_name = data.get("product_name")  # Optional: for product-specific initialization
    force_reset = data.get("force_reset", True)  # Default to True for webpage refresh
    
    if not serial:
        return jsonify({"error": "serial is required"}), 400

    try:
        # Step 1: Check existing camera status
        logger.info("=" * 70)
        logger.info("CAMERA INITIALIZATION REQUEST")
        logger.info(f"  Serial: {serial}")
        logger.info(f"  Product: {product_name or 'None (default settings)'}")
        logger.info(f"  Force Reset: {force_reset}")
        
        current_status = tis_camera.get_camera_status()
        logger.info(f"  Current Status: {current_status}")
        
        # Step 2: Handle existing pipeline
        pipeline_state = current_status.get('pipeline_state', 'NONE')
        
        if pipeline_state == 'PLAYING':
            # Pipeline is already running perfectly - reuse it!
            logger.info("✓ Camera pipeline already PLAYING - reusing existing pipeline")
            state.camera_serial = serial
            state.camera_initialized = True
            
            # Just apply new settings if product provided
            if product_name:
                logger.info(f"Applying settings for product: {product_name}")
                try:
                    roi_groups = fetch_roi_groups(product_name)
                    if roi_groups:
                        first_group_key = next(iter(roi_groups.keys()))
                        focus, exposure = first_group_key.split(',')
                        focus, exposure = int(focus), int(exposure)
                        
                        logger.info(f"Applying product-specific settings: focus={focus}, exposure={exposure}")
                        tis_camera.set_camera_properties(focus=focus, exposure_time=exposure, skip_settle_delay=False)
                        
                        return jsonify({
                            "status": "reused_playing_pipeline",
                            "serial": serial,
                            "product": product_name,
                            "settings": {"focus": focus, "exposure": exposure},
                            "pipeline_state": "PLAYING"
                        }), 200
                except Exception as e:
                    logger.warning(f"Failed to apply product settings: {e}")
            
            # No product - just confirm existing pipeline
            return jsonify({
                "status": "reused_playing_pipeline",
                "serial": serial,
                "pipeline_state": "PLAYING"
            }), 200
            
        elif current_status['initialized'] or current_status['pipeline_active']:
            # Pipeline exists but not PLAYING - try restart first, then reset
            logger.info(f"⚠ Camera pipeline in {pipeline_state} state - attempting restart")
            
            # Try restart first (stop + start) - more reliable for active pipelines
            restart_success = tis_camera.restart_camera_pipeline()
            if restart_success:
                logger.info("✓ Pipeline restarted successfully")
                state.camera_serial = serial
                state.camera_initialized = True
                
                # Apply product settings if provided
                if product_name:
                    logger.info(f"Applying settings for product: {product_name}")
                    try:
                        roi_groups = fetch_roi_groups(product_name)
                        if roi_groups:
                            first_group_key = next(iter(roi_groups.keys()))
                            focus, exposure = first_group_key.split(',')
                            focus, exposure = int(focus), int(exposure)
                            
                            logger.info(f"Applying product-specific settings: focus={focus}, exposure={exposure}")
                            tis_camera.set_camera_properties(focus=focus, exposure_time=exposure, skip_settle_delay=False)
                            
                            return jsonify({
                                "status": "restarted_pipeline",
                                "serial": serial,
                                "product": product_name,
                                "settings": {"focus": focus, "exposure": exposure},
                                "pipeline_state": "PLAYING"
                            }), 200
                    except Exception as e:
                        logger.warning(f"Failed to apply product settings: {e}")
                
                return jsonify({
                    "status": "restarted_pipeline",
                    "serial": serial,
                    "pipeline_state": "PLAYING"
                }), 200
            else:
                # Restart failed - try full reset
                logger.warning("⚠ Pipeline restart failed, attempting full reset...")
                reset_success = tis_camera.reset_camera_pipeline()
                if not reset_success:
                    logger.warning("Pipeline reset also failed, attempting initialization anyway...")
                else:
                    logger.info("✓ Pipeline reset successful")
                    import time
                    time.sleep(0.5)  # Brief pause after reset
        
        # Step 3: Initialize camera hardware
        logger.info("Initializing camera hardware...")
        initialized = tis_camera.initialize_camera(serial=serial)
        if not initialized:
            state.camera_initialized = False
            logger.error("❌ Camera initialization failed")
            return jsonify({"error": "Failed to initialize camera"}), 500
        
        logger.info("✓ Camera hardware initialized")
        state.camera_serial = serial
        state.camera_initialized = True
        
        # Apply product-specific settings if product provided
        if product_name:
            logger.info(f"Initializing camera with settings for product: {product_name}")
            try:
                # Load ROI groups for the product
                roi_groups = fetch_roi_groups(product_name)
                if roi_groups:
                    # Apply first ROI group settings
                    first_group_key = next(iter(roi_groups.keys()))
                    first_group = roi_groups[first_group_key]
                    focus, exposure = first_group_key.split(',')
                    focus, exposure = int(focus), int(exposure)
                    
                    logger.info(f"Applying product-specific camera settings: focus={focus}, exposure={exposure}")
                    
                    # Store settings for later use
                    state.first_roi_group_settings = {
                        'focus': focus,
                        'exposure': exposure,
                        'group_key': first_group_key
                    }
                    
                    # Apply camera settings
                    success = tis_camera.set_camera_properties(
                        focus=focus, 
                        exposure_time=exposure, 
                        skip_settle_delay=False
                    )
                    
                    if success:
                        logger.info(f"✓ Camera initialized with product settings (F:{focus}, E:{exposure})")
                        return jsonify({
                            "status": "initialized",
                            "serial": serial,
                            "product": product_name,
                            "settings": {"focus": focus, "exposure": exposure}
                        }), 200
                    else:
                        logger.warning("Camera settings applied but some properties may have failed")
                        return jsonify({
                            "status": "initialized",
                            "serial": serial,
                            "product": product_name,
                            "warning": "Some camera properties failed to apply"
                        }), 200
                else:
                    logger.warning(f"No ROI groups found for product {product_name}, using default settings")
            except Exception as product_exc:
                logger.warning(f"Failed to apply product-specific settings: {product_exc}")
                # Continue with default initialization
        
        # Step 4: Default initialization (no product or product settings failed)
        logger.info("Camera initialized with default settings")
        
        # Step 5: Verify final pipeline state
        final_status = tis_camera.get_camera_status()
        logger.info(f"Final Status: {final_status}")
        logger.info("=" * 70)
        
        return jsonify({
            "status": "initialized",
            "serial": serial,
            "settings": "default",
            "pipeline_state": final_status.get('pipeline_state', 'UNKNOWN')
        }), 200
        
    except Exception as exc:
        logger.error(f"❌ Camera initialization failed: {exc}")
        logger.error("=" * 70)
        state.camera_initialized = False
        return jsonify({"error": str(exc)}), 500


@app.route("/api/camera/start-live", methods=["POST"])
def start_live_view():
    """Start live camera view."""
    try:
        ensure_camera_initialized()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409

    try:
        # Start live view - this would start the camera streaming
        # The TIS camera module should handle live view activation
        success = tis_camera.start_live_view()
        if success:
            state.live_view_active = True
            return jsonify({"status": "live_view_started"}), 200
        else:
            return jsonify({"error": "Failed to start live view"}), 500
    except Exception as exc:
        logger.error(f"Start live view failed: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/camera/stop-live", methods=["POST"])
def stop_live_view():
    """Stop live camera view."""
    try:
        # Stop live view
        success = tis_camera.stop_live_view()
        state.live_view_active = False
        return jsonify({"status": "live_view_stopped"}), 200
    except Exception as exc:
        logger.error(f"Stop live view failed: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/camera/live-image", methods=["GET"])
def get_live_image():
    """Get current live image from camera."""
    try:
        ensure_camera_initialized()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409

    try:
        # Capture current frame
        frame = tis_camera.capture_tis_image_fast()
        if frame is None:
            frame = tis_camera.capture_tis_image()

        if frame is None:
            return jsonify({"error": "No frame available"}), 404

        # Convert to JPEG
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            return jsonify({"error": "Failed to encode frame"}), 500

        return Response(buffer.tobytes(), mimetype="image/jpeg")
    except Exception as exc:
        logger.error(f"Get live image failed: {exc}")
        return jsonify({"error": str(exc)}), 500


def gen_frames():
    while True:
        tis_instance = tis_camera.get_camera_instance()
        if tis_instance is None:
            time.sleep(0.5)
            continue

        frame = tis_camera.capture_tis_image_fast()
        if frame is None:
            frame = tis_camera.capture_tis_image()

        if frame is None:
            time.sleep(0.2)
            continue

        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            time.sleep(0.1)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@app.route("/api/camera/feed", methods=["GET"])
def camera_feed():
    try:
        ensure_camera_initialized()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409

    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/device/barcodes", methods=["GET"])
def get_device_barcodes():
    """Get current device barcodes."""
    return jsonify({
        "device_barcodes": [{
            "device_id": entry.device_id,
            "barcode": entry.barcode
        } for entry in state.device_barcodes]
    }), 200


@app.route("/api/device/barcodes", methods=["POST"])
def set_device_barcodes():
    """Set device barcodes for inspection."""
    data = request.get_json(silent=True) or {}
    device_barcodes = data.get("device_barcodes", [])
    
    state.device_barcodes.clear()
    for entry in device_barcodes:
        if "device_id" in entry and "barcode" in entry:
            state.device_barcodes.append(
                DeviceBarcodeEntry(entry["device_id"], entry["barcode"])
            )
    
    return jsonify({
        "status": "updated",
        "count": len(state.device_barcodes)
    }), 200


@app.route("/api/device/barcodes", methods=["DELETE"])
def clear_device_barcodes():
    """Clear all device barcodes."""
    state.device_barcodes.clear()
    return jsonify({"status": "cleared"}), 200


@app.route("/api/inspect", methods=["POST"])
def inspect():
    """Perform comprehensive grouped inspection with optimized camera workflow."""
    try:
        ensure_session()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409

    try:
        ensure_camera_initialized()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409

    data = request.get_json(silent=True) or {}
    product_name = data.get("product") or state.session_product
    
    # IMPORTANT: Always use device_barcodes from request (even if empty array)
    # Only fall back to cached state if device_barcodes key is NOT present in request
    if "device_barcodes" in data:
        # Client explicitly provided device_barcodes (could be empty array or with values)
        device_barcodes = data.get("device_barcodes")
        logger.info(f"Using device_barcodes from request: {device_barcodes}")
    elif state.device_barcodes:
        # Fallback to cached state only if client didn't provide the key at all
        device_barcodes = [{
            "device_id": entry.device_id,
            "barcode": entry.barcode
        } for entry in state.device_barcodes]
        logger.info(f"Using cached device_barcodes from state: {device_barcodes}")
    else:
        device_barcodes = []
        logger.info("No device_barcodes provided - using empty array")

    try:
        # Get ROI groups (use cached if available)
        roi_groups = state.roi_groups_cache or fetch_roi_groups(product_name)
        if not roi_groups:
            return jsonify({"error": "No ROI groups found for product"}), 400
            
        logger.info(f"Starting grouped inspection for {product_name} with {len(roi_groups)} ROI groups")
        
        # Start timing the entire inspection process
        inspection_start_time = time.time()
        
        # Perform optimized grouped capture
        capture_payload = perform_grouped_capture(product_name, roi_groups)
        
        # Send for inspection processing (includes network + server processing)
        inspection_result = send_grouped_inspection(
            product_name,
            capture_payload["captured_images"],
            capture_payload["capture_time"],
            device_barcodes,
        )

        # Calculate total inspection time from start to finish
        total_inspection_time = time.time() - inspection_start_time
        
        # Processing time = total time minus capture time
        processing_time = total_inspection_time - capture_payload["capture_time"]

        # Add timing and session information
        inspection_result["capture_time"] = capture_payload["capture_time"]
        inspection_result["processing_time"] = processing_time
        inspection_result["total_time"] = total_inspection_time
        inspection_result["session_id"] = state.session_id
        inspection_result["product"] = product_name
        inspection_result["roi_groups_count"] = len(roi_groups)
        inspection_result["timestamp"] = datetime.now().isoformat()
        
        # Generate summary from device_summaries for frontend display
        inspection_result["summary"] = generate_inspection_summary(inspection_result)

        # Auto-populate device barcodes from inspection results if available
        auto_populate_device_barcodes(inspection_result)
        
        # Revert camera to first ROI group settings for next inspection (async)
        # This runs in background so we don't delay the response
        threading.Thread(target=revert_camera_to_first_roi_group, daemon=True).start()
        logger.info("Camera revert started in background thread")
        
        state.last_result = inspection_result
        logger.info(f"Inspection completed successfully for {product_name}")
        
        return jsonify(inspection_result), 200
        
    except Exception as exc:  # noqa: BLE001
        logger.exception("Inspection failed")
        return jsonify({"error": str(exc)}), 500


def initialize_camera_for_product(product_name: str, roi_groups: Dict[str, Any]) -> bool:
    """Initialize camera with optimal settings for product's first ROI group."""
    try:
        if not roi_groups:
            logger.warning("No ROI groups found, using default camera settings")
            return True
            
        # Get first ROI group settings for optimal initialization
        first_group_key = next(iter(roi_groups.keys()))
        first_group = roi_groups[first_group_key]
        focus, exposure = first_group_key.split(',')
        focus, exposure = int(focus), int(exposure)
        
        logger.info(f"Applying first ROI group settings for optimal initialization: focus={focus}, exposure={exposure}")
        
        # Store first ROI group settings for later revert
        state.first_roi_group_settings = {
            'focus': focus,
            'exposure': exposure,
            'group_key': first_group_key
        }
        
        # Apply camera settings immediately to reduce first capture delay
        logger.info(f"Applying first ROI group settings: focus={focus}, exposure={exposure}")
        success = tis_camera.set_camera_properties(focus=focus, exposure_time=exposure, skip_settle_delay=False)
        
        if success:
            logger.info(f"Camera initialized and settled with optimal settings (F:{focus}, E:{exposure})")
        else:
            logger.warning(f"Camera settings applied but some properties may have failed")
        
        return True
        
    except Exception as e:
        logger.error(f"Camera initialization for product failed: {e}")
        return False


def generate_inspection_summary(inspection_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate inspection summary from device_summaries for frontend display."""
    try:
        device_summaries = inspection_result.get('device_summaries', {})
        
        if not device_summaries:
            return {
                "overall_result": "N/A",
                "total_devices": 0,
                "pass_count": 0,
                "fail_count": 0
            }
        
        total_devices = len(device_summaries)
        pass_count = sum(1 for summary in device_summaries.values() if summary.get('device_passed', False))
        fail_count = total_devices - pass_count
        overall_result = "PASS" if pass_count == total_devices else "FAIL"
        
        return {
            "overall_result": overall_result,
            "total_devices": total_devices,
            "pass_count": pass_count,
            "fail_count": fail_count
        }
    except Exception as e:
        logger.error(f"Error generating inspection summary: {e}")
        return {
            "overall_result": "ERROR",
            "total_devices": 0,
            "pass_count": 0,
            "fail_count": 0
        }


def auto_populate_device_barcodes(inspection_result: Dict[str, Any]) -> None:
    """Auto-populate device barcode fields from inspection results."""
    try:
        device_summaries = inspection_result.get('device_summaries', {})
        for device_id_str, summary in device_summaries.items():
            device_id = int(device_id_str)
            barcode = summary.get('barcode', '')
            
            # Only auto-populate if not already set and barcode was detected
            if barcode and barcode != 'N/A':
                # Check if already exists
                existing = next((entry for entry in state.device_barcodes 
                               if entry.device_id == device_id), None)
                if not existing:
                    state.device_barcodes.append(
                        DeviceBarcodeEntry(device_id, barcode)
                    )
                    logger.info(f"Auto-populated device {device_id} barcode: {barcode}")
                    
    except Exception as e:
        logger.error(f"Error auto-populating device barcodes: {e}")


def revert_camera_to_first_roi_group() -> None:
    """Revert camera settings to first ROI group for next inspection.
    This runs asynchronously in background to not block inspection results.
    """
    try:
        if not state.first_roi_group_settings:
            logger.info("No first ROI group settings stored, skipping camera revert")
            return
            
        focus = state.first_roi_group_settings['focus']
        exposure = state.first_roi_group_settings['exposure']
        
        logger.info(f"Reverting camera to first ROI group settings: F:{focus}, E:{exposure}")
        success = tis_camera.set_camera_properties(focus=focus, exposure_time=exposure, skip_settle_delay=False)
        
        if success:
            logger.info(f"Camera successfully reverted to first group settings (ready for next inspection)")
        else:
            logger.warning(f"Camera revert completed but some properties may have failed")
        
    except Exception as e:
        logger.error(f"Camera revert failed: {e}")


# Golden Sample Management Endpoints
@app.route("/api/golden-sample/save", methods=["POST"])
def save_golden_sample():
    """Proxy golden sample save request to the server (avoids CORS)."""
    try:
        data = request.form.to_dict()
        files = request.files
        
        product_name = data.get('product_name')
        roi_id = data.get('roi_id')
        sample_type = data.get('sample_type', 'pass_sample')
        
        if not product_name or not roi_id:
            return jsonify({"error": "product_name and roi_id are required"}), 400
            
        if 'golden_image' not in files:
            return jsonify({"error": "golden_image file is required"}), 400
        
        # Get server URL from config or environment
        server_url = os.environ.get('AOI_SERVER_URL', 'http://10.100.27.156:5000')
        
        # Forward the request to the actual server
        golden_image = files['golden_image']
        
        # Prepare files for forwarding
        files_data = {
            'golden_image': (golden_image.filename, golden_image.stream, golden_image.content_type)
        }
        
        # Prepare form data
        form_data = {
            'product_name': product_name,
            'roi_id': roi_id
        }
        
        logger.info(f"Forwarding golden sample save to server: {server_url}/api/golden-sample/save")
        logger.info(f"Product: {product_name}, ROI: {roi_id}")
        
        # Forward to server
        import requests
        response = requests.post(
            f"{server_url}/api/golden-sample/save",
            data=form_data,
            files=files_data,
            timeout=30
        )
        
        # Return server response
        try:
            result = response.json()
        except:
            # If server doesn't return JSON, create response
            if response.status_code == 200:
                result = {"message": f"Golden sample saved for ROI {roi_id}"}
            else:
                result = {"error": f"Server error: {response.status_code}"}
        
        logger.info(f"Server response: {response.status_code} - {result}")
        return jsonify(result), response.status_code
        
    except Exception as e:
        logger.error(f"Failed to save golden sample: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/golden-sample/<product_name>/<int:roi_id>", methods=["GET"])
def get_golden_samples(product_name: str, roi_id: int):
    """Get golden samples for a specific ROI."""
    try:
        # Try to fetch from server
        if not state.connected:
            return jsonify({"error": "Not connected to server"}), 503
            
        response = call_server(
            "GET", 
            f"/api/products/{product_name}/rois/{roi_id}/golden_samples",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify(data), 200
        else:
            error_msg = f"Server returned {response.status_code}: {response.text}"
            logger.error(f"Failed to get golden samples: {error_msg}")
            return jsonify({"error": error_msg}), response.status_code
        
    except Exception as e:
        logger.error(f"Failed to get golden samples: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/products/create", methods=["POST"])
def create_product():
    """Proxy: Create a new product on the server."""
    try:
        data = request.get_json(silent=True) or {}
        product_name = data.get('product_name', '').strip()
        description = data.get('description', '').strip()
        device_count = data.get('device_count', 1)
        
        if not product_name:
            return jsonify({"error": "product_name is required"}), 400
        
        if device_count < 1 or device_count > 4:
            return jsonify({"error": "device_count must be between 1 and 4"}), 400
        
        server_url = state.server_url
        logger.info(f"Creating product '{product_name}' on server (devices: {device_count})")
        
        # CORRECT: Server API endpoint is /api/products/create (per Swagger docs)
        response = requests.post(
            f"{server_url}/api/products/create",
            json={
                "product_name": product_name,
                "description": description
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"✅ Product '{product_name}' created successfully")
            
            # Clear products cache to force refresh
            state.products_cache = None
            
            return jsonify(result), 200
        else:
            logger.warning(f"Server returned {response.status_code} for product creation")
            logger.warning(f"Response text: {response.text[:200]}")  # Log first 200 chars
            
            # Try to parse JSON error, fallback to text if not JSON
            try:
                error_data = response.json()
                error_msg = error_data.get('error', f'Server error: {response.status_code}')
            except Exception:
                error_msg = f'Server error {response.status_code}: {response.text[:100]}'
            
            return jsonify({"error": error_msg}), response.status_code
        
    except Exception as e:
        logger.error(f"❌ Failed to create product: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/products/<product_name>/config", methods=["GET"])
def get_product_config(product_name: str):
    """Proxy: Get ROI configuration for a product from server."""
    try:
        server_url = state.server_url
        logger.info(f"Fetching config for product '{product_name}' from {server_url}")
        
        # Try server API first
        response = requests.get(
            f"{server_url}/api/products/{product_name}/rois",
            timeout=30
        )
        
        # Handle 404 with "No ROIs found" message as empty config (normal for new products)
        if response.status_code == 404:
            try:
                error_data = response.json()
                if "No ROIs found" in error_data.get('error', ''):
                    logger.info(f"ℹ️  Product '{product_name}' has no ROIs configured yet - returning empty config")
                    return jsonify({
                        "rois": [],
                        "roi_groups": {},
                        "product_name": product_name
                    }), 200
            except:
                pass  # Continue to normal 404 handling
        
        if response.status_code == 200:
            config = response.json()
            server_rois = config.get('rois', [])
            
            # Generate ROI groups from ROIs (group by focus and exposure)
            roi_groups = {}
            for roi in server_rois:
                focus = roi.get('focus', 305)
                exposure = roi.get('exposure', 1200)  # Server uses 'exposure'
                group_key = f"{focus},{exposure}"
                
                if group_key not in roi_groups:
                    roi_groups[group_key] = {
                        'focus': focus,
                        'exposure': exposure,
                        'rois': []
                    }
                roi_groups[group_key]['rois'].append(roi.get('idx'))
            
            logger.info(f"✅ Config loaded for '{product_name}': {len(server_rois)} ROIs, {len(roi_groups)} groups")
            config = {
                "rois": server_rois,  # Use server format directly
                "roi_groups": roi_groups,
                "product_name": product_name
            }
            return jsonify(config), 200
        elif response.status_code == 404:
            # Try fallback: read config file directly from server filesystem
            logger.info(f"Server API returned 404, trying direct file access...")
            config_file = f"/home/jason_nguyen/visual-aoi-server/config/products/{product_name}/rois_config_{product_name}.json"
            
            if os.path.exists(config_file):
                logger.info(f"Found config file: {config_file}")
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Convert legacy array format to ROI editor format using normalization
                if isinstance(config_data, list):
                    logger.info(f"Converting legacy array format for '{product_name}'")
                    try:
                        rois = normalize_roi_list(config_data, product_name)
                        config = {
                            "rois": rois, 
                            "roi_groups": {},
                            "product_name": product_name
                        }
                        logger.info(f"✅ Loaded and normalized {len(rois)} ROIs from file")
                        return jsonify(config), 200
                    except Exception as e:
                        logger.error(f"Failed to normalize legacy ROIs: {e}")
                        return jsonify({"error": f"ROI normalization failed: {str(e)}"}), 500
                elif isinstance(config_data, dict) and 'rois' in config_data:
                    # Modern format - still normalize to ensure consistency
                    logger.info(f"Normalizing modern format for '{product_name}'")
                    try:
                        rois = normalize_roi_list(config_data['rois'], product_name)
                        roi_groups = config_data.get('roi_groups', {})
                        config = {
                            "rois": rois, 
                            "roi_groups": roi_groups,
                            "product_name": product_name
                        }
                        logger.info(f"✅ Loaded and normalized {len(rois)} ROIs, {len(roi_groups)} groups from file")
                        return jsonify(config), 200
                    except Exception as e:
                        logger.error(f"Failed to normalize ROIs: {e}")
                        return jsonify({"error": f"ROI normalization failed: {str(e)}"}), 500
            
            # 404 is normal for products without configuration yet
            logger.info(f"ℹ️  No config found for '{product_name}' (404) - new product")
            return jsonify({"error": "Configuration not found", "rois": []}), 404
        else:
            logger.warning(f"Server returned {response.status_code} for '{product_name}'")
            return jsonify({"error": f"Server error: {response.status_code}"}), response.status_code
        
    except Exception as e:
        logger.error(f"❌ Failed to get product config for '{product_name}': {e}")
        return jsonify({"error": str(e), "rois": []}), 500


@app.route("/api/products/<product_name>/config", methods=["POST"])
def save_product_config(product_name: str):
    """Proxy: Save ROI configuration for a product to server."""
    try:
        data = request.get_json(silent=True) or {}
        server_url = state.server_url
        
        rois = data.get('rois', [])
        logger.info(f"Saving config for product '{product_name}' to server")
        logger.info(f"ROI count: {len(rois)}")
        
        # Pass ROIs directly to server without any conversion or validation
        # Server will handle validation and format
        server_payload = {'rois': rois}
        
        # Send to server
        logger.info(f"Sending to server: {server_url}/api/products/{product_name}/rois")
        response = requests.post(
            f"{server_url}/api/products/{product_name}/rois",
            json=server_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Config saved successfully to server: {result}")
            return jsonify(result), 200
        else:
            logger.error(f"❌ Server returned {response.status_code}: {response.text}")
            return jsonify({
                "error": f"Server error: {response.status_code}",
                "details": response.text
            }), response.status_code
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error saving product config: {e}")
        return jsonify({"error": f"Network error: {str(e)}"}), 503
    except Exception as e:
        logger.error(f"❌ Failed to save product config: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/camera/capture", methods=["GET", "POST"])
def capture_single_image():
    """Capture a single image from the camera for ROI editor."""
    # Check if another capture is in progress
    if not camera_lock.acquire(blocking=False):
        logger.warning("Camera capture already in progress, rejecting request")
        return jsonify({
            "error": "Camera busy - another capture is in progress",
            "retry_after": 3
        }), 429  # HTTP 429 Too Many Requests
    
    try:
        # Get focus and exposure from request body if provided
        focus = None
        exposure = None
        
        logger.info("Capturing single image for ROI editor")
        
        if request.method == "POST":
            logger.info(f"POST request received, content-type: {request.content_type}")
            logger.info(f"Request data: {request.data}")
            
            if request.is_json:
                data = request.get_json()
                logger.info(f"JSON data received: {data}")
                focus = data.get("focus")
                exposure = data.get("exposure")
                
                if focus or exposure:
                    logger.info(f"✓ Using ROI group settings: focus={focus}, exposure={exposure}")
                else:
                    logger.info("No camera settings in request, using defaults")
            else:
                logger.warning(f"POST request is not JSON, is_json={request.is_json}")
        
        # Initialize camera if not already initialized
        if not state.camera_initialized:
            logger.info("Camera not initialized, initializing now...")
            try:
                tis_camera.initialize_camera()
                state.camera_initialized = True
                logger.info("✅ Camera initialized successfully")
            except Exception as init_error:
                logger.error(f"Failed to initialize camera: {init_error}")
                return jsonify({"error": f"Camera initialization failed: {str(init_error)}"}), 500
        
        # Get camera instance
        tis_instance = tis_camera.get_camera_instance()
        if tis_instance is None:
            return jsonify({"error": "Camera instance not available"}), 500
        
        # Capture image using existing camera module function with optional focus/exposure
        if focus or exposure:
            image = tis_camera.capture_image(focus=focus, exposure_time=exposure)
        else:
            image = tis_camera.capture_image()
            
        if image is None:
            return jsonify({"error": "Failed to capture image"}), 500
        
        # Save to shared folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"roi_editor_{timestamp}.jpg"
        
        # Ensure shared folder exists
        shared_path = "/mnt/visual-aoi-shared/roi_editor"
        os.makedirs(shared_path, exist_ok=True)
        
        filepath = os.path.join(shared_path, filename)
        cv2.imwrite(filepath, image)
        
        logger.info(f"Image saved to: {filepath}")
        
        return jsonify({
            "success": True,
            "image_path": f"roi_editor/{filename}",
            "width": image.shape[1],
            "height": image.shape[0]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to capture image: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Always release the lock
        camera_lock.release()
        logger.debug("Camera lock released")


@app.route("/shared/<path:filename>")
def serve_shared_file(filename):
    """Serve files from the shared folder with no-cache headers to ensure fresh images."""
    try:
        # Base path for shared folder
        shared_base = "/mnt/visual-aoi-shared"
        
        # Security: prevent directory traversal
        safe_path = os.path.normpath(filename)
        if safe_path.startswith('..'):
            logger.warning(f"Attempted directory traversal: {filename}")
            return jsonify({"error": "Invalid path"}), 403
        
        full_path = os.path.join(shared_base, safe_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            logger.warning(f"File not found: {full_path}")
            return jsonify({"error": "File not found"}), 404
        
        # Serve the file
        directory = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)
        
        # CRITICAL: Send response with no-cache headers to prevent browser caching
        # This ensures inspection result images are always fresh
        response = send_from_directory(directory, file_name)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to serve shared file: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Register cleanup handlers
    atexit.register(cleanup_on_shutdown)
    signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination
    
    logger.info("Starting Visual AOI Client on port 5100...")
    logger.info("Cleanup handlers registered for graceful shutdown")
    
    try:
        app.run(debug=True, threaded=True, port=5100)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        cleanup_on_shutdown()
    except Exception as e:
        logger.error(f"Application error: {e}")
        cleanup_on_shutdown()
        raise
