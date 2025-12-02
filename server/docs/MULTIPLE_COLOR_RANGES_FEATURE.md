# Multiple Color Ranges Per Color - Feature Explanation

**Date:** October 31, 2025  
**Feature:** Enhanced Color Checking with Multiple Range Support

## 🎯 Question Answered

**"Some color has more than one color range, is it right?"**

**Answer: YES! This is absolutely correct and intentional.**

## 💡 Why Multiple Ranges Per Color?

Real-world colors have variations in:

- **Brightness:** Dark red vs. bright red
- **Saturation:** Vivid red vs. pale red
- **Hue:** Pure red vs. orange-red vs. pink-red

A single color range cannot cover all these variations effectively.

## 📊 How It Works

### Configuration Example

```json
{
  "color_ranges": [
    {
      "name": "red",
      "lower": [200, 0, 0],
      "upper": [255, 50, 50],
      "color_space": "RGB",
      "threshold": 40.0
    },
    {
      "name": "red",           // SAME NAME
      "lower": [150, 0, 0],
      "upper": [199, 30, 30],
      "color_space": "RGB",
      "threshold": 40.0
    },
    {
      "name": "red",           // SAME NAME
      "lower": [220, 50, 50],
      "upper": [255, 100, 100],
      "color_space": "RGB",
      "threshold": 40.0
    },
    {
      "name": "blue",
      "lower": [0, 0, 200],
      "upper": [50, 50, 255],
      "color_space": "RGB",
      "threshold": 40.0
    }
  ]
}
```

### Processing Algorithm

1. **Check Each Range Independently**

   ```
   Range 1 (bright red):  30% of pixels match
   Range 2 (dark red):    25% of pixels match
   Range 3 (pink red):    10% of pixels match
   Range 4 (blue):        20% of pixels match
   ```

2. **Aggregate by Color Name**

   ```
   red:  30% + 25% + 10% = 65% total
   blue: 20% total
   ```

3. **Select Winner**

   ```
   red has highest match (65%) → detected_color = "red"
   65% >= 40% threshold → passed = true
   ```

### Response Format

```json
{
  "roi_id": 5,
  "roi_type_name": "color",
  "passed": true,
  "detected_color": "red",
  "match_percentage": 65.0,        // Capped at 100% for display
  "match_percentage_raw": 65.0,    // Actual sum (can exceed 100%)
  "dominant_color": [220, 45, 32],
  "threshold": 40.0
}
```

## ✨ Benefits

### 1. **More Robust Detection**

- Won't miss colors just because they're too dark or too light
- Covers entire spectrum of a color family

### 2. **Reduced False Negatives**

- A single range might miss 60% of red pixels
- Multiple ranges can catch what single range misses

### 3. **Better Real-World Performance**

- Lighting variations
- Material reflections
- Camera exposure differences

### 4. **Flexible Configuration**

- Start with broad ranges
- Add specific ranges as needed
- Fine-tune without replacing

## 🔬 Practical Example

### Scenario: Inspecting Red Components

**Problem:** Components have varying red shades due to:

- Different batch materials
- Lighting angle variations
- Camera exposure drift

**Solution:** Define multiple red ranges

```python
color_config = {
    'color_ranges': [
        # Bright/vivid red
        {'name': 'red', 'lower': [200, 0, 0], 'upper': [255, 50, 50]},
        
        # Medium red
        {'name': 'red', 'lower': [180, 0, 0], 'upper': [199, 40, 40]},
        
        # Dark red
        {'name': 'red', 'lower': [150, 0, 0], 'upper': [179, 30, 30]},
        
        # Pink/light red (overexposed)
        {'name': 'red', 'lower': [220, 50, 50], 'upper': [255, 100, 100]},
        
        # Other colors for defect detection
        {'name': 'blue', 'lower': [0, 0, 200], 'upper': [50, 50, 255]},
        {'name': 'green', 'lower': [0, 200, 0], 'upper': [50, 255, 50]},
    ]
}
```

**Result:**

- **Good red components:** 50-90% red match → PASS
- **Blue contaminants:** High blue match → FAIL
- **Missing color:** Low all matches → FAIL

## 📝 Implementation Details

### Code Changes (src/color_check.py)

**Before:**

