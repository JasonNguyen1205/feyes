"""
Barcode detection and reading functionality.
"""

import cv2
import numpy as np
import ast

# ========== DYNAMSOFT BARCODE READER GLOBALS ==========
DYNAMSOFT_LICENSE = "DLC2MTc1NDQ3NTU1NwAB81/gLw1+Ai+DIrkPyJR2A1Vu9MUhTjpkrONwKA23HVQOEZHKawgdTViML5isBbSuKGEG1X2BZVCX+BervTfGr1uypFWqZJZrOn/WXVHkFuKFSBXeQRjRpJFa48p9vMkRYGuZFR0Qw+28+KgzogAqlQtGmPaBbWkuav3ScXZceO8hpS2koU5ODP3cOI47M7KjkCVKU755eyQdU0fsAnO71crUXfrHqi3BNmRIn3Qw9W/srCPzx+ksVwPXb0+WTo3DCoY2618b/J44AwwA8N/gIIDti5xySGG2ifx2rs7K10ETqW14Hos5mJjrigzworYVaVVE9EFFpRn7E1yHLAFRVk+tF/EKY7xChG4TpZDrSPhNA0myfzpC4hGorgGP3j2opkEHiOA/Px3xFWTphL6vRV90IV12afFjjoJl3pHJvCGc/6jvAbGF65Eh7ym+eKqHp7J+++aJlO2N3etEaP3JjXYE7NSAxppxavmBFWM7PshdfAJ7rWZ0fHIeszwGH2jnYxxwHXHfqREvOOSH7ZbUggiB04ci2mFnfwGRmB8mbzQPS8w/kjvZ/xD23BgFLwrg6zuWVpbMHS5cvQvl7ixcVeTTUrMZ3GNnt+N+joq6HTk/Z3+W6zlaFtvN1GqUoLeKCyZmR7k="
DYNAMSOFT_ROUTER = None
DYNAMSOFT_LICENSE_INITIALIZED = False

class BarcodeReader:
    """Wrapper class for Dynamsoft Barcode Reader functionality."""
    
    def __init__(self):
        self.router = None
        self.license_initialized = False
    
    def init_license(self, license_key):
        """Initialize the license for barcode reading."""
        try:
            from dynamsoft_barcode_reader_bundle import LicenseManager, EnumErrorCode
            errorCode, errorMsg = LicenseManager.init_license(license_key)
            if errorCode != EnumErrorCode.EC_OK and errorCode != EnumErrorCode.EC_LICENSE_CACHE_USED:
                return (errorCode, f"License initialization failed: {errorMsg}")
            self.license_initialized = True
            return (0, "License initialized successfully")
        except Exception as e:
            return (-1, f"License initialization error: {e}")
    
    def decode_buffer(self, buffer_data):
        """Decode barcodes from buffer data."""
        if not self.license_initialized:
            return []
        try:
            from dynamsoft_barcode_reader_bundle import CaptureVisionRouter, EnumPresetTemplate
            if self.router is None:
                self.router = CaptureVisionRouter()
            
            result_array = self.router.capture_multi_pages(buffer_data, EnumPresetTemplate.PT_READ_BARCODES)
            results = result_array.get_results() if result_array else None
            
            barcodes = []
            if results:
                for result in results:
                    barcode_result = result.get_decoded_barcodes_result()
                    if barcode_result and barcode_result.get_items():
                        items = barcode_result.get_items()
                        for item in items:
                            barcodes.append(item.get_text())
            return barcodes
        except Exception as e:
            print(f"Barcode decoding error: {e}")
            return []

def initialize_barcode_reader(license_key=None):
    """Initialize and return a BarcodeReader instance."""
    if license_key is None:
        license_key = DYNAMSOFT_LICENSE
    
    reader = BarcodeReader()
    if license_key:
        error_code, error_msg = reader.init_license(license_key)
        if error_code != 0:
            print(f"Barcode reader license error: {error_msg}")
    return reader

def read_barcodes(image_array, reader=None):
    """Read barcodes from image array using provided or default reader."""
    if reader is None:
        reader = initialize_barcode_reader()
    
    try:
        # Encode as JPEG in memory
        is_success, buffer = cv2.imencode(".jpg", image_array)
        if not is_success:
            return []
        
        jpeg_bytes = buffer.tobytes()
        return reader.decode_buffer(jpeg_bytes)
    except Exception as e:
        print(f"Barcode reading error: {e}")
        return []

