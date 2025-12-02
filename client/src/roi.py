"""
ROI (Region of Interest) management and processing functionality.
"""

import os
import json
import glob
import cv2
import time
from collections import defaultdict

from src.config import get_config_filename, get_golden_roi_dir, FOCUS_SETTLE_DELAY
from src.ai import extract_features_from_array, cosine_similarity, normalize_illumination
from src.barcode import process_barcode_roi
from src.ocr import process_ocr_roi

# Global ROI list
ROIS = []

def normalize_roi(r):
    """Normalize ROI tuple to always include all required fields (Updated October 3, 2025 - added is_device_barcode)."""
    # (idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location, sample_text, is_device_barcode)
    if len(r) == 11:
        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location, sample_text, is_device_barcode = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        is_device_barcode_val = bool(is_device_barcode) if is_device_barcode is not None else True
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure_time), ai_threshold_val, str(feature_method), int(rotation), int(device_location), str(sample_text) if sample_text is not None else None, is_device_barcode_val)
    elif len(r) == 10:
        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location, sample_text = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        # For backward compatibility, default is_device_barcode to True for barcode ROIs
        is_barcode = int(typ) == 1 or str(feature_method).lower() == 'barcode'
        is_device_barcode_val = True if is_barcode else False
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure_time), ai_threshold_val, str(feature_method), int(rotation), int(device_location), str(sample_text) if sample_text is not None else None, is_device_barcode_val)
    elif len(r) == 9:
        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        sample_text = None  # Default for backward compatibility
        is_barcode = int(typ) == 1 or str(feature_method).lower() == 'barcode'
        is_device_barcode_val = True if is_barcode else False
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure_time), ai_threshold_val, str(feature_method), int(rotation), int(device_location), sample_text, is_device_barcode_val)
    elif len(r) == 8:
        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        device_location = 1  # Default to device location 1
        sample_text = None  # Default for backward compatibility
        is_barcode = int(typ) == 1 or str(feature_method).lower() == 'barcode'
        is_device_barcode_val = True if is_barcode else False
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure_time), ai_threshold_val, str(feature_method), int(rotation), int(device_location), sample_text, is_device_barcode_val)
    elif len(r) == 7:
        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method = r
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        sample_text = None  # Default for backward compatibility
        is_barcode = int(typ) == 1 or str(feature_method).lower() == 'barcode'
        is_device_barcode_val = True if is_barcode else False
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure_time), ai_threshold_val, str(feature_method), int(rotation), int(device_location), sample_text, is_device_barcode_val)
    elif len(r) == 6:
        idx, typ, coords, focus, exposure_time, ai_threshold = r
        feature_method = "mobilenet" if int(typ) == 2 else "opencv"
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else None
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        sample_text = None  # Default for backward compatibility
        is_barcode = int(typ) == 1
        is_device_barcode_val = True if is_barcode else False
        return (int(idx), int(typ), tuple(coords), int(focus), int(exposure_time), ai_threshold_val, feature_method, int(rotation), int(device_location), sample_text, is_device_barcode_val)
    elif len(r) == 5:
        # Legacy format: add defaults for new fields
        idx, typ, coords, focus, ai_threshold = r
        exposure_time = 3000
        feature_method = "mobilenet" if int(typ) == 2 else "opencv"
        ai_threshold_val = float(ai_threshold) if ai_threshold is not None else (0.9 if int(typ) == 2 else None)
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        sample_text = None  # Default for backward compatibility
        is_barcode = int(typ) == 1
        is_device_barcode_val = True if is_barcode else False
        return (int(idx), int(typ), tuple(coords), int(focus), exposure_time, ai_threshold_val, feature_method, int(rotation), int(device_location), sample_text, is_device_barcode_val)
    elif len(r) == 4:
        # Legacy format: add defaults for new fields
        idx, typ, coords, focus = r
        exposure_time = 3000
        ai_threshold = 0.9 if int(typ) == 2 else None
        feature_method = "mobilenet" if int(typ) == 2 else "opencv"
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        sample_text = None  # Default for backward compatibility
        is_barcode = int(typ) == 1
        is_device_barcode_val = True if is_barcode else False
        return (int(idx), int(typ), tuple(coords), int(focus), exposure_time, ai_threshold, feature_method, int(rotation), int(device_location), sample_text, is_device_barcode_val)
    elif len(r) == 3:
        # Legacy format: add defaults for new fields
        idx, typ, coords = r
        focus = 305
        exposure_time = 3000
        ai_threshold = 0.9 if int(typ) == 2 else None
        feature_method = "mobilenet" if int(typ) == 2 else "opencv"
        rotation = 0  # Default rotation
        device_location = 1  # Default to device location 1
        sample_text = None  # Default for backward compatibility
        is_barcode = int(typ) == 1
        is_device_barcode_val = True if is_barcode else False
        return (int(idx), int(typ), tuple(coords), focus, exposure_time, ai_threshold, feature_method, int(rotation), int(device_location), sample_text, is_device_barcode_val)
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
        # Save all ROI attributes, including exposure_time and ai_threshold
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
                    ROIS = [normalize_roi(tuple(r)) for r in loaded if normalize_roi(tuple(r)) is not None]
            
            # Set default focus/exposure to first ROI group and update camera
            group_dict = defaultdict(list)
            
            for roi in ROIS:
                focus = None
                exposure_time = None
                if roi is None:
                    continue
                if roi[1] == 2:
                    # AI comparison ROI - unpack all fields including device location and is_device_barcode
                    if len(roi) >= 11:
                        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location, sample_text, is_device_barcode = roi[:11]
                    elif len(roi) >= 10:
                        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location, sample_text = roi[:10]
                    elif len(roi) >= 9:
                        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location = roi[:9]
                    elif len(roi) >= 7:
                        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method = roi[:7]
                    else:
                        idx, typ, coords, focus, exposure_time = roi[:5]
                elif roi[1] == 1:
                    # Barcode ROI - unpack all fields including device location and is_device_barcode
                    if len(roi) >= 11:
                        idx, typ, coords, focus, exposure_time, _, _, _, device_location, sample_text, is_device_barcode = roi[:11]
                    elif len(roi) >= 10:
                        idx, typ, coords, focus, exposure_time, _, _, _, device_location, sample_text = roi[:10]
                    elif len(roi) >= 9:
                        idx, typ, coords, focus, exposure_time, _, _, _, device_location = roi[:9]
                    elif len(roi) >= 7:
                        idx, typ, coords, focus, exposure_time, _, _ = roi[:7]
                    else:
                        idx, typ, coords, focus, exposure_time = roi[:5]
                    feature_method = "barcode"
                    ai_threshold = None
                elif roi[1] == 3:
                    # OCR ROI - unpack all fields including device location, sample_text, and is_device_barcode
                    if len(roi) >= 11:
                        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location, sample_text, is_device_barcode = roi[:11]
                    elif len(roi) >= 10:
                        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location, sample_text = roi[:10]
                    elif len(roi) >= 9:
                        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation, device_location = roi[:9]
                        sample_text = None
                    elif len(roi) >= 8:
                        idx, typ, coords, focus, exposure_time, ai_threshold, feature_method, rotation = roi[:8]
                        sample_text = None
                    else:
                        idx, typ, coords, focus, exposure_time, _, _ = roi[:7]
                        sample_text = None
                group_dict[(focus, exposure_time)].append(roi)
            
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

