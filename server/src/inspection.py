"""
Main inspection logic that ties together all modules.
"""

import time
import threading
import queue
import gc
import logging
from typing import List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

from .config import (PRODUCT_NAME, DEFAULT_FOCUS, DEFAULT_EXPOSURE, FOCUS_SETTLE_DELAY, ENABLE_FAST_CAPTURE, MAX_THREADS)
# Camera imports removed - all camera handling is deferred to client side
from .roi import get_rois, process_compare_roi
from .barcode import process_barcode_roi
from .ocr import process_ocr_roi
from .ai import initialize_mobilenet_model
from .ocr import initialize_easyocr_reader
from .barcode import init_dynamsoft_router
from .utils import print_memory_usage

# Stub functions for camera operations - server should not handle camera
def get_default_focus():
    """Return default focus value since server doesn't handle camera operations."""
    return DEFAULT_FOCUS

def get_default_exposure():
    """Return default exposure value since server doesn't handle camera operations."""
    return DEFAULT_EXPOSURE

def get_focus_settle_delay():
    """Return default focus settle delay since server doesn't handle camera operations."""
    return FOCUS_SETTLE_DELAY

def get_enable_fast_capture():
    """Return default fast capture setting since server doesn't handle camera operations."""
    return ENABLE_FAST_CAPTURE

def get_max_threads():
    """Return default max threads setting since server doesn't handle camera operations."""
    return MAX_THREADS

def set_camera_properties(*args, **kwargs):
    """Stub function - camera operations are handled by client only."""
    print("WARNING: Server attempted camera operation - this should be handled by client")
    return False

def capture_tis_image(*args, **kwargs):
    """Stub function - camera operations are handled by client only."""
    print("WARNING: Server attempted image capture - this should be handled by client")
    return None

def capture_tis_image_fast(*args, **kwargs):
    """Stub function - camera operations are handled by client only."""
    print("WARNING: Server attempted fast image capture - this should be handled by client")
    return None

# Global variables for system state
ui_instance = None
system_ready = False
camera_ready = False
ai_ready = False

def set_ui_instance(ui):
    """Set the UI instance for callbacks."""
    global ui_instance
    ui_instance = ui

def is_system_ready():
    """Check if core system components are ready for operation."""
    # System is ready if core initialization is complete
    # Camera is optional - system can work with placeholder images if no camera available
    # AI models are optional - system can work without them (compare ROIs will use OpenCV)
    return system_ready

