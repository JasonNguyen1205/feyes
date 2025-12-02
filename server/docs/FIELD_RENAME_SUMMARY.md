# Field Rename: sample_text → expected_text

**Date:** October 6, 2025  
**Status:** ✅ Complete  
**Impact:** Global field name change across entire codebase

## Overview

Renamed the `sample_text` field to `expected_text` throughout the entire codebase for better clarity and semantic meaning. This affects ROI configurations, source code, tests, and documentation.

## Rationale

The term **"expected_text"** is more descriptive and accurately represents the field's purpose:

- **Old name:** `sample_text` - Could be confused with "example text" or "sample data"
- **New name:** `expected_text` - Clearly indicates this is the text we expect to validate against

This improves code readability and makes the validation logic more intuitive for developers and users.

## Changes Applied

### 1. Global Find-and-Replace

**Command executed:**

```bash
find . -type f \( -name "*.py" -o -name "*.json" -o -name "*.md" \) \
  ! -path "./.git/*" ! -path "./*/__pycache__/*" \
  -exec sed -i 's/sample_text/expected_text/g' {} +
```

### 2. Files Modified

| Category | Files Affected | Examples |
|----------|---------------|----------|
| **Source Code** | 3 files | `src/ocr.py`, `src/inspection.py`, `src/roi.py` |
| **Configuration** | 12+ files | All `rois_config_*.json` files |
| **Documentation** | 5+ files | `docs/OCR_*.md`, `.github/copilot-instructions.md` |
| **Tests** | 3 files | `tests/test_roi.py`, `tests/test_ocr.py`, etc. |
| **Server API** | 1 file | `server/simple_api_server.py` |
| **Scripts** | 1 file | `scripts/migrate_roi_config.py` |

**Total files affected:** 25+ files across the entire codebase

### 3. Key Code Changes

**src/ocr.py:**

```python
# Before
def process_ocr_roi(norm2, x1, y1, x2, y2, idx, rotation=0, sample_text=None):

# After
def process_ocr_roi(norm2, x1, y1, x2, y2, idx, rotation=0, expected_text=None):
```

**src/inspection.py:**

```python
# Before
sample_text = roi[9] if len(roi) > 9 else None
ocr_result = process_ocr_roi(img, x1, y1, x2, y2, roi_idx, rotation, sample_text)

# After
expected_text = roi[9] if len(roi) > 9 else None
ocr_result = process_ocr_roi(img, x1, y1, x2, y2, roi_idx, rotation, expected_text)
```

**Configuration files:**

```json
{
  "idx": 5,
  "type": 3,
  "expected_text": "HELLO"  // ← Renamed from sample_text
}
```

## ROI Field Structure

The 11-field ROI tuple structure remains unchanged, only the field name changed:

**Position 9 (zero-indexed):**

- **Old name:** `sample_text`
- **New name:** `expected_text`
- **Type:** `str | None`
- **Purpose:** Expected text for OCR validation (case-insensitive substring matching)

**Full ROI structure:**

```python
(idx, type, coords, focus, exposure, ai_threshold, feature_method, 
 rotation, device_location, expected_text, is_device_barcode)
#                         ↑ Position 9
```

## Validation

### ✅ Syntax Validation

```bash
python3 -m py_compile src/ocr.py src/inspection.py src/roi.py
# Result: ✓ No syntax errors
```

### ✅ Configuration Loading

```python
from src import roi as roi_module
roi_module.load_rois_from_config('20003548')
# Result: ✓ 6 ROIs loaded successfully
```

### ✅ OCR Logic Testing

```python
# Test 1: PASS case
result = (1, 3, img, None, coords, 'OCR', 'HELLO [PASS: Contains "HELLO"]', 0)
assert is_roi_passed(result) == True  # ✓ Passed

# Test 2: FAIL case  
result = (2, 3, img, None, coords, 'OCR', 'TEXT [FAIL: Expected "HELLO", detected "TEXT"]', 0)
assert is_roi_passed(result) == False  # ✓ Passed
```

### ✅ Server Startup

```bash
python3 server/simple_api_server.py --host 0.0.0.0 --port 5000
# Result: ✓ Server starts successfully
```

## API Impact

### Request Format (unchanged structure, new field name)

**ROI Configuration:**

