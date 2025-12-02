"""
OCR (Optical Character Recognition) functionality.
"""

import cv2
import numpy as np
import gc
from PIL import Image

# ========== EASYOCR READER ==========
# Initialize as None, will be loaded later to avoid conflicts
easyocr_reader = None

# Make easyocr available for mocking in tests
try:
    import easyocr
except ImportError:
    easyocr = None

def initialize_ocr_reader(languages=['en', 'fr', 'de', 'vi'], gpu=True):
    """Initialize and return an EasyOCR reader instance."""
    try:
        if easyocr is None:
            raise ImportError("easyocr module not available")
        
        # For RTX 5080: First try GPU, but with better error handling
        if gpu:
            try:
                reader = easyocr.Reader(languages, verbose=False, gpu=True)
                print("EasyOCR initialized with GPU support")
                return reader
            except Exception as gpu_error:
                print(f"GPU EasyOCR initialization failed: {gpu_error}")
                print("This is normal for RTX 5080 - PyTorch may need JIT compilation")
                print("Falling back to CPU...")
        
        # CPU fallback
        reader = easyocr.Reader(languages, verbose=False, gpu=False)
        print("EasyOCR initialized with CPU")
        return reader
        
    except Exception as e:
        print(f"OCR initialization failed: {e}")
        return None

def read_text(image_array, reader=None):
    """Read text from image array using provided or default reader."""
    if reader is None:
        reader = easyocr_reader
        if reader is None:
            reader = initialize_ocr_reader()
            if reader is None:
                return []
    
    try:
        # Convert BGR to RGB if needed
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image_array
        
        result = reader.readtext(image_rgb, detail=0)
        return result
    except Exception as e:
        print(f"OCR text reading error: {e}")
        return []

def initialize_easyocr_reader():
    """Initialize EasyOCR reader with GPU priority for RTX 5080."""
    global easyocr_reader
    if easyocr_reader is not None:
        return True
        
    try:
        import easyocr
        import torch
        
        # Check PyTorch CUDA compatibility first
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            print(f"Detected {device_count} CUDA device(s)")
            
            for i in range(device_count):
                gpu_name = torch.cuda.get_device_name(i)
                print(f"  GPU {i}: {gpu_name}")
        
        # Try GPU first - PyTorch 2.5.1 has much better RTX 5080 support
        try:
            print("Attempting to initialize EasyOCR with GPU support...")
            easyocr_reader = easyocr.Reader(['en', 'fr', 'de', 'vi'], verbose=False, gpu=True)
            print("✓ EasyOCR initialized successfully with GPU acceleration")
            return True
        except Exception as gpu_error:
            print(f"GPU EasyOCR initialization failed: {gpu_error}")
            print("Falling back to CPU mode...")
        
        # CPU fallback
        try:
            easyocr_reader = easyocr.Reader(['en', 'fr', 'de', 'vi'], verbose=False, gpu=False)
            print("✓ EasyOCR initialized successfully with CPU")
            return True
        except Exception as cpu_error:
            print(f"CPU EasyOCR initialization also failed: {cpu_error}")
        
        print("Warning: EasyOCR reader not available, OCR text will be empty")
        easyocr_reader = None
        return False
        
    except Exception as e:
        print(f"EasyOCR initialization failed completely: {e}")
        print("Warning: EasyOCR reader not available, OCR text will be empty")
        easyocr_reader = None
        return False

