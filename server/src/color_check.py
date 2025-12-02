"""
Color checking module for Visual AOI system.
Supports checking if colors in ROI match defined color ranges.
"""
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def get_color_range_from_expected(rgb):
    """
    Get predefined color range based on expected RGB values.
    Uses standard color ranges for accurate color detection.
    
    Color Range Definitions:
    - Red:    RGB(170-255, 0-90, 0-90)
    - Green:  RGB(0-100, 170-255, 0-100)
    - Blue:   RGB(0-100, 0-100, 170-255)
    - Yellow: RGB(220-255, 220-255, 0-120)
    - Orange: RGB(210-255, 120-200, 0-80)
    - Purple: RGB(120-220, 0-100, 160-255)
    - Pink:   RGB(220-255, 120-200, 180-255)
    - Black:  RGB(0-50, 0-50, 0-50)
    - White:  RGB(230-255, 230-255, 230-255)
    - Gray:   RGB(80-200, 80-200, 80-200)
    - Brown:  RGB(120-200, 60-140, 0-80)
    - Cyan:   RGB(0-120, 180-255, 180-255)
    
    Args:
        rgb: [R, G, B] array - the expected color chosen by user
        
    Returns:
        Tuple: (color_name, lower_rgb, upper_rgb)
    """
    r, g, b = rgb
    
    # Define color ranges (min-max for each RGB channel)
    color_ranges = {
        'Black':  ([0, 0, 0],       [50, 50, 50]),
        'White':  ([230, 230, 230], [255, 255, 255]),
        'Gray':   ([80, 80, 80],    [200, 200, 200]),
        'Red':    ([170, 0, 0],     [255, 90, 90]),
        'Green':  ([0, 170, 0],     [100, 255, 100]),
        'Blue':   ([0, 0, 170],     [100, 100, 255]),
        'Yellow': ([220, 220, 0],   [255, 255, 120]),
        'Orange': ([210, 120, 0],   [255, 200, 80]),
        'Purple': ([120, 0, 160],   [220, 100, 255]),
        'Pink':   ([220, 120, 180], [255, 200, 255]),
        'Brown':  ([120, 60, 0],    [200, 140, 80]),
        'Cyan':   ([0, 180, 180],   [120, 255, 255])
    }
    
    # Find which color range the expected RGB falls into
    for color_name, (lower, upper) in color_ranges.items():
        # Check if expected color is within or close to this range
        # Allow some flexibility by checking if expected is near the midpoint
        mid_r = (lower[0] + upper[0]) / 2
        mid_g = (lower[1] + upper[1]) / 2
        mid_b = (lower[2] + upper[2]) / 2
        
        # Calculate distance from midpoint
        dist = ((r - mid_r)**2 + (g - mid_g)**2 + (b - mid_b)**2) ** 0.5
        
        # Also check if expected is within the range
        in_range = (lower[0] <= r <= upper[0] and 
                   lower[1] <= g <= upper[1] and 
                   lower[2] <= b <= upper[2])
        
        # If distance is small or within range, use this color
        if in_range or dist < 80:
            logger.info(f"Detected color '{color_name}' for expected RGB({r},{g},{b})")
            return (color_name, lower, upper)
    
    # If no match found, return custom range based on tolerance
    # This shouldn't happen with standard colors
    logger.warning(f"No standard color match for RGB({r},{g},{b}), using default tolerance")
    return (f"Custom RGB({r},{g},{b})", rgb, rgb)


def normalize_color_image(img):
    """
    Normalize color image to reduce lighting variations.
    Uses denoising to improve color detection accuracy.
    
    Args:
        img: Input BGR image
        
    Returns:
        Normalized BGR image
    """
    try:
        # Apply denoising to reduce noise while preserving color information
        # Using lower h values to preserve color information better
        normalized = cv2.fastNlMeansDenoisingColored(
            img, None, 
            h=5,              # Luminance filter strength (lower = preserve more detail)
            hColor=5,         # Color filter strength (lower = preserve more color info)
            templateWindowSize=7, 
            searchWindowSize=21
        )
        return normalized
    except Exception as e:
        logger.warning(f"Color normalization failed: {e}, using original image")
        return img


def process_color_roi(norm2, x1, y1, x2, y2, idx, color_ranges=None, expected_color=None, color_tolerance=None, min_pixel_percentage=None):
    """
    Process a color checking ROI.
    
    Supports two modes:
    1. Color ranges mode (legacy): Check against multiple color ranges with names
    2. Expected color mode (new): Check if pixels match expected_color within tolerance
    
    Color checking uses flexible range matching instead of exact color values:
    - Black: RGB(0,0,0) with tolerance 50 covers RGB(0-50, 0-50, 0-50)
    - White: RGB(255,255,255) with tolerance 30 covers RGB(225-255, 225-255, 225-255)
    
    Args:
        norm2: Input image (will be normalized for better color detection)
        x1, y1, x2, y2: ROI coordinates
        idx: ROI index
        color_ranges: List of color ranges to check against (legacy mode)
                     Format: [{'name': 'red', 'lower': [r,g,b], 'upper': [r,g,b], 'threshold': 50.0}, ...]
        expected_color: Expected RGB color array [r, g, b] (new mode)
        color_tolerance: Tolerance for color deviation (int, default 10)
        min_pixel_percentage: Minimum percentage of pixels that must match (float, default 5.0)
    
    Returns:
        Tuple: (idx, 4, roi_img, None, (x1,y1,x2,y2), "Color", result_dict)
        where result_dict contains:
            - 'passed': bool
            - 'detected_color': str (name of matched color or 'Unknown')
            - 'match_percentage': float (0-100)
            - 'dominant_color': [r, g, b]
            - 'expected_color': [r, g, b] (if using expected color mode)
            - 'color_tolerance': int (if using expected color mode)
            - 'min_pixel_percentage': float (if using expected color mode)
    """
    try:
        # Extract ROI
        roi = norm2[y1:y2, x1:x2].copy()
        
        if roi is None or roi.size == 0:
            logger.error(f"Color ROI {idx}: Invalid ROI extraction")
            return (idx, 4, None, None, (x1, y1, x2, y2), "Color", {
                'passed': False,
                'detected_color': 'Error',
                'match_percentage': 0.0,
                'dominant_color': [0, 0, 0],
                'error': 'Invalid ROI'
            })
        
        # Apply color normalization to reduce lighting variations
        roi_normalized = normalize_color_image(roi)
        
        # Calculate dominant color from normalized image (mean BGR values)
        mean_color = cv2.mean(roi_normalized)[:3]  # Get BGR values, ignore alpha
        dominant_color = [int(mean_color[2]), int(mean_color[1]), int(mean_color[0])]  # Convert to RGB
        
        logger.info(f"Color ROI {idx}: Dominant color (RGB) = {dominant_color}")
        
        # Mode 1: Expected color mode (new approach with predefined color ranges)
        if expected_color is not None:
            min_percentage = min_pixel_percentage if min_pixel_percentage is not None else 5.0
            
            # Get predefined color range based on expected RGB
            # This maps user's expected color to standard color ranges
            # e.g., RGB(255,255,255) -> White range RGB(230-255, 230-255, 230-255)
            color_name, lower_rgb, upper_rgb = get_color_range_from_expected(expected_color)
            
            logger.info(f"Color ROI {idx}: Expected color mode - {color_name}")
            logger.info(f"Color ROI {idx}: User specified RGB{expected_color}")
            logger.info(f"Color ROI {idx}: Using range RGB({lower_rgb[0]}-{upper_rgb[0]}, {lower_rgb[1]}-{upper_rgb[1]}, {lower_rgb[2]}-{upper_rgb[2]})")
            logger.info(f"Color ROI {idx}: Min percentage required: {min_percentage}%")
            
            # Convert RGB ranges to BGR for OpenCV
            lower_bgr = np.array([lower_rgb[2], lower_rgb[1], lower_rgb[0]], dtype=np.uint8)
            upper_bgr = np.array([upper_rgb[2], upper_rgb[1], upper_rgb[0]], dtype=np.uint8)
            
            # Create mask for pixels within the predefined color range (using normalized image)
            mask = cv2.inRange(roi_normalized, lower_bgr, upper_bgr)
            
            # Calculate percentage of matching pixels
            match_pixels = cv2.countNonZero(mask)
            total_pixels = roi_normalized.shape[0] * roi_normalized.shape[1]
            match_percentage = (match_pixels / total_pixels) * 100.0
            
            # Determine pass/fail
            passed = match_percentage >= min_percentage
            
            logger.info(f"Color ROI {idx}: Match = {match_percentage:.2f}% (Required: {min_percentage}%), Passed: {passed}")
            
            return (idx, 4, roi, None, (x1, y1, x2, y2), "Color", {
                'passed': passed,
                'detected_color': color_name if passed else 'No Match',
                'match_percentage': match_percentage,
                'match_percentage_raw': match_percentage,
                'dominant_color': dominant_color,
                'expected_color': expected_color,
                'color_tolerance': f"Range: RGB({lower_rgb[0]}-{upper_rgb[0]}, {lower_rgb[1]}-{upper_rgb[1]}, {lower_rgb[2]}-{upper_rgb[2]})",
                'min_pixel_percentage': min_percentage,
                'threshold': min_percentage,  # For compatibility
                'color_range': f"{color_name}: RGB({lower_rgb[0]}-{upper_rgb[0]}, {lower_rgb[1]}-{upper_rgb[1]}, {lower_rgb[2]}-{upper_rgb[2]})"
            })
        
        # Mode 2: Color ranges mode (legacy approach)
        if not color_ranges or len(color_ranges) == 0:
            logger.warning(f"Color ROI {idx}: No color ranges defined, returning dominant color only")
            return (idx, 4, roi, None, (x1, y1, x2, y2), "Color", {
                'passed': True,  # Pass by default if no ranges defined
                'detected_color': 'Undefined',
                'match_percentage': 0.0,
                'dominant_color': dominant_color
            })
        
        # Check against defined color ranges
        # Group matches by color name to support multiple ranges per color
        color_matches = {}  # {color_name: {'total_percentage': float, 'ranges_matched': int, 'threshold': float}}
        
        for color_range in color_ranges:
            color_name = color_range.get('name', 'Unknown')
            lower = np.array(color_range.get('lower', [0, 0, 0]), dtype=np.uint8)
            upper = np.array(color_range.get('upper', [255, 255, 255]), dtype=np.uint8)
            threshold = color_range.get('threshold', 50.0)
            
            # Convert to BGR for OpenCV
            lower_bgr = np.array([lower[2], lower[1], lower[0]], dtype=np.uint8)
            upper_bgr = np.array([upper[2], upper[1], upper[0]], dtype=np.uint8)
            
            # Create mask for this color range (using normalized image)
            mask = cv2.inRange(roi_normalized, lower_bgr, upper_bgr)
            
            # Calculate percentage of pixels matching this color
            match_pixels = cv2.countNonZero(mask)
            total_pixels = roi.shape[0] * roi.shape[1]
            match_percentage = (match_pixels / total_pixels) * 100.0
            
            logger.info(f"Color ROI {idx}: Range '{color_name}' (range {color_range.get('lower')}-{color_range.get('upper')}) = {match_percentage:.2f}%")
            
            # Aggregate matches by color name (support multiple ranges per color)
            if color_name not in color_matches:
                color_matches[color_name] = {
                    'total_percentage': 0.0,
                    'ranges_matched': 0,
                    'threshold': threshold,
                    'best_range_percentage': 0.0
                }
            
            # Accumulate total percentage across all ranges for this color
            color_matches[color_name]['total_percentage'] += match_percentage
            color_matches[color_name]['ranges_matched'] += 1
            
            # Track best single range match
            if match_percentage > color_matches[color_name]['best_range_percentage']:
                color_matches[color_name]['best_range_percentage'] = match_percentage
        
        # Find the color with highest total percentage
        best_match = None
        best_match_percentage = 0.0
        threshold = 50.0  # Default threshold
        
        for color_name, stats in color_matches.items():
            # Use total percentage as the match score (sum of all ranges)
            total_percentage = stats['total_percentage']
            logger.info(f"Color ROI {idx}: '{color_name}' total match across {stats['ranges_matched']} range(s) = {total_percentage:.2f}%")
            
            if total_percentage > best_match_percentage:
                best_match_percentage = total_percentage
                best_match = color_name
                threshold = stats['threshold']
        
        # Cap match percentage at 100% for display (since multiple ranges can sum > 100%)
        display_percentage = min(best_match_percentage, 100.0)
        passed = best_match_percentage >= threshold
        
        result_dict = {
            'passed': passed,
            'detected_color': best_match if best_match else 'Unknown',
            'match_percentage': round(display_percentage, 2),
            'match_percentage_raw': round(best_match_percentage, 2),  # Actual sum (can be > 100%)
            'dominant_color': dominant_color,
            'threshold': threshold
        }
        
        logger.info(f"Color ROI {idx}: Result = {result_dict}")
        
        return (idx, 4, roi, None, (x1, y1, x2, y2), "Color", result_dict)
        
    except Exception as e:
        logger.error(f"Color ROI {idx} processing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return (idx, 4, None, None, (x1, y1, x2, y2), "Color", {
            'passed': False,
            'detected_color': 'Error',
            'match_percentage': 0.0,
            'dominant_color': [0, 0, 0],
            'error': str(e)
        })


def hex_to_rgb(hex_color):
    """Convert hex color (#RRGGBB) to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]


def rgb_to_hex(r, g, b):
    """Convert RGB tuple to hex color (#RRGGBB)."""
    return f'#{r:02x}{g:02x}{b:02x}'