```json
{
  "idx": 5,
  "type": 3,
  "coords": [100, 200, 300, 400],
  "focus": 305,
  "exposure": 1200,
  "ai_threshold": null,
  "feature_method": "opencv",
  "rotation": 0,
  "device_location": 1,
  "expected_text": "SERIAL123",  // ← Use this name
  "is_device_barcode": null
}
```

**API Response (unchanged):**

```json
{
  "roi_idx": 5,
  "roi_type": 3,
  "roi_type_name": "OCR",
  "result": "SERIAL123456 [PASS: Contains 'SERIAL123']",
  "passed": true
}
```

## Documentation Updates

All documentation updated to reflect the new field name:

1. **docs/OCR_PASS_FAIL_LOGIC.md**
   - All references to `sample_text` → `expected_text`
   - Code examples updated
   - Configuration examples updated

2. **docs/OCR_VALIDATION_UPDATE_SUMMARY.md**
   - Field name updated throughout
   - Examples updated

3. **.github/copilot-instructions.md**
   - ROI format documentation updated
   - Example configurations updated

4. **README.md**
   - ROI structure description updated

## Migration Notes

### For Existing Configurations

**Action Required:** ⚠️ **BREAKING CHANGE**

All existing `rois_config_*.json` files must use `expected_text` instead of `sample_text`.

**Migration completed automatically** for all files in the repository:

- 12+ product configurations updated
- All test configurations updated
- Shared/golden configurations updated

### For Client Applications

**Client-side changes required:**

1. **Configuration files:** Update field name from `sample_text` to `expected_text`
2. **Code references:** Update any code that accesses the field
3. **API calls:** Use `expected_text` in ROI configurations

**Example client-side update:**

```python
# Before
roi = {
    "idx": 5,
    "type": 3,
    "sample_text": "HELLO"  # Old field name
}

# After
roi = {
    "idx": 5,
    "type": 3,
    "expected_text": "HELLO"  # New field name
}
```

## Backward Compatibility

❌ **NOT backward compatible**

This is a **breaking change**. Old configurations using `sample_text` will not work.

**Reason:** The field name is used directly in:

- JSON configuration parsing
- ROI normalization
- API validation
- Function parameters

**Mitigation:** All repository configurations have been updated automatically. External clients must update their configurations.

## Rollback Procedure

If rollback is needed:

```bash
# Reverse the find-and-replace
find . -type f \( -name "*.py" -o -name "*.json" -o -name "*.md" \) \
  ! -path "./.git/*" ! -path "./*/__pycache__/*" \
  -exec sed -i 's/expected_text/sample_text/g' {} +

# Verify
python3 -m py_compile src/*.py
python3 server/simple_api_server.py --version
```

**Git rollback:**

```bash
git checkout HEAD -- .
```

## Benefits

1. ✅ **Clearer Semantics:** "expected" is more intuitive than "sample"
2. ✅ **Better Code Documentation:** Self-documenting field name
3. ✅ **Reduced Confusion:** Eliminates ambiguity about field purpose
4. ✅ **Consistent Terminology:** Aligns with validation terminology
5. ✅ **Improved Developer Experience:** More obvious what the field does

## Testing Checklist

- [x] Python syntax validation (no errors)
- [x] Configuration loading (6/6 ROIs loaded)
- [x] OCR validation logic (PASS/FAIL working)
- [x] Server startup (successful)
- [x] Field access in tuple position 9 (correct)
- [x] API documentation updated
- [x] All test files updated
- [x] Migration script updated

## Production Deployment

**Deployment Steps:**

1. **Update client configurations:**

   ```bash
   # On client machines, update config files
   sed -i 's/sample_text/expected_text/g' config/products/*/rois_config_*.json
   ```

2. **Deploy server update:**

   ```bash
   git pull origin master
   ./start_server.sh
   ```

3. **Verify client connectivity:**
   - Test inspection API calls
   - Verify OCR validation works
   - Check device results

**Downtime:** None (if clients updated before server deployment)

**Risk Level:** Medium (breaking change, but simple find-replace fix)

## Related Changes

This rename was part of the OCR validation logic update (October 6, 2025):

- Enhanced pass/fail validation
- Explicit PASS/FAIL tags
- Stricter validation rules

See also:

- `docs/OCR_PASS_FAIL_LOGIC.md`
- `docs/OCR_VALIDATION_UPDATE_SUMMARY.md`

---

**Rename Complete** ✅  
**All Files Updated** ✅  
**Validation Passed** ✅  
**Documentation Updated** ✅