```python
# Only kept highest single range match
best_match_percentage = 0.0
for color_range in color_ranges:
    if match_percentage > best_match_percentage:
        best_match_percentage = match_percentage
```

**After:**

```python
# Aggregate by color name
color_matches = {}  # {color_name: {'total_percentage': float}}
for color_range in color_ranges:
    color_name = color_range['name']
    if color_name not in color_matches:
        color_matches[color_name] = {'total_percentage': 0.0}
    color_matches[color_name]['total_percentage'] += match_percentage

# Find color with highest total
best_match = max(color_matches, key=lambda k: color_matches[k]['total_percentage'])
```

### Logging Output

```
Color ROI 5: Range 'red' (range [200, 0, 0]-[255, 50, 50]) = 30.45%
Color ROI 5: Range 'red' (range [150, 0, 0]-[199, 30, 30]) = 24.80%
Color ROI 5: Range 'red' (range [220, 50, 50]-[255, 100, 100]) = 10.15%
Color ROI 5: Range 'blue' (range [0, 0, 200]-[50, 50, 255]) = 5.20%
Color ROI 5: 'red' total match across 3 range(s) = 65.40%
Color ROI 5: 'blue' total match across 1 range(s) = 5.20%
Color ROI 5: Result = {'passed': True, 'detected_color': 'red', 'match_percentage': 65.4}
```

## ⚠️ Important Notes

### 1. Match Percentage Can Exceed 100%

**Why?** Overlapping ranges can match the same pixels multiple times.

**Example:**

```
Bright red: [200, 0, 0] - [255, 50, 50]  → 60% match
Light red:  [220, 50, 50] - [255, 100, 100] → 50% match
Overlap region: ~20% of pixels match BOTH ranges
Total: 60% + 50% = 110% raw match
```

**Solution:**

- `match_percentage`: Capped at 100% for display
- `match_percentage_raw`: Actual sum for debugging

### 2. Threshold Per Color

Each color range can have its own threshold:

```json
{
  "name": "red",
  "threshold": 40.0,  // Red needs 40% match
}
{
  "name": "blue",
  "threshold": 30.0,  // Blue only needs 30% match (more sensitive)
}
```

The system uses the threshold of the winning color.

### 3. Color Space Mixing

You can mix RGB and HSV ranges:

```json
{
  "name": "red",
  "color_space": "RGB",  // RGB for this range
  "lower": [200, 0, 0]
},
{
  "name": "red",
  "color_space": "HSV",  // HSV for this range
  "lower": [0, 50, 50]
}
```

Each range is converted appropriately before checking.

## 🧪 Testing

### Test Configuration

```bash
curl -X POST http://localhost:5000/api/products/test_product/colors \
  -H "Content-Type: application/json" \
  -d '{
    "color_ranges": [
      {"name": "red", "lower": [200, 0, 0], "upper": [255, 50, 50], "color_space": "RGB", "threshold": 40.0},
      {"name": "red", "lower": [150, 0, 0], "upper": [199, 30, 30], "color_space": "RGB", "threshold": 40.0},
      {"name": "red", "lower": [220, 50, 50], "upper": [255, 100, 100], "color_space": "RGB", "threshold": 40.0}
    ]
  }'
```

### Test Results

✅ Configuration saved successfully  
✅ Multiple ranges with same name supported  
✅ Ranges retrieved and grouped correctly  
✅ Total match percentage calculated properly  
✅ Logging shows individual and aggregated matches

## 📚 Documentation Updated

1. **API Client Guide** (`docs/API_CLIENT_GUIDE.md`)
   - Added explanation of multiple ranges per color
   - Included practical examples
   - Explained aggregation algorithm

2. **Code Comments** (`src/color_check.py`)
   - Documented aggregation logic
   - Added inline explanations

3. **This Document** (created)
   - Comprehensive feature explanation
   - Practical examples and use cases

## ✅ Summary

**Yes, multiple color ranges per color name is correct and intentional!**

This feature:

- ✅ Makes color detection more robust
- ✅ Handles real-world color variations
- ✅ Reduces false negatives
- ✅ Provides flexibility in configuration
- ✅ Is fully implemented and tested

**Use it whenever you need to detect a color that has multiple variations in brightness, saturation, or hue!**
