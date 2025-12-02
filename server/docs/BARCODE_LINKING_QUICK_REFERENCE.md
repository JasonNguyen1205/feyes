# Barcode Linking - Quick Reference

**Feature**: External API integration for device barcode validation  
**Status**: ✅ **Production Ready**  
**Date**: October 20, 2025

---

## 📋 What It Does

When a device barcode is scanned during inspection, the system automatically:

1. Calls external API to validate/link the barcode
2. Uses the linked data as the final device barcode
3. Falls back to original barcode if API unavailable

---

## 🚀 Usage

### No Code Changes Required

The barcode linking is **automatically enabled** and works transparently during inspection. No changes needed to existing client code.

### API Flow

```
Device Barcode Detected → Call External API → Use Linked Data
         ↓                        ↓                    ↓
  "ABC-123-456"          POST to API          "ABC-123-456"
                  (or fallback if failed)
```

---

## ⚙️ Configuration

### Default Settings

- **API URL**: `http://fvn-s-web01:5000/api/ProcessLock/FA/GetLinkData`
- **Timeout**: 3 seconds
- **Enabled**: Yes
- **Fallback**: Original barcode if API fails

### Change API URL

```python
from src.barcode_linking import set_barcode_link_api_url
set_barcode_link_api_url("http://10.100.27.100:5000/api/ProcessLock/FA/GetLinkData")
```

### Change Timeout

```python
from src.barcode_linking import set_barcode_link_timeout
set_barcode_link_timeout(1)  # 1 second
```

### Disable Linking

```python
from src.barcode_linking import set_barcode_link_enabled
set_barcode_link_enabled(False)
```

---

## 🧪 Testing

### Test Linking Functionality

```bash
cd /home/jason_nguyen/visual-aoi-server
python3 tests/test_barcode_linking.py
```

### Test with curl

```bash
curl -X POST "http://fvn-s-web01:5000/api/ProcessLock/FA/GetLinkData" \
  -H "Content-Type: application/json" \
  -d '"20003548-0000003-1019720-101"'
```

Expected output:

```
20003548-0000003-1019720-101
```

---

## 📊 Logging

### Success

```
INFO - [Priority 0] Using linked barcode for device 1: ABC123 -> XYZ789
```

### Fallback

```
WARNING - Barcode link API timeout after 3s for barcode: ABC123
INFO - [Priority 0] Using device main barcode ROI for device 1: ABC123 (linking failed)
```

---

## 🔍 Troubleshooting

### Problem: Linking Always Fails

**Check 1**: Verify API is reachable

```bash
curl http://fvn-s-web01:5000/api/ProcessLock/FA/GetLinkData
```

**Check 2**: Check network connectivity

```bash
ping fvn-s-web01
```

**Solution**: Use IP address instead of hostname

```python
set_barcode_link_api_url("http://10.100.27.100:5000/api/ProcessLock/FA/GetLinkData")
```

---

### Problem: Slow Performance

**Cause**: API timeout too long (3s default)

**Solution**: Reduce timeout

```python
set_barcode_link_timeout(1)  # 1 second
```

---

## 📁 Files

| File | Description |
|------|-------------|
| `src/barcode_linking.py` | Core linking functionality |
| `server/simple_api_server.py` | Integration (lines 800-836) |
| `tests/test_barcode_linking.py` | Test suite |
| `docs/BARCODE_LINKING_INTEGRATION.md` | Full documentation |
| `docs/BARCODE_LINKING_QUICK_REFERENCE.md` | This file |

---

## 🔗 When Linking Happens

### Priority 0: Device Main Barcode ROIs

- ROIs with `is_device_barcode=True`
- **Always linked** if detected

### Priority 1: Any Barcode ROI

- Any barcode ROI when device barcode not yet set
- **Always linked** if detected

### Priority 2 & 3: Manual/Legacy Barcodes

- Manual barcodes from client
- Legacy single barcode field
- **NOT linked** (used as-is)

---

## ✅ Benefits

✅ **Automatic**: No client code changes required  
✅ **Reliable**: Graceful fallback if API unavailable  
✅ **Fast**: 3s timeout (configurable to 1s)  
✅ **Traceable**: All linking logged  
✅ **Configurable**: API URL, timeout, enable/disable  

---

## 📚 Related Documentation

- **Full Documentation**: [BARCODE_LINKING_INTEGRATION.md](BARCODE_LINKING_INTEGRATION.md)
- **Architecture**: [copilot-instructions.md](../.github/copilot-instructions.md)
- **API Docs**: [SWAGGER_DOCUMENTATION.md](SWAGGER_DOCUMENTATION.md)

---

**Last Updated**: October 20, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅
