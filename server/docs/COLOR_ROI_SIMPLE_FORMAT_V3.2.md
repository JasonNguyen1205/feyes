# Color ROI Simple Format (v3.2) - November 2025

## Overview

Version 3.2 introduces a **simpler color checking format** for Color ROIs (Type 4) that eliminates the need to manually specify lower/upper bounds. Instead, you provide a target color and tolerance, and the system automatically creates the matching range.

## What's New in v3.2

### Simplified Color Checking

Instead of manually defining color ranges with lower/upper bounds:

**Old Way (v3.1 - still supported):**

```json
{
  "color_ranges": [
    {
      "name": "red",
      "lower": [200, 0, 0],
      "upper": [255, 50, 50],
      "color_space": "RGB",
      "threshold": 50.0
    }
  ]
}
```

**New Way (v3.2 - recommended):**

```json
{
  "expected_color": [255, 0, 0],
  "color_tolerance": 10,
  "min_pixel_percentage": 5.0
}
```

### How It Works

1. **expected_color** `[R, G, B]`: The target color you want to check
   - Example: `[255, 0, 0]` for pure red
   - RGB values from 0-255

2. **color_tolerance** (integer): How much deviation is allowed
   - Example: `10` means ±10 on each RGB channel
   - For `[255, 0, 0]` with tolerance `10`:
     - R: 245-255 ✅
     - G: 0-10 ✅
     - B: 0-10 ✅
   - Default: `10` if not specified

3. **min_pixel_percentage** (float): Minimum match percentage to pass
   - Example: `5.0` means at least 5% of pixels must match
   - Default: `5.0` if not specified

### ROI Configuration Examples

#### Object Format (Recommended)

```json
{
  "idx": 1,
  "type": 4,
  "coords": [100, 100, 300, 300],
  "focus": 305,
  "exposure": 1200,
  "rotation": 0,
  "device_location": 1,
  "expected_color": [255, 0, 0],
  "color_tolerance": 10,
  "min_pixel_percentage": 5.0
}
```

#### Array Format

```json
[
  1,                           // idx
  4,                           // type (Color)
  [100, 100, 300, 300],       // coords
  305,                         // focus
  1200,                        // exposure
  null,                        // ai_threshold (not used for color)
  null,                        // feature_method (not used for color)
  0,                           // rotation
  1,                           // device_location
  null,                        // expected_text (not used for color)
  null,                        // is_device_barcode (not used for color)
  {                            // color_config (Field 11)
    "expected_color": [255, 0, 0],
    "color_tolerance": 10,
    "min_pixel_percentage": 5.0
  }
]
```

## Common Use Cases

### 1. Red Component Check

Check for red LEDs, red indicators, red labels:

```json
{
  "expected_color": [255, 0, 0],
  "color_tolerance": 15,
  "min_pixel_percentage": 3.0
}
```

### 2. Green Component Check

Check for green status lights, green labels:

```json
{
  "expected_color": [0, 255, 0],
  "color_tolerance": 20,
  "min_pixel_percentage": 5.0
}
```

### 3. Blue Component Check

Check for blue indicators, blue markings:

```json
{
  "expected_color": [0, 0, 255],
  "color_tolerance": 15,
  "min_pixel_percentage": 4.0
}
```

### 4. White Component Check

Check for white labels, white text:

```json
{
  "expected_color": [255, 255, 255],
  "color_tolerance": 20,
  "min_pixel_percentage": 10.0
}
```

### 5. Black Component Check

Check for black text, black markings:

```json
{
  "expected_color": [0, 0, 0],
  "color_tolerance": 30,
  "min_pixel_percentage": 8.0
}
```

## API Integration

### Creating Sessions with Simple Color ROIs

```python
import requests

# Create session with simple color checking
response = requests.post('http://server:5000/api/session/create', json={
    'product_name': 'test_product',
    'client_info': {
        'client_id': 'station_1',
        'client_name': 'Assembly Line 1'
    },
    'rois_config': [
        {
            'idx': 1,
            'type': 4,  # Color type
            'coords': [100, 100, 300, 300],
            'focus': 305,
            'exposure': 1200,
            'rotation': 0,
            'device_location': 1,
            'expected_color': [255, 0, 0],      # Red
            'color_tolerance': 10,
            'min_pixel_percentage': 5.0
        }
    ]
})

session_id = response.json()['session_id']
```

### Inspection with Color ROIs

The inspection process is the same - just send the image:

```python
# Preferred: Send file path (99% smaller payload)
response = requests.post(
    f'http://server:5000/api/session/{session_id}/inspect',
    json={
        'image_filename': 'captured_image.jpg'
    }
)

# Legacy: Send Base64 (still supported)
import base64
with open('image.jpg', 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('utf-8')

response = requests.post(
    f'http://server:5000/api/session/{session_id}/inspect',
    json={'image': image_b64}
)
```

### Result Format

Color ROI results include match percentage and pass/fail status:

```json
{
  "success": true,
  "roi_results": [
    {
      "roi_idx": 1,
      "roi_type": 4,
      "roi_type_name": "Color",
      "result": "PASS",
      "details": {
        "match_percentage": 12.5,
        "threshold": 5.0,
        "expected_color": [255, 0, 0],
        "color_tolerance": 10,
        "matched_pixels": 2500,
        "total_pixels": 20000
      }
    }
  ],
  "overall_pass": true
}
```

## Legacy Format Support

The old `color_ranges` format from v3.1 is still fully supported:

```json
{
  "idx": 1,
  "type": 4,
  "coords": [100, 100, 300, 300],
  "focus": 305,
  "exposure": 1200,
  "rotation": 0,
  "device_location": 1,
  "color_ranges": [
    {
      "name": "red",
      "lower": [200, 0, 0],
      "upper": [255, 50, 50],
      "color_space": "RGB",
      "threshold": 50.0
    }
  ]
}
```

You can use either format in the same product configuration.

## Migration Guide

### From v3.1 to v3.2

If you have existing color ROIs with manual bounds, you can simplify them:

**Before (v3.1):**

```json
{
  "color_ranges": [
    {
      "name": "red",
      "lower": [245, 0, 0],
      "upper": [255, 10, 10],
      "color_space": "RGB",
      "threshold": 5.0
    }
  ]
}
```

**After (v3.2):**

```json
{
  "expected_color": [255, 0, 0],
  "color_tolerance": 10,
  "min_pixel_percentage": 5.0
}
```

### When to Use Each Format

**Use Simple Format (v3.2)** when:

- ✅ Checking for a single solid color
- ✅ You want automatic range calculation
- ✅ Basic color validation is sufficient

**Use Legacy Format (v3.1)** when:

- ✅ You need precise control over color ranges
- ✅ Color space conversions (HSV) are required
- ✅ Multiple color ranges for the same color (brightness variations)

## Best Practices

### 1. One ROI = One Color

Create separate ROIs for each color you need to check. Don't try to check multiple colors in one ROI.

**Good:**

```json
[
  {"idx": 1, "type": 4, "expected_color": [255, 0, 0], ...},  // Red ROI
  {"idx": 2, "type": 4, "expected_color": [0, 255, 0], ...}   // Green ROI
]
```

**Bad:**

```json
[
  {"idx": 1, "type": 4, "expected_color": [[255,0,0], [0,255,0]], ...}  // ❌ Won't work
]
```

### 2. Adjust Tolerance for Lighting

If lighting varies, increase tolerance:

- **Stable lighting**: tolerance 5-10
- **Variable lighting**: tolerance 15-25
- **Outdoor/sunlight**: tolerance 30+

### 3. Match Percentage Guidelines

- **Solid color components**: 5-15% typical
- **Labels with color**: 10-30% typical
- **Full colored areas**: 50%+ typical

### 4. Testing and Calibration

1. Start with defaults (tolerance=10, min_pixel_percentage=5.0)
2. Test with good samples - note actual match percentages
3. Adjust min_pixel_percentage to 80% of typical good sample
4. Test with bad samples to ensure they fail

## Technical Details

### Internal Processing

When you specify:

```json
{
  "expected_color": [255, 0, 0],
  "color_tolerance": 10
}
```

The system internally creates:

```python
# RGB to BGR conversion (OpenCV uses BGR)
expected_bgr = [0, 0, 255]

# Create bounds with tolerance
lower_bound = [0-10, 0-10, 255-10] = [0, 0, 245]
upper_bound = [0+10, 0+10, 255+10] = [10, 10, 255]

# Apply bounds
mask = cv2.inRange(roi_image, lower_bound, upper_bound)
match_percentage = (matching_pixels / total_pixels) * 100

# Compare to threshold
pass = match_percentage >= min_pixel_percentage
```

### Performance

- **Simple format**: Identical performance to legacy format
- **RGB color space only**: Fast direct comparison
- **No HSV conversion**: Simpler and faster
- **Parallel processing**: All ROIs processed simultaneously

## API Schema Version

Updated schema endpoint returns v3.2 format:

```bash
curl http://server:5000/api/schema/roi
```

```json
{
  "version": "3.2",
  "format": "12-field",
  "updated": "2025-11-01",
  "fields": [
    {
      "index": 11,
      "name": "color_config",
      "formats": {
        "simple": {
          "fields": {
            "expected_color": "array[int, int, int]",
            "color_tolerance": "int (default: 10)",
            "min_pixel_percentage": "float (default: 5.0)"
          }
        }
      }
    }
  ]
}
```

## Troubleshooting

### Issue: Color ROI always fails

**Solution:**

- Check that expected_color is in RGB format (not BGR)
- Increase tolerance if lighting varies
- Lower min_pixel_percentage threshold
- Verify ROI coordinates cover the colored area

### Issue: Color ROI always passes (even for wrong colors)

**Solution:**

- Increase min_pixel_percentage threshold
- Decrease tolerance for more precise matching
- Verify expected_color is correct RGB value
- Check ROI doesn't include too much background

### Issue: Results inconsistent across captures

**Solution:**

- Increase color_tolerance to handle lighting variations
- Ensure consistent lighting conditions
- Consider using legacy format with HSV color space for better stability

## Examples Repository

See `/config/products/test_color_demo/` for complete examples:

- Simple red/green/blue checks
- White label validation
- Black text verification
- Multi-device color configurations

## Related Documentation

- [Color ROI Type 4 Complete Documentation](./COLOR_ROI_TYPE_4_COMPLETE_DOCUMENTATION.md)
- [Color ROI Embedded Config (v3.1)](./COLOR_ROI_EMBEDDED_CONFIG.md)
- [ROI Definition Specification](./ROI_DEFINITION_SPECIFICATION.md)
- [Client-Server Architecture](./CLIENT_SERVER_ARCHITECTURE.md)

## Support

For issues or questions:

1. Check tolerance and threshold values
2. Review actual match percentages in inspection results
3. Test with both good and bad samples
4. Consider legacy format if more control needed