def update_best_golden_image(idx, best_golden_path, product_name):
    """Rename best golden image to 'best_golden.jpg' and others to 'original_*.jpg' for this ROI."""
    print(f"🔄 Updating best golden image for ROI {idx}...")
    print(f"   Promoting: {os.path.basename(best_golden_path)}")
    
    # Get the absolute path to the project root
    # This file is in src/roi.py, so project root is one level up from src
    current_file_dir = os.path.dirname(os.path.abspath(__file__))  # src directory
    project_root = os.path.dirname(current_file_dir)  # project root
    roi_dir = os.path.join(project_root, get_golden_roi_dir(product_name, idx))
    
    # Rename current best_golden.jpg to original_*.jpg if it exists
    ts = int(time.time())
    current_best = os.path.join(roi_dir, "best_golden.jpg")
    if os.path.exists(current_best):
        backup_name = f"original_{ts}_old_best.jpg"
        backup_path = os.path.join(roi_dir, backup_name)
        os.rename(current_best, backup_path)
        print(f"   Backed up old best golden as: {backup_name}")
    
    # Rename the new best golden to best_golden.jpg
    if os.path.abspath(best_golden_path) != os.path.abspath(current_best):
        if os.path.exists(best_golden_path):
            os.rename(best_golden_path, current_best)
            print(f"   ✓ {os.path.basename(best_golden_path)} is now the best golden image")
        else:
            print(f"   ⚠️ Warning: Source file {best_golden_path} not found")
    
    # Clean up any duplicate original files with same timestamp
    for f in glob.glob(os.path.join(roi_dir, "*.jpg")):
        filename = os.path.basename(f)
        if filename.startswith("original_") and not filename.endswith("_old_best.jpg"):
            # Check if this is a duplicate that needs renaming
            if filename == f"original_{ts}.jpg":
                new_ts = ts + 1
                new_name = f"original_{new_ts}.jpg"
                new_path = os.path.join(roi_dir, new_name)
                if not os.path.exists(new_path):
                    os.rename(f, new_path)
    
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
                return (idx, 2, best_golden_img, crop2, (x1, y1, x2, y2), result, color, best_ai_similarity, ai_threshold)
    
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
                matched_golden_path = golden_path
                best_matching_golden_path = golden_path
                
                print(f"DEBUG: ROI {idx} - Match found with alternative golden '{os.path.basename(golden_path)}'")
                print(f"DEBUG: ROI {idx} - Promoting '{os.path.basename(golden_path)}' to best golden image")
                
                # Rename the matching golden image to become the new best golden
                update_best_golden_image(idx, golden_path, product_name)
                break
    
    # If no match found above threshold, use the best similarity we found
    if not match_found:
        if best_matching_golden_path and best_matching_golden_path != (golden_files_sorted[0] if golden_files_sorted else None):
            print(f"DEBUG: ROI {idx} - No threshold match, but best similarity {best_ai_similarity:.4f} from '{os.path.basename(best_matching_golden_path)}'")
            print(f"DEBUG: ROI {idx} - Promoting best matching golden '{os.path.basename(best_matching_golden_path)}' to best golden for future comparisons")
            # Even if no match, promote the best matching golden for future efficiency
            update_best_golden_image(idx, best_matching_golden_path, product_name)
    
    result = "Match" if match_found else "Different"
    color = (0, 255, 0) if match_found else (0, 0, 255)
    
    print(f"DEBUG: ROI {idx} - Final result: {result} (similarity: {best_ai_similarity:.4f})")
    return (idx, 2, best_golden_img, crop2, (x1, y1, x2, y2), result, color, best_ai_similarity, ai_threshold)

def get_rois():
    """Get the current ROI list."""
    return ROIS

def set_rois(new_rois):
    """Set the ROI list."""
    global ROIS
    ROIS = new_rois.copy() if new_rois else []
