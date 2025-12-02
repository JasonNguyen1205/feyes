# Barcode Linking - Client Integration Guide

**Date**: October 20, 2025  
**Target**: Client Application Developers  
**API Version**: 1.1

---

## 🎯 Overview

The Visual AOI Server now automatically links device barcodes through an external API. When your client sends an inspection request, the server will:

1. Scan the barcode ROI (e.g., `"1897848 S/N: 65514 3969 1006 V"`)
2. Call external API to get linked barcode (e.g., `"1897848-0001555-118714"`)
3. Return the **linked barcode** in the `device_summaries` field

**No client code changes required!** Just read the correct field.

---

## 📊 API Response Structure

### Example Inspection Response

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "product_name": "20003548",
  "timestamp": "2025-10-20T14:30:00",
  
  "roi_results": [
    {
      "roi_idx": 3,
      "roi_type": "Barcode",
      "result": "Pass",
      "barcode_values": ["1897848 S/N: 65514 3969 1006 V"],
      "device_location": 1,
      "coordinates": [100, 100, 200, 150]
    }
  ],
  
  "device_summaries": {
    "1": {
      "device_id": 1,
      "barcode": "1897848-0001555-118714",  ← ✅ USE THIS!
      "result": "Pass",
      "passed_rois": 10,
      "failed_rois": 0
    }
  },
  
  "overall_result": {
    "passed": true,
    "total_rois": 10,
    "passed_rois": 10,
    "failed_rois": 0
  }
}
```

---

## 💡 Client Code Examples

### Python Client

```python
import requests
import json

# Send inspection request
response = requests.post(
    'http://10.100.27.156:5000/api/session/SESSION_ID/inspect',
    json={
        'image': 'base64_image_data',
        'product_name': '20003548'
    }
)

result = response.json()

# ✅ CORRECT: Read linked barcode from device_summaries
device_id = 1
linked_barcode = result['device_summaries'][str(device_id)]['barcode']
print(f"Device barcode: {linked_barcode}")
# Output: Device barcode: 1897848-0001555-118714

# ❌ WRONG: Don't read from roi_results (this is the original scanned barcode)
# original_barcode = result['roi_results'][0]['barcode_values'][0]
# This gives: 1897848 S/N: 65514 3969 1006 V (not linked!)
```

### C# Client

```csharp
using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;

public class InspectionClient
{
    private readonly HttpClient _httpClient;
    
    public async Task<string> GetDeviceBarcode(string sessionId, string imageData)
    {
        var request = new
        {
            image = imageData,
            product_name = "20003548"
        };
        
        var response = await _httpClient.PostAsJsonAsync(
            $"http://10.100.27.156:5000/api/session/{sessionId}/inspect",
            request
        );
        
        var result = await response.Content.ReadFromJsonAsync<InspectionResult>();
        
        // ✅ CORRECT: Read linked barcode from device_summaries
        var deviceId = 1;
        var linkedBarcode = result.DeviceSummaries[deviceId.ToString()].Barcode;
        Console.WriteLine($"Device barcode: {linkedBarcode}");
        // Output: Device barcode: 1897848-0001555-118714
        
        return linkedBarcode;
    }
}

public class InspectionResult
{
    public Dictionary<string, DeviceSummary> DeviceSummaries { get; set; }
}

public class DeviceSummary
{
    public string Barcode { get; set; }
    public string Result { get; set; }
    public int PassedRois { get; set; }
    public int FailedRois { get; set; }
}
```

### JavaScript/TypeScript Client

```typescript
interface InspectionResult {
  session_id: string;
  device_summaries: {
    [deviceId: string]: {
      barcode: string;
      result: string;
      passed_rois: number;
      failed_rois: number;
    };
  };
}

async function inspectDevice(sessionId: string, imageData: string): Promise<string> {
  const response = await fetch(
    `http://10.100.27.156:5000/api/session/${sessionId}/inspect`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image: imageData,
        product_name: '20003548'
      })
    }
  );
  
  const result: InspectionResult = await response.json();
  
  // ✅ CORRECT: Read linked barcode from device_summaries
  const deviceId = 1;
  const linkedBarcode = result.device_summaries[deviceId].barcode;
  console.log(`Device barcode: ${linkedBarcode}`);
  // Output: Device barcode: 1897848-0001555-118714
  
  return linkedBarcode;
}
```

---

## 🔄 Barcode Transformation Examples

### Real-World Examples

| Original Barcode (Scanned) | Linked Barcode (API) | Use Case |
|----------------------------|---------------------|----------|
| `1897848 S/N: 65514 3969 1006 V` | `1897848-0001555-118714` | Serial number mapping |
| `20003548-0000003-1019720-101` | `20003548-0000003-1019720-101` | Already formatted (pass-through) |
| `INVALID-BARCODE` | `INVALID-BARCODE` | API returns null, fallback to original |

---

## ⚠️ Important Notes

### 1. **Always Use device_summaries["barcode"]**

```python
# ✅ CORRECT
final_barcode = result['device_summaries']['1']['barcode']

