"""ROI processing functionality for Visual AOI system."""

import os
import time
import cv2
import numpy as np
import glob
import json
import threading
from collections import defaultdict
from .ai_pytorch import extract_features_from_array, cosine_similarity, normalize_illumination
from .config import get_config_filename, get_golden_roi_dir

# Global lock for thread-safe golden sample updates (prevents race conditions in parallel processing)
golden_update_lock = threading.Lock()

# Global ROI list
ROIS = []

def normalize_roi(r):
    """
    Normalize ROI to always include all required fields.
    Supports both array format and object format:
    - Array: [idx, type, coords, focus, exposure, threshold, method, rotation, device, expected_text, is_device_barcode]
    - Object: {"idx": 1, "type": 2, "coords": [...], ...}
    
    Returns 12-field tuple: (idx, type, coords, focus, exposure, threshold, method, rotation, device, expected_text, is_device_barcode, color_ranges)
    Note: color_ranges is only used for type 4 (Color ROI), otherwise None
    """
    # Handle object format (dict)
    if isinstance(r, dict):
        # Extract color config if present (for type 4 Color ROI)
        # Support both formats:
        # 1. color_ranges (legacy) - array of range objects
        # 2. expected_color + color_tolerance + min_pixel_percentage (new)
        color_config = None
        if r.get('expected_color') is not None:
            # New format: expected_color with tolerance
            color_config = {
                'expected_color': r.get('expected_color'),
                'color_tolerance': r.get('color_tolerance', 10),
                'min_pixel_percentage': r.get('min_pixel_percentage', 5.0)
            }
        elif r.get('color_ranges') is not None:
            # Legacy format: color ranges array
            color_config = {'color_ranges': r.get('color_ranges')}
        
        return (
            int(r.get('idx', 0)),
            int(r.get('type', 1)),
            tuple(r.get('coords', [])),
            int(r.get('focus', 305)),
            int(r.get('exposure', 1200)),
            float(r['ai_threshold']) if r.get('ai_threshold') is not None else None,
            str(r.get('feature_method', 'opencv')) if r.get('feature_method') is not None else None,
            int(r.get('rotation', 0)),
            int(r.get('device_location', 1)),
            str(r['expected_text']) if r.get('expected_text') is not None else None,
            bool(r['is_device_barcode']) if r.get('is_device_barcode') is not None else None,
            color_config  # Field 11: Color config (dict with expected_color+tolerance OR color_ranges)
        )
    
    # Handle array format (legacy)
    # (idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text, is_device_barcode, color_ranges)
    if len(r) == 12:
        # NEW: 12-field format with color_ranges
        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text, is_device_barcode, color_ranges = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        is_device_barcode_val = bool(is_device_barcode) if is_device_barcode is not None else None
        feature_method_val = str(feature_method) if feature_method is not None else None
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure), ai_threshold_val, feature_method_val, int(rotation), int(device_location), str(expected_text) if expected_text is not None else None, is_device_barcode_val, color_ranges)
    elif len(r) == 11:
        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text, is_device_barcode = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        is_device_barcode_val = bool(is_device_barcode) if is_device_barcode is not None else None
        feature_method_val = str(feature_method) if feature_method is not None else None
        color_ranges = None  # Default for backward compatibility
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure), ai_threshold_val, feature_method_val, int(rotation), int(device_location), str(expected_text) if expected_text is not None else None, is_device_barcode_val, color_ranges)
    elif len(r) == 10:
        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        feature_method_val = str(feature_method) if feature_method is not None else None
        is_device_barcode = None  # Default for backward compatibility
        color_ranges = None  # Default for backward compatibility
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure), ai_threshold_val, feature_method_val, int(rotation), int(device_location), str(expected_text) if expected_text is not None else None, is_device_barcode, color_ranges)
    elif len(r) == 9:
        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        feature_method_val = str(feature_method) if feature_method is not None else None
        expected_text = None  # Default for backward compatibility
        is_device_barcode = None  # Default for backward compatibility
        color_ranges = None  # Default for backward compatibility
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure), ai_threshold_val, feature_method_val, int(rotation), int(device_location), expected_text, is_device_barcode, color_ranges)
    elif len(r) == 8:
        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        feature_method_val = str(feature_method) if feature_method is not None else None
        device_location = 1  # Default to device location 1
        expected_text = None  # Default for backward compatibility
        is_device_barcode = None  # Default for backward compatibility
        color_ranges = None  # Default for backward compatibility
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure), ai_threshold_val, feature_method_val, int(rotation), int(device_location), expected_text, is_device_barcode, color_ranges)
    elif len(r) == 7:
        idx, typ, coords, focus, exposure, ai_threshold, feature_method = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        feature_method_val = str(feature_method) if feature_method is not None else None
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        expected_text = None  # Default for backward compatibility
        is_device_barcode = None  # Default for backward compatibility
        color_ranges = None  # Default for backward compatibility
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure), ai_threshold_val, feature_method_val, int(rotation), int(device_location), expected_text, is_device_barcode, color_ranges)
    elif len(r) == 6:
        idx, typ, coords, focus, exposure, ai_threshold = r
        feature_method = "mobilenet" if int(typ) == 2 else "opencv"
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        expected_text = None  # Default for backward compatibility
        is_device_barcode = None  # Default for backward compatibility
        color_ranges = None  # Default for backward compatibility
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure), ai_threshold_val, feature_method, int(rotation), int(device_location), expected_text, is_device_barcode, color_ranges)
    elif len(r) == 5:
        # Legacy format: add defaults for new fields
        idx, typ, coords, focus, ai_threshold = r
        exposure = 3000
        feature_method = "mobilenet" if int(typ) == 2 else "opencv"
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else (0.9 if int(typ) == 2 else None)
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        expected_text = None  # Default for backward compatibility
        is_device_barcode = None  # Default for backward compatibility
        color_ranges = None  # Default for backward compatibility
        return (int(idx), int(typ), tuple(coords), int(focus), exposure, ai_threshold_val, feature_method, int(rotation), int(device_location), expected_text, is_device_barcode, color_ranges)
    elif len(r) == 4:
        # Legacy format: add defaults for new fields
        idx, typ, coords, focus = r
        exposure = 3000
        ai_threshold = 0.9 if int(typ) == 2 else None
        feature_method = "mobilenet" if int(typ) == 2 else "opencv"
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        expected_text = None  # Default for backward compatibility
        is_device_barcode = None  # Default for backward compatibility
        color_ranges = None  # Default for backward compatibility
        return (int(idx), int(typ), tuple(coords), int(focus), exposure, ai_threshold, feature_method, int(rotation), int(device_location), expected_text, is_device_barcode, color_ranges)
    elif len(r) == 3:
        # Legacy format: add defaults for new fields
        idx, typ, coords = r
        focus = 305
        exposure = 3000
        ai_threshold = 0.9 if int(typ) == 2 else None
        feature_method = "mobilenet" if int(typ) == 2 else "opencv"
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        expected_text = None  # Default for backward compatibility
        is_device_barcode = None  # Default for backward compatibility
        color_ranges = None  # Default for backward compatibility
        return (int(idx), int(typ), tuple(coords), focus, exposure, ai_threshold, feature_method, int(rotation), int(device_location), expected_text, is_device_barcode, color_ranges)
    else:
        return None

