# EasyOCR Accuracy Improvement Guide

**Date**: October 9, 2025  
**Current Status**: EasyOCR working with 95-99% accuracy on CPU  
**Goal**: Maximize OCR accuracy for PCB inspection

---

## Current Performance Baseline

- **Accuracy**: 95-99% on test cases
- **Speed**: 33ms average on CPU
- **Test Results**: 100% accuracy on simple text (PCB, R110, C123, etc.)

---

## 🎯 Top 10 Techniques to Improve EasyOCR Accuracy

### 1. **Image Preprocessing** ⭐⭐⭐⭐⭐ (MOST IMPORTANT)

Image quality is the #1 factor affecting OCR accuracy. Proper preprocessing can improve accuracy from 85% to 99%.

#### A. Grayscale Conversion

```python
import cv2

# Convert to grayscale for better contrast
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
```

#### B. Contrast Enhancement (CLAHE)

```python
# Adaptive histogram equalization
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(gray)
```

#### C. Denoising

```python
# Remove noise while preserving edges
denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
```

#### D. Thresholding (Binary Images)

```python
# Otsu's thresholding for automatic threshold selection
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Or adaptive thresholding for varying lighting
binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                cv2.THRESH_BINARY, 11, 2)
```

#### E. Morphological Operations

```python
# Remove small noise
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
```

#### F. Sharpening

```python
# Enhance edges
kernel = np.array([[-1,-1,-1],
                   [-1, 9,-1],
                   [-1,-1,-1]])
sharpened = cv2.filter2D(image, -1, kernel)
```

#### **Complete Preprocessing Pipeline:**

```python
def preprocess_for_ocr(image):
    """
    Complete preprocessing pipeline for maximum OCR accuracy
    """
    # 1. Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # 2. Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10)
    
    # 3. Enhance contrast (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # 4. Sharpen
    kernel = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # 5. Binary threshold
    _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 6. Remove small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return cleaned
```

**Expected improvement**: 5-15% accuracy increase

---

### 2. **EasyOCR Parameter Tuning** ⭐⭐⭐⭐

EasyOCR has many parameters that can be adjusted for better accuracy.

#### A. Basic Parameters

```python
reader = easyocr.Reader(['en'], gpu=True)

# Most important parameters for accuracy
results = reader.readtext(
    image,
    detail=1,                    # Get confidence scores
    paragraph=False,             # Detect individual words
    min_size=10,                 # Minimum text size (pixels)
    text_threshold=0.7,          # Text detection confidence (0-1)
    low_text=0.4,                # Low text threshold
    link_threshold=0.4,          # Link threshold
    canvas_size=2560,            # Maximum image dimension
    mag_ratio=1.0,               # Magnification ratio
    slope_ths=0.1,               # Slope threshold for text lines
    ycenter_ths=0.5,             # Y-center threshold
    height_ths=0.5,              # Height threshold
    width_ths=0.5,               # Width threshold
    add_margin=0.1,              # Margin around detected text (0-1)
    contrast_ths=0.1,            # Contrast threshold
    adjust_contrast=0.5,         # Contrast adjustment
)
```

#### B. Recommended Settings for PCB Text

```python
def ocr_pcb_text(image):
    """
    Optimized settings for PCB component labels
    """
    results = reader.readtext(
        image,
        detail=1,
        paragraph=False,         # Individual components
        min_size=5,              # Small text on PCBs
        text_threshold=0.6,      # Lower threshold for small text
        low_text=0.3,
        link_threshold=0.3,
        canvas_size=3840,        # High resolution support
        mag_ratio=1.5,           # Magnify small text
        add_margin=0.15,         # More margin for small characters
    )
    
    # Filter by confidence
    filtered = [r for r in results if r[2] > 0.5]  # Confidence > 50%
    
    return filtered
```

**Expected improvement**: 3-8% accuracy increase

---

### 3. **Image Resolution Optimization** ⭐⭐⭐⭐

Text size matters! EasyOCR works best with text height of 20-100 pixels.

#### A. Check Text Size

```python
def check_text_size(roi_height, num_text_lines=1):
    """
    Calculate approximate text height
    """
    text_height = roi_height / num_text_lines * 0.7  # Rough estimate
    
    if text_height < 20:
        return "TOO SMALL - resize needed"
    elif text_height > 100:
        return "TOO LARGE - might reduce accuracy"
    else:
        return "OPTIMAL"
```