def initialize_system():
    """Initialize all system components."""
    global system_ready, camera_ready, ai_ready
    
    try:
        print("Starting system initialization...")
        system_ready = False
        camera_ready = False  # Will be handled by client
        ai_ready = False
        
        # Update UI status - skip camera initialization completely
        if ui_instance:
            ui_instance.set_status("Initializing AI models...")
            ui_instance.set_system_ready(False)
        
        # CAMERA INITIALIZATION COMPLETELY REMOVED FROM SERVER
        # All camera handling will be done on client side to avoid resource conflicts
        print("Camera initialization deferred to client side")
        camera_ready = True  # Mark as ready since client will handle it
        
        # Initialize AI models first (since camera is deferred to client)
        print("Initializing AI models...")
        from .ai import initialize_mobilenet_model
        ai_ready = initialize_mobilenet_model()
        
        # Initialize barcode reader
        if ui_instance:
            ui_instance.set_status("Initializing barcode reader...")
        print("Initializing barcode reader...")
        from .barcode import init_dynamsoft_router
        init_dynamsoft_router()
        
        # Initialize OCR reader
        if ui_instance:
            ui_instance.set_status("Initializing OCR reader...")
        print("Initializing OCR reader...")
        from .ocr import initialize_easyocr_reader
        initialize_easyocr_reader()
        
        # Load ROI configuration for the selected product
        if PRODUCT_NAME:
            if ui_instance:
                ui_instance.set_status(f"Loading ROI configuration for product: {PRODUCT_NAME}")
            print(f"Loading ROI configuration for product: {PRODUCT_NAME}")
            from .roi import load_rois_from_config
            load_rois_from_config(PRODUCT_NAME)
            
            # Camera configuration is handled by client - server just loads ROI configs
            print("Camera configuration will be handled by client")
            
            # Refresh UI with loaded ROIs
            if ui_instance and hasattr(ui_instance, 'refresh_roi_editor'):
                ui_instance.refresh_roi_editor()
            
        system_ready = True
        
        # Update UI with final status
        if ui_instance:
            if is_system_ready():
                print("DEBUG: System is ready, enabling UI button...")
                status_msg = f"System ready for product: {PRODUCT_NAME}"
                if not camera_ready:
                    status_msg += " (Using placeholder images - no camera detected)"
                if not ai_ready:
                    status_msg += " (AI models disabled - compare ROIs will use OpenCV)"
                ui_instance.set_status(status_msg)
                # Use after_idle to ensure UI update happens in main thread
                ui_instance.root.after_idle(lambda: ui_instance.set_system_ready(True))
            else:
                status_msg = "System not ready. "
                if not system_ready:
                    status_msg += "Core initialization failed. "
                print(f"DEBUG: System not ready: {status_msg}")
                ui_instance.set_status(status_msg.strip())
                ui_instance.root.after_idle(lambda: ui_instance.set_system_ready(False))
        
        print("System initialization complete.")
        return True
        
    except Exception as e:
        print(f"System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        if ui_instance:
            ui_instance.set_status(f"Initialization failed: {e}")
            ui_instance.set_system_ready(False)
        return False

def process_roi(roi, img, product_name):
    """Process a single ROI based on its type."""
    if not roi or len(roi) < 3:
        return None
    
    roi_idx = roi[0]
    roi_type = roi[1]
    coords = roi[2]
    
    if len(coords) != 4:
        print(f"Invalid ROI coordinates for ROI {roi_idx}: {coords}")
        return None
    
    x1, y1, x2, y2 = coords
    
    try:
        if roi_type == 1:  # Barcode ROI
            from .barcode import process_barcode_roi
            return process_barcode_roi(img, x1, y1, x2, y2, roi_idx)
        elif roi_type == 2:  # Compare ROI
            ai_threshold = roi[5] if len(roi) > 5 else 0.9
            feature_method = roi[6] if len(roi) > 6 else "mobilenet"
            return process_compare_roi(img, x1, y1, x2, y2, roi_idx, ai_threshold, feature_method, product_name)
        elif roi_type == 3:  # OCR ROI
            rotation = roi[7] if len(roi) > 7 else 0
            expected_text = roi[9] if len(roi) > 9 else None  # Get sample text for comparison
            from .ocr import process_ocr_roi
            ocr_result = process_ocr_roi(img, x1, y1, x2, y2, roi_idx, rotation, expected_text)
            
            # Fix for OCR ROI image display - if the image is None, get it from the original
            if isinstance(ocr_result, tuple) and len(ocr_result) > 2 and ocr_result[2] is None:
                ocr_result = list(ocr_result)
                roi_img = img[y1:y2, x1:x2]  # Extract original ROI image
                ocr_result[2] = roi_img
                ocr_result = tuple(ocr_result)
            
            return ocr_result
        elif roi_type == 4:  # Color Check ROI
            # Get color config from ROI (field 11) - supports two formats:
            # 1. expected_color + color_tolerance + min_pixel_percentage (new, simpler)
            # 2. color_ranges array (legacy)
            color_config = roi[11] if len(roi) >= 12 and roi[11] is not None else None
            
            # Check if we have embedded config with new format (expected_color)
            if isinstance(color_config, dict) and 'expected_color' in color_config:
                logger.debug(f"Using expected_color format from ROI config")
                from .color_check import process_color_roi
                return process_color_roi(
                    img, x1, y1, x2, y2, roi_idx,
                    expected_color=color_config.get('expected_color'),
                    color_tolerance=color_config.get('color_tolerance', 10),
                    min_pixel_percentage=color_config.get('min_pixel_percentage', 5.0)
                )
            
            # Check if we have embedded config with legacy format (color_ranges)
            elif isinstance(color_config, dict) and 'color_ranges' in color_config:
                logger.debug(f"Using embedded color_ranges from ROI config")
                from .color_check import process_color_roi
                return process_color_roi(img, x1, y1, x2, y2, roi_idx, 
                                        color_ranges=color_config.get('color_ranges'))
            
            # Fallback to product-level config file
            elif product_name:
                try:
                    import os
                    import json
                    
                    color_config_path = os.path.join(
                        'config', 'products', product_name,
                        f'colors_config_{product_name}.json'
                    )
                    
                    if os.path.exists(color_config_path):
                        with open(color_config_path, 'r') as f:
                            config_data = json.load(f)
                            color_ranges = config_data.get('color_ranges', [])
                        logger.debug(f"Loaded {len(color_ranges)} color ranges from product config for {product_name}")
                        from .color_check import process_color_roi
                        return process_color_roi(img, x1, y1, x2, y2, roi_idx, color_ranges=color_ranges)
                    else:
                        logger.warning(f"No color config found for product {product_name}")
                except Exception as e:
                    logger.error(f"Error loading color config: {e}")
            
            # No config found anywhere
            logger.error(f"No color configuration found for ROI {roi_idx}")
            from .color_check import process_color_roi
            return process_color_roi(img, x1, y1, x2, y2, roi_idx)
        else:
            print(f"Unknown ROI type: {roi_type}")
            return None
    except Exception as e:
        print(f"Error processing ROI {roi_idx}: {e}")
        import traceback
        traceback.print_exc()
        return None

def capture_and_update():
    """Server-side stub function - actual inspection is handled by client."""
    print("WARNING: capture_and_update called on server side - camera operations should be handled by client")
    if ui_instance:
        ui_instance.set_status("Camera operations are handled by client - server does not capture images")
    return None

    print("DEBUG: Asynchronous inspection process started")

def is_roi_passed(roi_result: Tuple) -> bool:
    """Check if a ROI result indicates a pass.
    
    ROI result formats:
    - Barcode: (idx, 1, roi_img, None, coords, "Barcode", data)
    - Compare: (idx, 2, roi_img, golden_img, coords, "Compare", result, color, similarity, threshold)
    - OCR: (idx, 3, roi_img, None, coords, "OCR", data, rotation)
    - Color: (idx, 4, roi_img, None, coords, "Color", result_dict)
    """
    if not roi_result or len(roi_result) < 2:
        return False
    
    roi_type = roi_result[1]
    
    if roi_type == 2:  # Compare ROI
        # For compare ROI: roi_result[6] contains "Match" or "Different"
        if len(roi_result) > 6:
            match_result = str(roi_result[6])
            return "Match" in match_result
        return False
    elif roi_type == 1:  # Barcode ROI
        # For barcode ROI: roi_result[6] contains the barcode data
        barcode_result = roi_result[6] if len(roi_result) > 6 else None
        return bool(barcode_result and str(barcode_result).strip())
    elif roi_type == 3:  # OCR ROI
        # For OCR ROI: roi_result[6] contains the OCR text with [PASS]/[FAIL] tags
        ocr_result = roi_result[6] if len(roi_result) > 6 else ""
        ocr_text = str(ocr_result).strip()
        # OCR pass/fail logic:
        # - FAIL tag present: explicit failure (expected text not found or no text detected)
        # - PASS tag present: explicit pass (expected text found or text detected without validation)
        if "[FAIL:" in ocr_text:
            return False
        elif "[PASS:" in ocr_text:
            return True
        else:
            # Fallback: if no tags present (shouldn't happen with updated logic), consider it a fail
            return False
    elif roi_type == 4:  # Color Check ROI
        # For color ROI: roi_result[6] contains result dict with 'passed' field
        color_result = roi_result[6] if len(roi_result) > 6 else {}
        if isinstance(color_result, dict):
            return color_result.get('passed', False)
        return False
    
    return False

def run_single_inspection():
    """Run a single inspection cycle (for testing/debugging)."""
    if not initialize_system():
        print("System initialization failed. Cannot run inspection.")
        return False
    
    print("Running single inspection...")
    capture_and_update()
    return True

def main_inspection_loop():
    """Main inspection loop (if running without GUI)."""
    if not initialize_system():
        print("System initialization failed.")
        return
    
    print("Starting inspection loop. Press Ctrl+C to stop.")
    try:
        while True:
            print("\n" + "="*50)
            print(f"Starting inspection at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            capture_and_update()
            print("Inspection cycle complete.")
            
            # Wait for user input or implement automatic trigger
            input("Press Enter for next inspection or Ctrl+C to exit...")
            
    except KeyboardInterrupt:
        print("\nInspection loop stopped by user.")
    except Exception as e:
        print(f"Inspection loop error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run inspection loop if this module is executed directly
    main_inspection_loop()