# ❌ WRONG - This is the original scanned value
original_barcode = result['roi_results'][0]['barcode_values'][0]
```

### 2. **Both Values Are Available**

- **`roi_results[].barcode_values`**: Original scanned barcode (for audit/debugging)
- **`device_summaries[].barcode`**: Final linked barcode (use this for production)

### 3. **Fallback Behavior**

If the linking API fails:

- Server falls back to original barcode
- `device_summaries["barcode"]` = original scanned value
- Inspection continues normally (non-blocking)

### 4. **Multiple Devices**

For multi-device products:

```python
# Read barcode for each device
for device_id in result['device_summaries']:
    barcode = result['device_summaries'][device_id]['barcode']
    print(f"Device {device_id}: {barcode}")

# Output:
# Device 1: 1897848-0001555-118714
# Device 2: 1897848-0001556-118715
# Device 3: 1897848-0001557-118716
# Device 4: 1897848-0001558-118717
```

---

## 🧪 Testing Your Integration

### Test with curl

```bash
# Create session
SESSION_ID=$(curl -X POST "http://10.100.27.156:5000/api/session/create" \
  -H "Content-Type: application/json" \
  -d '{"product_name":"20003548"}' | jq -r '.session_id')

# Run inspection (use actual image or test image)
curl -X POST "http://10.100.27.156:5000/api/session/$SESSION_ID/inspect" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "BASE64_IMAGE_DATA",
    "product_name": "20003548"
  }' | jq '.device_summaries["1"].barcode'

# Expected output: "1897848-0001555-118714"
```

### Verify Linking is Working

```bash
# Check server logs for linking activity
ssh user@10.100.27.156
tail -f /home/jason_nguyen/visual-aoi-server/logs/api_server.log | grep "barcode"

# Expected log entries:
# INFO - Calling barcode link API for: 1897848 S/N: 65514 3969 1006 V
# INFO - Barcode link API returned: 1897848-0001555-118714
# INFO - Using linked barcode: 1897848 S/N: 65514 3969 1006 V -> 1897848-0001555-118714
```

---

## 🔍 Troubleshooting

### Problem: Getting Original Barcode Instead of Linked

**Symptom**: Client receives `1897848 S/N: 65514 3969 1006 V` instead of `1897848-0001555-118714`

**Causes**:

1. ❌ Reading from `roi_results[].barcode_values` (wrong field)
2. ⚠️ API linking failed (check server logs)

**Solutions**:

1. ✅ Read from `device_summaries[].barcode` (correct field)
2. ✅ Check server logs: `grep "barcode" logs/api_server.log`
3. ✅ Verify API: `curl -X POST "http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData" -d '"TEST"'`

---

### Problem: Linked Barcode is "null"

**Symptom**: `device_summaries[].barcode` contains `"null"` or original barcode

**Causes**:

- Barcode not found in external system
- Invalid barcode format
- API returned null response

**Expected Behavior**: Server falls back to original barcode (non-blocking)

**Action**: Check if original barcode is valid in external system

---

### Problem: Inspection Takes Too Long

**Symptom**: Inspection requests timeout or take 3+ seconds

**Cause**: Barcode linking API timeout (default 3 seconds)

**Solution**: Server admin can reduce timeout:

```python
from src.barcode_linking import set_barcode_link_timeout
set_barcode_link_timeout(1)  # 1 second
```

---

## 📚 Related Documentation

- **Server Architecture**: [copilot-instructions.md](../.github/copilot-instructions.md)
- **Technical Guide**: [BARCODE_LINKING_INTEGRATION.md](BARCODE_LINKING_INTEGRATION.md)
- **API Documentation**: [SWAGGER_DOCUMENTATION.md](SWAGGER_DOCUMENTATION.md)

---

## ✅ Migration Checklist

- [ ] Update client code to read `device_summaries[].barcode` instead of `roi_results[].barcode_values`
- [ ] Test with known barcodes that transform (e.g., `1897848 S/N: 65514 3969 1006 V`)
- [ ] Test with barcodes that pass through (e.g., `20003548-0000003-1019720-101`)
- [ ] Verify fallback behavior when API is unavailable
- [ ] Update client logs/displays to show linked barcodes
- [ ] Update database schema if storing barcodes (may need larger field)

---

## 🎓 Summary

**What Changed**: Server now returns **linked barcodes** instead of raw scanned barcodes

**Action Required**: Update client to read `device_summaries[device_id]["barcode"]`

**Benefit**: Automatic barcode transformation and validation through external system

**Compatibility**: Non-breaking - original barcode still available in `roi_results[].barcode_values`

---

**Last Updated**: October 20, 2025  
**Server Version**: 1.1 (with barcode linking)  
**API Endpoint**: `http://10.100.27.156:5000`  
**Status**: ✅ Production Ready