#### B. Upscale Small Text

```python
def resize_for_ocr(image, target_text_height=40):
    """
    Resize image to optimal text height
    """
    h, w = image.shape[:2]
    
    # If text is too small, upscale
    if h < 40:
        scale = target_text_height / h
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Use INTER_CUBIC for upscaling (better quality)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        return resized
    
    return image
```

#### C. Complete Resolution Pipeline

```python
def optimize_resolution_for_ocr(image):
    """
    Optimize image resolution for OCR
    """
    h, w = image.shape[:2]
    
    # Target: text height 30-50 pixels
    if h < 30:
        scale = 40 / h
        new_size = (int(w * scale), int(h * scale))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)
    elif h > 200:
        scale = 100 / h
        new_size = (int(w * scale), int(h * scale))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    
    return image
```

**Expected improvement**: 5-10% accuracy increase for small text

---

### 4. **Text Rotation Correction** ⭐⭐⭐

Already implemented in your system, but ensure it's working correctly.

```python
def rotate_image(image, angle):
    """
    Rotate image for text alignment
    """
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), 
                             flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
    
    return rotated
```

**Expected improvement**: 10-20% for rotated text

---

### 5. **Character Whitelist/Allowlist** ⭐⭐⭐⭐

Limit character set to expected characters for higher accuracy.

```python
# For component labels (alphanumeric + common symbols)
reader = easyocr.Reader(['en'], gpu=False)

# Define allowlist
allowlist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.'

results = reader.readtext(
    image,
    allowlist=allowlist,  # Only these characters
    detail=1
)
```

#### Common Whitelists

```python
# Component references (R110, C123, etc.)
COMPONENT_CHARS = 'RLCDFQJKU0123456789'

# Product codes (alphanumeric)
PRODUCT_CODE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'

# Numbers only
NUMBERS_ONLY = '0123456789'

# Alphanumeric with common symbols
ALPHANUMERIC_SYMBOLS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_./\\'
```

**Expected improvement**: 5-15% accuracy increase

---

### 6. **Language Model Selection** ⭐⭐⭐

Use the right language model for your text.

```python
# Single language (fastest, most accurate)
reader = easyocr.Reader(['en'], gpu=False)

# Multiple languages (slower, may reduce accuracy)
reader = easyocr.Reader(['en', 'fr', 'de'], gpu=False)

# For English-only text, use only 'en'
# For mixed languages, add only required languages
```

**Recommendation for PCB**: Use `['en']` only unless you need other languages.

**Expected improvement**: 2-5% accuracy increase

---

### 7. **Post-Processing Corrections** ⭐⭐⭐

Apply text corrections based on expected patterns.

```python
def correct_ocr_result(text, expected_pattern=None):
    """
    Apply common OCR error corrections
    """
    # Common OCR mistakes
    corrections = {
        '0': 'O',  # Zero vs O
        'O': '0',
        '1': 'I',  # One vs I
        'I': '1',
        '5': 'S',  # Five vs S
        'S': '5',
        '8': 'B',  # Eight vs B
        'B': '8',
    }
    
    # If expected pattern is known, apply smart corrections
    if expected_pattern == 'component':
        # Component labels: R110, C123 (letter + numbers)
        if len(text) > 1:
            # First char should be letter
            if text[0].isdigit():
                text = corrections.get(text[0], text[0]) + text[1:]
            # Rest should be numbers
            for i in range(1, len(text)):
                if not text[i].isdigit():
                    text = text[:i] + corrections.get(text[i], text[i]) + text[i+1:]
    
    return text

def validate_and_correct(text, expected_format):
    """
    Validate text against expected format
    """
    if expected_format == 'component':
        # Expected: Letter followed by numbers (R110, C123)
        import re
        pattern = r'^[RLCDFQJKU]\d+$'
        if re.match(pattern, text):
            return text, True
        else:
            # Try corrections
            corrected = correct_ocr_result(text, 'component')
            return corrected, re.match(pattern, corrected) is not None
    
    return text, True
```

**Expected improvement**: 3-8% accuracy increase

---

### 8. **Ensemble Methods** ⭐⭐⭐

Run OCR multiple times with different settings and combine results.

