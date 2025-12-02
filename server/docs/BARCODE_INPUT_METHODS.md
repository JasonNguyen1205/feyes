# Device Barcode Input Methods

## Overview

The Visual AOI Server supports **two methods** for obtaining device barcodes during inspection:

1. **ROI-Scanned Barcodes** - Detected automatically during image inspection
2. **Client-Provided Barcodes** - Sent directly by the client via API parameters

**Both methods now apply barcode linking** to validate/transform barcodes through the external API.

---

## Method 1: ROI-Scanned Barcodes

### Description

The server detects barcodes from the inspection image using configured barcode ROIs.

### Configuration

```json
{
  "idx": 1,
  "type": 1,
  "coords": [100, 200, 300, 400],
  "is_device_barcode": true,  // ← Mark this ROI as device barcode
  ...
}
```

### Priority Levels

#### Priority 0: Device Main Barcode ROIs (HIGHEST)

- **Trigger**: ROI has `is_device_barcode: true`
- **Applies Linking**: ✅ YES
- **Example**:

  ```
  Scanned: "1897848 S/N: 65514 3969 1006 V"
  Linked:  "1897848-0001555-118714"
  ```

#### Priority 1: Any Barcode ROI (Fallback)

- **Trigger**: Any barcode ROI if device barcode not yet set
- **Applies Linking**: ✅ YES
- **Example**:

  ```
  Scanned: "20003548-0000003-1019720-101"
  Linked:  "20003548-0000003-1019720-101" (validated)
  ```

### API Request Example

```bash
curl -X POST "http://10.100.27.156:5000/api/session/d34614ce/inspect" \
  -H "Content-Type: application/json" \
  -d '{
    "image_filename": "device_image.jpg"
  }'
```

### API Response

```json
{
  "device_summaries": {
    "1": {
      "barcode": "1897848-0001555-118714",  // ← Linked barcode
      "device_passed": true,
      ...
    }
  },
  "roi_results": [
    {
      "roi_id": 1,
      "roi_type_name": "barcode",
      "barcode_values": ["1897848 S/N: 65514 3969 1006 V"],  // ← Original
      ...
    }
  ]
}
```

---

## Method 2: Client-Provided Barcodes

### Description

The client sends device barcodes directly as API parameters, bypassing ROI detection.

### Use Cases

- Client already has barcode from external scanner
- Barcode was pre-scanned before inspection
- Manual barcode entry by operator
- Integration with external barcode systems

### Priority Levels

#### Priority 2: Multi-Device Barcodes

- **Trigger**: `device_barcodes` parameter provided
- **Applies Linking**: ✅ YES (NEW!)
- **Format**: Dictionary mapping device ID to barcode

**API Request Example**:

```bash
curl -X POST "http://10.100.27.156:5000/api/session/d34614ce/inspect" \
  -H "Content-Type: application/json" \
  -d '{
    "image_filename": "device_image.jpg",
    "device_barcodes": {
      "1": "1897848 S/N: 65514 3969 1006 V",
      "2": "20003548-0000003-1019720-101"
    }
  }'
```

**API Response**:

```json
{
  "device_summaries": {
    "1": {
      "barcode": "1897848-0001555-118714",  // ← Linked from client input
      "device_passed": true,
      ...
    },
    "2": {
      "barcode": "20003548-0000003-1019720-101",  // ← Validated
      "device_passed": true,
      ...
    }
  }
}
```

**Alternative List Format**:

```bash
curl -X POST "http://10.100.27.156:5000/api/session/d34614ce/inspect" \
  -H "Content-Type: application/json" \
  -d '{
    "image_filename": "device_image.jpg",
    "device_barcodes": [
      {"device_id": 1, "barcode": "1897848 S/N: 65514 3969 1006 V"},
      {"device_id": 2, "barcode": "20003548-0000003-1019720-101"}
    ]
  }'
```

#### Priority 3: Legacy Single Barcode

- **Trigger**: `device_barcode` parameter provided (legacy)
- **Applies Linking**: ✅ YES (NEW!)
- **Format**: Single string applied to all devices

**API Request Example**:

```bash
curl -X POST "http://10.100.27.156:5000/api/session/d34614ce/inspect" \
  -H "Content-Type: application/json" \
  -d '{
    "image_filename": "device_image.jpg",
    "device_barcode": "1897848 S/N: 65514 3969 1006 V"
  }'
```