def process_ocr_roi(norm2, x1, y1, x2, y2, idx, rotation=0, expected_text=None):
    """Process an OCR ROI and return text results with optional sample text comparison."""
    print(f"DEBUG: Entered process_ocr_roi with idx={idx}, coords=({x1},{y1},{x2},{y2}), rotation={rotation}, expected_text='{expected_text}'")
    try:
        img_h, img_w = norm2.shape[:2]
        # Defensive bounds check
        x1 = max(0, min(x1, img_w - 1))
        x2 = max(0, min(x2, img_w - 1))
        y1 = max(0, min(y1, img_h - 1))
        y2 = max(0, min(y2, img_h - 1))
        
        if x1 >= x2 or y1 >= y2:
            print(f"DEBUG: Invalid ROI size for idx={idx}, skipping OCR")
            # Return empty image for invalid ROI
            empty_img = np.zeros((10, 10, 3), dtype=np.uint8)
            # Return format: (idx, type, captured_image, golden_image, coords, type_name, text, rotation)
            return (idx, 3, empty_img, None, (x1, y1, x2, y2), "OCR", "", rotation)
            
        roi_img = norm2[y1:y2, x1:x2]
        print(f"DEBUG: roi_img shape: {roi_img.shape}")
        
        # Check for empty or too small ROI
        if roi_img.size == 0 or roi_img.shape[0] < 10 or roi_img.shape[1] < 10:
            print(f"DEBUG: Empty or too small ROI for idx={idx}, skipping OCR")
            # Return format: (idx, type, captured_image, golden_image, coords, type_name, text, rotation)
            return (idx, 3, roi_img, None, (x1, y1, x2, y2), "OCR", "", rotation)
        
        # Convert to RGB first (OpenCV uses BGR by default)
        roi_rgb = cv2.cvtColor(roi_img, cv2.COLOR_BGR2RGB)
        print(f"DEBUG: roi_rgb shape before rotation: {roi_rgb.shape}")
        
        # Rotate if needed, expanding the image so nothing is cropped
        if rotation != 0:
            print(f"DEBUG: Rotating OCR image by {rotation} degrees")
            # PIL Image.fromarray expects RGB format, which we now have
            roi_pil = Image.fromarray(roi_rgb)
            roi_pil = roi_pil.rotate(rotation, expand=True)
            roi_rgb = np.array(roi_pil)
            print(f"DEBUG: roi_rgb shape after rotation: {roi_rgb.shape}")
        
        print(f"DEBUG: Final roi_rgb shape for OCR: {roi_rgb.shape}")
        
        # Remove debug image write for speed and memory
        # cv2.imwrite(f"roi{idx+1}_ocr.jpg", roi_rgb)
        
        if easyocr_reader is None:
            # Try to initialize the reader if not already done
            if not initialize_easyocr_reader():
                print("Warning: EasyOCR reader not available, OCR text will be empty")
                result = []
            else:
                result = easyocr_reader.readtext(roi_rgb, detail=0) if easyocr_reader else []
        else:
            result = easyocr_reader.readtext(roi_rgb, detail=0)
        
        print(f"DEBUG: OCR result: {result}")
        text = " ".join(str(item) for item in result).strip()
        
        # Perform sample text comparison if expected_text is provided
        comparison_result = ""
        if expected_text is not None and expected_text.strip():
            detected_text_clean = text.lower().strip()
            expected_text_clean = expected_text.lower().strip()
            
            # Check if detected text contains sample text (case-insensitive substring matching)
            # For pass: detected text MUST contain the expected sample text
            if expected_text_clean in detected_text_clean:
                comparison_result = f" [PASS: Contains '{expected_text}']"
                print(f"DEBUG: OCR text comparison PASSED - detected: '{text}' contains expected: '{expected_text}'")
            else:
                comparison_result = f" [FAIL: Expected '{expected_text}', detected '{text}']"
                print(f"DEBUG: OCR text comparison FAILED - detected: '{text}' does NOT contain expected: '{expected_text}'")
        else:
            # If no expected_text provided, any detected text is considered a pass
            if text:
                comparison_result = " [PASS: Text detected]"
                print(f"DEBUG: OCR text detected (no validation): '{text}'")
            else:
                comparison_result = " [FAIL: No text detected]"
                print(f"DEBUG: OCR failed - no text detected")
        
        # Append comparison result to the text for display
        final_text = text + comparison_result
        
        gc.collect()
        
    except Exception as e:
        print(f"Error in OCR processing: {e}")
        import traceback
        traceback.print_exc()
        text = "Error in OCR: " + str(e)
        # Return format: (idx, type, captured_image, golden_image, coords, type_name, text, rotation)
        return (idx, 3, roi_img, None, (x1, y1, x2, y2), "OCR", text, rotation)
    
    print(f"DEBUG: Returning from process_ocr_roi idx={idx} with text='{final_text}'")
    # Return format: (idx, type, captured_image, golden_image, coords, type_name, text, rotation)
    return (idx, 3, roi_img, None, (x1, y1, x2, y2), "OCR", final_text, rotation)