```python
def ensemble_ocr(image):
    """
    Run OCR with multiple configurations and vote
    """
    results = []
    
    # Method 1: Original image
    r1 = reader.readtext(image, detail=1)
    results.append(r1)
    
    # Method 2: Preprocessed image
    preprocessed = preprocess_for_ocr(image)
    r2 = reader.readtext(preprocessed, detail=1)
    results.append(r2)
    
    # Method 3: Different parameters
    r3 = reader.readtext(image, text_threshold=0.6, detail=1)
    results.append(r3)
    
    # Combine results by voting
    from collections import Counter
    all_texts = [r[1] for result in results for r in result]
    if all_texts:
        most_common = Counter(all_texts).most_common(1)[0][0]
        return most_common
    
    return ""
```

**Expected improvement**: 2-5% accuracy increase (at cost of 3x processing time)

---

### 9. **ROI Expansion** ⭐⭐

Add margin around text for better detection.

```python
def expand_roi(image, roi_coords, margin_percent=0.1):
    """
    Expand ROI to include more context
    """
    x1, y1, x2, y2 = roi_coords
    h, w = image.shape[:2]
    
    width = x2 - x1
    height = y2 - y1
    
    margin_w = int(width * margin_percent)
    margin_h = int(height * margin_percent)
    
    # Expand with bounds checking
    new_x1 = max(0, x1 - margin_w)
    new_y1 = max(0, y1 - margin_h)
    new_x2 = min(w, x2 + margin_w)
    new_y2 = min(h, y2 + margin_h)
    
    return new_x1, new_y1, new_x2, new_y2
```

**Expected improvement**: 2-5% accuracy increase

---

### 10. **GPU Acceleration** ⭐⭐

When available, GPU provides same accuracy but faster (allows more preprocessing).

```python
# Check GPU availability
import torch
gpu_available = torch.cuda.is_available()

reader = easyocr.Reader(['en'], gpu=gpu_available)
```

**Expected improvement**: 0% accuracy (same model), but 2-6x faster

---

## 🔧 Implementation Plan for Visual AOI Server

### Phase 1: Quick Wins (1-2 hours)

#### 1. Add Image Preprocessing

Modify `src/ocr.py` to add preprocessing:

```python
def preprocess_ocr_image(image):
    """
    Preprocess image for better OCR accuracy
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10)
    
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # Binary threshold
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

def process_ocr_roi(image, x1, y1, x2, y2, idx, rotation=0, expected_text=None):
    """
    Enhanced OCR processing with preprocessing
    """
    # ... existing code ...
    
    # NEW: Preprocess before OCR
    preprocessed = preprocess_ocr_image(roi)
    
    # Run OCR
    results = easyocr_reader.readtext(preprocessed, detail=0)
    
    # ... rest of code ...
```

**Expected gain**: 5-10% accuracy improvement

---

#### 2. Add Character Whitelist

```python
# In process_ocr_roi()
if expected_text and expected_text[0] in 'RLCDFQJKU':
    # Component label - use restricted charset
    allowlist = 'RLCDFQJKU0123456789'
    results = easyocr_reader.readtext(preprocessed, allowlist=allowlist, detail=0)
else:
    # General text
    results = easyocr_reader.readtext(preprocessed, detail=0)
```

**Expected gain**: 3-5% accuracy improvement

---

#### 3. Add Resolution Optimization

```python
def optimize_roi_size(roi):
    """
    Resize ROI to optimal size for OCR
    """
    h, w = roi.shape[:2]
    
    # Target text height: 30-50 pixels
    if h < 30:
        scale = 40 / h
        new_size = (int(w * scale), int(h * scale))
        return cv2.resize(roi, new_size, interpolation=cv2.INTER_CUBIC)
    
    return roi

# In process_ocr_roi()
roi = optimize_roi_size(roi)
```

**Expected gain**: 5-10% for small text

---

### Phase 2: Advanced Features (4-8 hours)

#### 1. Parameter Tuning

Add OCR parameters to ROI config:

```json
{
  "idx": 4,
  "type": 3,
  "ocr_params": {
    "min_size": 5,
    "text_threshold": 0.6,
    "mag_ratio": 1.5
  }
}
```

#### 2. Post-Processing Corrections

Add validation and correction logic based on expected patterns.

#### 3. Multiple Preprocessing Modes

Test and select best preprocessing method per product.

---

## 📊 Expected Results

### Current Accuracy (Baseline)