**API Response**:

```json
{
  "device_summaries": {
    "1": {
      "barcode": "1897848-0001555-118714",  // ← Linked from legacy input
      "device_passed": true,
      ...
    }
  }
}
```

---

## Barcode Linking Behavior

### What Happens When Client Provides Barcode

**Before (Old Behavior)**:

```
Client Input → Server → Response (original barcode)
```

**After (New Behavior)**:

```
Client Input → Server → External API → Response (linked barcode)
```

### Example Flow

1. **Client sends barcode**:

   ```json
   {
     "device_barcodes": {
       "1": "1897848 S/N: 65514 3969 1006 V"
     }
   }
   ```

2. **Server calls external API**:

   ```bash
   POST http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData
   Body: "1897848 S/N: 65514 3969 1006 V"
   ```

3. **API responds with linked data**:

   ```
   1897848-0001555-118714
   ```

4. **Server returns linked barcode**:

   ```json
   {
     "device_summaries": {
       "1": {
         "barcode": "1897848-0001555-118714"
       }
     }
   }
   ```

### Error Handling

If the external API fails (timeout, connection error, returns "null"), the server gracefully falls back to the original barcode:

```
Client Input:  "1897848 S/N: 65514 3969 1006 V"
API Timeout:   (3 second timeout exceeded)
Fallback:      "1897848 S/N: 65514 3969 1006 V" (original)
Server Returns: "1897848 S/N: 65514 3969 1006 V"
```

---

## Priority Order Summary

The server applies barcode sources in this priority order:

```
Priority 0: ROI with is_device_barcode=true
            ↓ (applies linking) ✅
            
Priority 1: Any barcode ROI (if Priority 0 not found)
            ↓ (applies linking) ✅
            
Priority 2: device_barcodes parameter
            ↓ (applies linking) ✅ NEW!
            
Priority 3: device_barcode parameter (legacy)
            ↓ (applies linking) ✅ NEW!
            
Priority 4: Default 'N/A'
```

**Key Point**: Barcode linking is now applied at **ALL priority levels** (0-3).

---

## Code Examples

### Python Client - Send Pre-Scanned Barcode

```python
import requests

# Client already has barcode from external scanner
scanned_barcode = "1897848 S/N: 65514 3969 1006 V"

# Send to server for inspection
response = requests.post(
    'http://10.100.27.156:5000/api/session/d34614ce/inspect',
    json={
        'image_filename': 'device_image.jpg',
        'device_barcodes': {
            '1': scanned_barcode  # Server will link this barcode
        }
    }
)

# Get linked barcode from response
result = response.json()
linked_barcode = result['device_summaries']['1']['barcode']
print(f"Sent: {scanned_barcode}")
print(f"Got:  {linked_barcode}")
# Output:
# Sent: 1897848 S/N: 65514 3969 1006 V
# Got:  1897848-0001555-118714
```

### C# Client - Multi-Device Barcodes

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;

var client = new HttpClient();

// Client has barcodes from external scanners
var requestData = new
{
    image_filename = "device_image.jpg",
    device_barcodes = new Dictionary<string, string>
    {
        { "1", "1897848 S/N: 65514 3969 1006 V" },
        { "2", "20003548-0000003-1019720-101" }
    }
};

var json = JsonSerializer.Serialize(requestData);
var content = new StringContent(json, Encoding.UTF8, "application/json");

var response = await client.PostAsync(
    "http://10.100.27.156:5000/api/session/d34614ce/inspect",
    content
);

var responseJson = await response.Content.ReadAsStringAsync();
var result = JsonSerializer.Deserialize<JsonDocument>(responseJson);

// Both barcodes were linked by server
var device1Barcode = result.RootElement
    .GetProperty("device_summaries")
    .GetProperty("1")
    .GetProperty("barcode")
    .GetString();
    
Console.WriteLine($"Device 1 Linked Barcode: {device1Barcode}");
// Output: Device 1 Linked Barcode: 1897848-0001555-118714
```

### JavaScript/TypeScript - Legacy Single Barcode

```typescript
import axios from 'axios';

// Client has single barcode for all devices
const scannedBarcode = "1897848 S/N: 65514 3969 1006 V";