def get_next_roi_index():
    """Return the next available ROI index (max existing idx + 1) from the global ROIS list."""
    if not ROIS:
        return 1
    try:
        max_idx = max(int(r[0]) for r in ROIS if r is not None and len(r) > 0)
        return max_idx + 1
    except Exception:
        return 1

def save_rois_to_config(product_name):
    """Save ROIs to configuration file."""
    global ROIS
    if product_name:
        # Get the absolute path to the project root
        # This file is in src/roi.py, so project root is one level up from src
        current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src directory
        project_root = os.path.dirname(current_file_dir)  # project root
        config_file = os.path.join(project_root, get_config_filename(product_name))
        config_dir = os.path.dirname(config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        # Save all ROI attributes, including exposure and ai_threshold
        with open(config_file, 'w') as f:
            json.dump(ROIS, f)
        # Camera configuration is handled by client - server just saves ROI configs
        if ROIS:
            print("ROI configuration saved - camera configuration will be handled by client")

def load_rois_from_config(product_name):
    """Load ROIs from configuration file."""
    global ROIS
    from .config import default_focus, default_exposure
    
    if product_name:
        # Get the absolute path to the project root
        # This file is in src/roi.py, so project root is one level up from src
        current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src directory
        project_root = os.path.dirname(current_file_dir)  # project root
        config_file = os.path.join(project_root, get_config_filename(product_name))
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    loaded = json.load(f)
                    # Support both dict (object) and list (array) formats
                    ROIS = []
                    for r in loaded:
                        if isinstance(r, dict):
                            # Object format - pass directly to normalize_roi
                            normalized = normalize_roi(r)
                        else:
                            # Array format - convert to tuple first
                            normalized = normalize_roi(tuple(r))
                        if normalized is not None:
                            ROIS.append(normalized)
            
            # Set default focus/exposure to first ROI group and update camera
            group_dict = defaultdict(list)
            
            for roi in ROIS:
                focus = None
                exposure = None
                if roi is None:
                    continue
                if roi[1] == 2:
                    # AI comparison ROI - unpack all fields including device location
                    if len(roi) >= 12:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text, is_device_barcode, _ = roi[:12]
                    elif len(roi) >= 11:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text, is_device_barcode = roi[:11]
                    elif len(roi) >= 10:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text = roi[:10]
                    elif len(roi) >= 9:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location = roi[:9]
                    elif len(roi) >= 7:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method = roi[:7]
                    else:
                        idx, typ, coords, focus, exposure = roi[:5]
                elif roi[1] == 1:
                    # Barcode ROI - unpack all fields including device location and is_device_barcode
                    if len(roi) >= 12:
                        idx, typ, coords, focus, exposure, _, _, _, device_location, expected_text, is_device_barcode, _ = roi[:12]
                    elif len(roi) >= 11:
                        idx, typ, coords, focus, exposure, _, _, _, device_location, expected_text, is_device_barcode = roi[:11]
                    elif len(roi) >= 10:
                        idx, typ, coords, focus, exposure, _, _, _, device_location, expected_text = roi[:10]
                    elif len(roi) >= 9:
                        idx, typ, coords, focus, exposure, _, _, _, device_location = roi[:9]
                    elif len(roi) >= 7:
                        idx, typ, coords, focus, exposure, _, _ = roi[:7]
                    else:
                        idx, typ, coords, focus, exposure = roi[:5]
                    feature_method = "barcode"
                    ai_threshold = None
                elif roi[1] == 3:
                    # OCR ROI - unpack all fields including device location and expected_text (expected_text)
                    if len(roi) >= 12:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text, is_device_barcode, _ = roi[:12]
                    elif len(roi) >= 11:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text, is_device_barcode = roi[:11]
                    elif len(roi) >= 10:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text = roi[:10]
                    elif len(roi) >= 9:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location = roi[:9]
                        expected_text = None
                    elif len(roi) >= 8:
                        idx, typ, coords, focus, exposure, ai_threshold, feature_method, rotation = roi[:8]
                        expected_text = None
                    else:
                        idx, typ, coords, focus, exposure, _, _ = roi[:7]
                        expected_text = None
                elif roi[1] == 4:
                    # Color ROI - unpack fields (12-field format with color_config)
                    if len(roi) >= 12:
                        idx, typ, coords, focus, exposure, _, _, rotation, device_location, _, _, color_config = roi
                    elif len(roi) >= 9:
                        idx, typ, coords, focus, exposure, _, _, rotation, device_location = roi[:9]
                    elif len(roi) >= 8:
                        idx, typ, coords, focus, exposure, _, _, rotation = roi[:8]
                    else:
                        idx, typ, coords, focus, exposure = roi[:5]
                else:
                    # Unknown type - extract basic fields
                    idx, typ, coords, focus, exposure = roi[:5]
                group_dict[(focus, exposure)].append(roi)
            
            if group_dict:
                first_key = next(iter(group_dict))
                default_focus, default_exposure = first_key
                print(f"ROI configuration loaded - camera configuration (focus={default_focus}, exposure={default_exposure}) will be handled by client")
        except Exception as e:
            print(f"Failed to load ROIs from config: {e}")
            import traceback
            traceback.print_exc()
            ROIS = []
    else:
        ROIS = []

def save_golden_roi(idx, roi_img, product_name):
    """Save a golden ROI image."""
    # Get the absolute path to the project root
    # This file is in src/roi.py, so project root is one level up from src
    current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src directory
    project_root = os.path.dirname(current_file_dir)  # project root
    roi_dir = os.path.join(project_root, get_golden_roi_dir(product_name, idx))
    os.makedirs(roi_dir, exist_ok=True)
    best_path = os.path.join(roi_dir, "best_golden.jpg")
    img = cv2.imread(best_path)  # Check if best_golden.jpg exists
    if img is not None:
        # If it exists, rename it to original_TIMESTAMP.jpg
        ts = int(time.time())
        os.rename(best_path, os.path.join(roi_dir, f"original_{ts}.jpg"))
    # Save the new best golden image
    cv2.imwrite(best_path, roi_img)

def load_golden_rois(idx, product_name):
    """Load golden ROI images for comparison."""
    if product_name:
        # Get the absolute path to the project root
        # This file is in src/roi.py, so project root is one level up from src
        current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src directory
        project_root = os.path.dirname(current_file_dir)  # project root
        roi_dir = os.path.join(project_root, get_golden_roi_dir(product_name, idx))
        if not os.path.exists(roi_dir):
            return []
        files = [os.path.join(roi_dir, f) for f in os.listdir(roi_dir) if f.endswith(".jpg")]
        rois = [cv2.imread(f) for f in files]
        return [roi for roi in rois if roi is not None]
    return []

def update_best_golden_image(idx, best_golden_path, product_name, similarity_score=None):
    """Rename best golden image to 'best_golden.jpg' with thread safety for parallel processing."""
    
    # CRITICAL: Lock to prevent race conditions when multiple ROIs promote golden samples simultaneously
    # Without this lock, parallel ROI processing can cause:
    # - Timestamp collisions (same backup filename)
    # - File corruption (multiple threads renaming same file)
    # - Wrong golden samples (threads overwriting each other's changes)
    with golden_update_lock:
        print(f"🔄 Updating best golden image for ROI {idx}...")
        print(f"   Promoting: {os.path.basename(best_golden_path)}")
        
        # Get the absolute path to the project root
        # This file is in src/roi.py, so project root is one level up from src
        current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src directory
        project_root = os.path.dirname(current_file_dir)  # project root
        roi_dir = os.path.join(project_root, get_golden_roi_dir(product_name, idx))
        
        # Rename current best_golden.jpg to {timestamp}_golden_sample.jpg if it exists
        # Use milliseconds for unique timestamps (prevents collisions in parallel processing)
        ts = int(time.time() * 1000)
        current_best = os.path.join(roi_dir, "best_golden.jpg")
        if os.path.exists(current_best):
            backup_name = f"{ts}_golden_sample.jpg"
            backup_path = os.path.join(roi_dir, backup_name)
            os.rename(current_best, backup_path)
            print(f"   Backed up old best golden as: {backup_name}")
        
        # Rename the new best golden to best_golden.jpg
        if os.path.abspath(best_golden_path) != os.path.abspath(current_best):
            if os.path.exists(best_golden_path):
                promoted_filename = os.path.basename(best_golden_path)
                os.rename(best_golden_path, current_best)
                print(f"   ✓ {promoted_filename} is now the best golden image")
            else:
                print(f"   ⚠️ Warning: Source file {best_golden_path} not found")
        
        print(f"   ✓ Best golden image update completed for ROI {idx}")

def process_compare_roi(norm2, x1, y1, x2, y2, idx, ai_threshold=0.9, feature_method="mobilenet", product_name=None):
    """Process a comparison ROI and return results with enhanced golden image matching."""
    crop2 = norm2[y1:y2, x1:x2]
    crop2_normalized = normalize_illumination(crop2)
    # Get the absolute path to the project root
    # This file is in src/roi.py, so project root is one level up from src
    current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src directory
    project_root = os.path.dirname(current_file_dir)  # project root
    roi_dir = os.path.join(project_root, get_golden_roi_dir(product_name, idx))
    golden_files = glob.glob(os.path.join(roi_dir, "*.jpg"))
    
    # Prioritize best_golden.jpg
    best_golden_path = os.path.join(roi_dir, "best_golden.jpg")
    golden_files_sorted = [best_golden_path] if best_golden_path in golden_files else []
    golden_files_sorted += [f for f in golden_files if f != best_golden_path]
    golden_rois = [cv2.imread(f) for f in golden_files_sorted]
    
    match_found = False
    best_ai_similarity = 0
    best_golden_img = None
    matched_golden_path = None
    best_matching_golden_path = None
    feat2 = extract_features_from_array(crop2_normalized, feature_method=feature_method)
    
    print(f"DEBUG: ROI {idx} - Processing {len(golden_files_sorted)} golden images")
    
    # First pass: Try to find a match with the best golden image
    if golden_files_sorted:
        first_golden_path = golden_files_sorted[0]
        first_golden = golden_rois[0] if golden_rois else None
        
        if first_golden is not None:
            if first_golden.shape != crop2_normalized.shape:
                first_golden_resized = cv2.resize(first_golden, (crop2_normalized.shape[1], crop2_normalized.shape[0]))
            else:
                first_golden_resized = first_golden
            first_golden_normalized = normalize_illumination(first_golden_resized)
            feat1 = extract_features_from_array(first_golden_normalized, feature_method=feature_method)
            first_similarity = cosine_similarity(feat1, feat2)
            
            print(f"DEBUG: ROI {idx} - Best golden similarity: {first_similarity:.4f} (threshold: {ai_threshold})")
            
            # Update best similarity tracking
            best_ai_similarity = first_similarity
            best_golden_img = first_golden_resized
            matched_golden_path = first_golden_path
            
            # Check if best golden image matches
            if first_similarity + 1e-8 >= ai_threshold:
                match_found = True
                print(f"DEBUG: ROI {idx} - Match found with best golden image")
                result = "Match"
                color = (0, 255, 0)
                # Return format: (idx, type, captured_image, golden_image, coords, type_name, result, color, similarity, threshold)
                return (idx, 2, crop2, best_golden_img, (x1, y1, x2, y2), "Compare", result, color, best_ai_similarity, ai_threshold)
    
    # Second pass: If best golden doesn't match, try other golden images
    if not match_found and len(golden_files_sorted) > 1:
        print(f"DEBUG: ROI {idx} - Best golden didn't match, trying {len(golden_files_sorted)-1} other golden images")
        
        for golden, golden_path in zip(golden_rois[1:], golden_files_sorted[1:]):
            if golden is None:
                continue
                
            if golden.shape != crop2_normalized.shape:
                golden_resized = cv2.resize(golden, (crop2_normalized.shape[1], crop2_normalized.shape[0]))
            else:
                golden_resized = golden
            golden_resized_normalized = normalize_illumination(golden_resized)
            feat1 = extract_features_from_array(golden_resized_normalized, feature_method=feature_method)
            ai_similarity = cosine_similarity(feat1, feat2)
            
            print(f"DEBUG: ROI {idx} - Alternative golden '{os.path.basename(golden_path)}' similarity: {ai_similarity:.4f}")
            
            # Track best similarity regardless of threshold
            if ai_similarity > best_ai_similarity:
                best_ai_similarity = ai_similarity
                best_golden_img = golden_resized
                matched_golden_path = golden_path
                best_matching_golden_path = golden_path
            
            # Check if this golden image matches above threshold
            if ai_similarity + 1e-8 >= ai_threshold:
                match_found = True
                best_golden_img = golden_resized
                best_ai_similarity = ai_similarity
                
                print(f"DEBUG: ROI {idx} - Match found with alternative golden '{os.path.basename(golden_path)}'")
                print(f"DEBUG: ROI {idx} - Promoting '{os.path.basename(golden_path)}' to best golden image")
                
                # Promote the matching golden image to best golden
                update_best_golden_image(idx, golden_path, product_name, ai_similarity)
                
                # Return PASS immediately - skip checking rest of golden samples
                result = "Match"
                color = (0, 255, 0)
                print(f"DEBUG: ROI {idx} - Final result: {result} (similarity: {best_ai_similarity:.4f})")
                return (idx, 2, crop2, best_golden_img, (x1, y1, x2, y2), "Compare", result, color, best_ai_similarity, ai_threshold)
    
    # If we reach here, no golden sample matched the threshold - return FAIL
    result = "Different"
    color = (0, 0, 255)
    
    print(f"DEBUG: ROI {idx} - No golden sample matched threshold")
    print(f"DEBUG: ROI {idx} - Final result: {result} (best similarity: {best_ai_similarity:.4f}, threshold: {ai_threshold})")
    # Return format: (idx, type, captured_image, golden_image, coords, type_name, result, color, similarity, threshold)
    return (idx, 2, crop2, best_golden_img, (x1, y1, x2, y2), "Compare", result, color, best_ai_similarity, ai_threshold)

def get_rois():
    """Get the current ROI list."""
    return ROIS

def set_rois(new_rois):
    """Set the ROI list."""
    global ROIS
    ROIS = new_rois.copy() if new_rois else []