- Simple text (PCB, R110): 100%
- Complex text: 95-99%
- Average: ~97%

### After Phase 1 Implementation

- Simple text: 100%
- Complex text: 98-100%
- Average: ~99%
- **Improvement**: +2-3%

### After Phase 2 Implementation

- Simple text: 100%
- Complex text: 99-100%
- Average: ~99.5%
- **Improvement**: +2-3% more

### Total Expected Improvement: 95-99% → 99-100%

---

## 🧪 Testing Plan

### 1. Create Test Dataset

```python
test_cases = [
    # Simple
    ("PCB", "PCB"),
    ("R110", "R110"),
    ("C123", "C123"),
    
    # Complex
    ("R110 C123", "R110 C123"),
    ("PCB-001-Rev2", "PCB-001-Rev2"),
    ("20003548", "20003548"),
    
    # Challenging
    ("O0O0O0", "O0O0O0"),  # O vs 0
    ("I1I1I1", "I1I1I1"),  # I vs 1
]
```

### 2. Benchmark Tests

```python
def benchmark_accuracy(preprocessing=False):
    """
    Test accuracy with/without improvements
    """
    correct = 0
    total = len(test_cases)
    
    for expected, text in test_cases:
        # Create test image
        img = create_test_image(text)
        
        # Apply preprocessing if enabled
        if preprocessing:
            img = preprocess_ocr_image(img)
        
        # Run OCR
        result = easyocr_reader.readtext(img, detail=0)
        detected = " ".join(result)
        
        if detected == expected:
            correct += 1
    
    accuracy = (correct / total) * 100
    return accuracy

# Test
baseline = benchmark_accuracy(preprocessing=False)
improved = benchmark_accuracy(preprocessing=True)

print(f"Baseline: {baseline}%")
print(f"Improved: {improved}%")
print(f"Gain: +{improved - baseline}%")
```

---

## 🎯 Recommendations

### For Your System (Priority Order)

1. **✅ Implement Image Preprocessing** (Phase 1.1)
   - Highest impact: 5-10% improvement
   - Moderate effort: 1-2 hours
   - Low risk: Can fallback to original if worse

2. **✅ Add Character Whitelist** (Phase 1.2)
   - Good impact: 3-5% improvement
   - Low effort: 30 minutes
   - No risk: Only restricts character set

3. **✅ Optimize ROI Resolution** (Phase 1.3)
   - Good impact: 5-10% for small text
   - Low effort: 30 minutes
   - Low risk: Only affects small text

4. **⚠️ Advanced Tuning** (Phase 2)
   - Medium impact: 2-3% additional
   - High effort: 4-8 hours
   - Consider only if Phase 1 is insufficient

---

## 📝 Implementation Checklist

- [ ] Create test dataset with current accuracy baseline
- [ ] Implement preprocessing function
- [ ] Add preprocessing to `process_ocr_roi()`
- [ ] Test accuracy improvement
- [ ] Add character whitelist support
- [ ] Test whitelist accuracy
- [ ] Add resolution optimization
- [ ] Test on real PCB images
- [ ] Measure performance impact (processing time)
- [ ] Update documentation
- [ ] Deploy to production

---

## ⚠️ Important Notes

1. **Speed vs Accuracy Tradeoff**: Preprocessing adds 5-10ms per ROI
2. **Test on Real Data**: Synthetic tests may not reflect real performance
3. **Gradual Rollout**: Test on one product before applying to all
4. **Fallback Option**: Keep original method as backup
5. **Monitor Performance**: Track accuracy and speed metrics

---

## 📚 References

- EasyOCR Documentation: <https://github.com/JaidedAI/EasyOCR>
- OpenCV Preprocessing: <https://docs.opencv.org/4.x/>
- OCR Best Practices: <https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html>
- Character Recognition: <https://arxiv.org/abs/1904.01906>

---

## Conclusion

**Can we improve EasyOCR accuracy?** ✅ **YES!**

**Expected improvement**: 95-99% → 99-100% accuracy

**Best approach**:

1. Start with image preprocessing (biggest impact)
2. Add character whitelist (easy win)
3. Optimize resolution (helps small text)
4. Test on real PCB images
5. Deploy gradually

**Effort**: 2-4 hours for Phase 1 (quick wins)

**Risk**: Low (can always fallback to current method)

**Next step**: Implement Phase 1.1 (preprocessing) and measure results