const response = await axios.post(
  'http://10.100.27.156:5000/api/session/d34614ce/inspect',
  {
    image_filename: 'device_image.jpg',
    device_barcode: scannedBarcode  // Legacy format (server will link)
  }
);

// Server returns linked barcode
const linkedBarcode = response.data.device_summaries['1'].barcode;
console.log(`Original: ${scannedBarcode}`);
console.log(`Linked:   ${linkedBarcode}`);
// Output:
// Original: 1897848 S/N: 65514 3969 1006 V
// Linked:   1897848-0001555-118714
```

---

## When to Use Each Method

### Use ROI-Scanned Barcodes When

- ✅ Barcode is part of the device/product being inspected
- ✅ Barcode is visible in the inspection image
- ✅ You want to verify barcode presence during inspection
- ✅ Barcode location is consistent across devices

### Use Client-Provided Barcodes When

- ✅ Barcode was pre-scanned before image capture
- ✅ Using external barcode scanner hardware
- ✅ Barcode is not visible in inspection image
- ✅ Manual barcode entry by operator
- ✅ Integration with existing barcode tracking system

### Combining Both Methods

You can mix both methods! If you provide `device_barcodes` parameter AND have barcode ROIs configured:

1. ROI-scanned barcodes take priority (Priority 0/1)
2. Client-provided barcodes used as fallback (Priority 2/3)

---

## Migration Guide

### For Existing Clients Using Client-Provided Barcodes

**No changes required!** Your existing code will continue working, but now you'll automatically get linked barcodes.

**Before (old behavior)**:

```
Client sends: "1897848 S/N: 65514 3969 1006 V"
Server returns: "1897848 S/N: 65514 3969 1006 V" (same)
```

**After (new behavior)**:

```
Client sends: "1897848 S/N: 65514 3969 1006 V"
Server returns: "1897848-0001555-118714" (linked!)
```

**Action Items**:

1. Test your client code with the updated server
2. Verify the linked barcodes are correct
3. Update any barcode validation logic if needed
4. Update logs/displays to show linked barcodes

---

## Troubleshooting

### Issue: Client-provided barcode not being linked

**Check**:

1. Verify server has barcode linking enabled:

   ```bash
   # Check server logs for "Barcode linking enabled" message
   ```

2. Test barcode linking directly:

   ```bash
   curl -X POST 'http://10.100.10.83:5000/api/ProcessLock/FA/GetLinkData' \
     -H 'Content-Type: application/json' \
     -d '"YOUR_BARCODE_HERE"'
   ```

3. Check server logs for linking errors:

   ```bash
   grep "barcode" /path/to/server.log
   ```

### Issue: Getting original barcode instead of linked

**Possible Causes**:

1. External API is down/unreachable
2. External API returned "null" (invalid barcode)
3. API timeout (>3 seconds)
4. Network connectivity issue

**Solution**: Server gracefully falls back to original barcode. Check logs:

```
[WARNING] Barcode linking failed for '...': Connection timeout
[INFO] Using original barcode as fallback
```

---

## Configuration

### Enable/Disable Barcode Linking

```python
from src.barcode_linking import set_barcode_link_enabled

# Disable linking for all barcodes (testing/debugging)
set_barcode_link_enabled(False)

# Re-enable linking
set_barcode_link_enabled(True)
```

### Change API Endpoint

```python
from src.barcode_linking import set_barcode_link_api_url

# Point to different API server
set_barcode_link_api_url("http://backup-server:5000/api/ProcessLock/FA/GetLinkData")
```

### Adjust Timeout

```python
from src.barcode_linking import set_barcode_link_timeout

# Increase timeout for slow networks
set_barcode_link_timeout(5.0)  # 5 seconds
```

---

## Summary

| Method | Priority | Applies Linking | Use Case |
|--------|----------|-----------------|----------|
| ROI with `is_device_barcode=true` | 0 | ✅ YES | Main device barcode in image |
| Any barcode ROI | 1 | ✅ YES | Fallback barcode in image |
| `device_barcodes` parameter | 2 | ✅ YES (NEW!) | Pre-scanned multi-device barcodes |
| `device_barcode` parameter | 3 | ✅ YES (NEW!) | Pre-scanned single barcode (legacy) |

**Key Takeaway**: All barcode sources now go through the external linking API for validation/transformation. The server always returns the linked barcode in `device_summaries[device_id]["barcode"]`.