def init_dynamsoft_router():
    """Initialize Dynamsoft barcode router."""
    global DYNAMSOFT_ROUTER, DYNAMSOFT_LICENSE_INITIALIZED
    if DYNAMSOFT_ROUTER is not None and DYNAMSOFT_LICENSE_INITIALIZED:
        return DYNAMSOFT_ROUTER
    try:
        from dynamsoft_barcode_reader_bundle import CaptureVisionRouter, EnumErrorCode, LicenseManager
        errorCode, errorMsg = LicenseManager.init_license(DYNAMSOFT_LICENSE)
        if errorCode != EnumErrorCode.EC_OK and errorCode != EnumErrorCode.EC_LICENSE_CACHE_USED:
            print("License initialization failed: ErrorCode:", errorCode, ", ErrorString:", errorMsg)
            DYNAMSOFT_LICENSE_INITIALIZED = False
            DYNAMSOFT_ROUTER = None
            return None
        DYNAMSOFT_ROUTER = CaptureVisionRouter()
        DYNAMSOFT_LICENSE_INITIALIZED = True
        return DYNAMSOFT_ROUTER
    except Exception as e:
        print("Dynamsoft router init error:", e)
        DYNAMSOFT_ROUTER = None
        DYNAMSOFT_LICENSE_INITIALIZED = False
        return None

def scan_barcodes_from_array(image_array, roi_idx=None):
    """
    Scan barcodes using Dynamsoft Barcode Reader SDK with CaptureVisionRouter.
    Uses JPEG encoding for in-memory images.
    """
    try:
        from dynamsoft_barcode_reader_bundle import EnumPresetTemplate, EnumErrorCode
        cvr_instance = init_dynamsoft_router()
        if cvr_instance is None:
            print("Dynamsoft router not initialized.")
            return None
        
        # Encode as JPEG in memory (SDK supports JPEG)
        is_success, buffer = cv2.imencode(".jpg", image_array)
        if not is_success:
            print("Failed to encode image as JPEG for barcode scanning.")
            return None
        
        jpeg_bytes = buffer.tobytes()
        
        # Decode barcodes from buffer using preset template
        result_array = cvr_instance.capture_multi_pages(jpeg_bytes, EnumPresetTemplate.PT_READ_BARCODES)
        results = result_array.get_results() if result_array else None
        barcodes = []
        
        if results is None or len(results) == 0:
            return None
            
        for i, result in enumerate(results):
            if result.get_error_code() == EnumErrorCode.EC_UNSUPPORTED_JSON_KEY_WARNING:
                print("Warning:", result.get_error_code(), result.get_error_string())
            elif result.get_error_code() != EnumErrorCode.EC_OK:
                print("Error:", result.get_error_code(), result.get_error_string())
            
            barcode_result = result.get_decoded_barcodes_result()
            if barcode_result is None or barcode_result.get_items() == 0:
                continue
                
            items = barcode_result.get_items()
            for item in items:
                barcodes.append(item.get_text())
                
        return barcodes if barcodes else None
    except Exception as e:
        print("Dynamsoft barcode error:", e)
        return None

def safe_parse_coords(coord_str):
    """Safely parse coordinate strings."""
    try:
        coords = ast.literal_eval(coord_str)
        if isinstance(coords, list):
            return coords
    except Exception:
        pass
    return []

def process_barcode_roi(norm2, x1, y1, x2, y2, idx):
    """Process a barcode ROI and return results in the format expected by the UI."""
    roi_barcode = norm2[y1:y2, x1:x2]
    # Removed cv2.imwrite for speed (uncomment for debugging)
    # cv2.imwrite(f"roi{idx+1}_barcode.jpg", roi_barcode)
    barcode_result = scan_barcodes_from_array(roi_barcode, roi_idx=idx)
    
    # Process barcode results to match main_old.py format
    if barcode_result and isinstance(barcode_result, list):
        barcode_values = [b["Barcode"] if isinstance(b, dict) and "Barcode" in b else b for b in barcode_result]
    else:
        # Return empty list instead of None when no barcodes detected
        barcode_values = []
    
    print(f"DEBUG: Barcode ROI result for idx={idx}: {barcode_values}")
    
    # Return format: (idx, roi_type, roi_image, None, coordinates, "Barcode", barcode_values)
    # This matches the format expected by the UI in main_old.py
    return (idx, 1, roi_barcode, None, (x1, y1, x2, y2), "Barcode", barcode_values)
