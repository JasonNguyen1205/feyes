# Raspberry Pi Camera Support

**Last Updated:** December 2025  
**Version:** 1.0

## Overview

The Visual AOI Client now supports both **TIS Industrial Cameras** and **Raspberry Pi Cameras**. The camera type is configured in the system config file, and the application automatically handles the differences between the two camera types.

## Key Differences

### TIS Industrial Camera (Default)
- **Manual Focus & Exposure**: Requires precise focus and exposure settings per ROI group
- **Settle Delay**: 3-second delay after changing settings for camera to stabilize
- **GStreamer Pipeline**: Uses GStreamer for video capture
- **Full Control**: All camera parameters can be adjusted programmatically

### Raspberry Pi Camera
- **Auto Focus & Exposure**: Automatically adjusts focus and brightness
- **No Settle Delay**: Immediate capture without waiting periods
- **Picamera2 Library**: Uses native Picamera2 Python library
- **Simplified Control**: Focus and exposure adjustments are **automatically skipped**

## Configuration

### Enabling Raspberry Pi Camera

Edit `/home/pi/feyes/client/config/system/camera.json`:

```json
{
  "camera_type": "RASPI",
  "camera_hardware": {
    "serial": "",
    "width": 7716,
    "height": 5360,
    "fps": "143/20",
    "format": "BAYER_GBRG"
  },
  "camera_defaults": {
    "focus": 305,
    "exposure": 15000
  },
  "raspi_camera": {
    "enabled": true,
    "width": 1920,
    "height": 1080,
    "skip_focus_adjust": true,
    "skip_brightness_adjust": true,
    "auto_focus": false,
    "auto_exposure": true
  },
  ...
}
```

### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `camera_type` | string | "TIS" or "RASPI" |
| `raspi_camera.enabled` | boolean | Enable Raspi Camera support |
| `raspi_camera.width` | integer | Image width (default: 1920) |
| `raspi_camera.height` | integer | Image height (default: 1080) |
| `raspi_camera.skip_focus_adjust` | boolean | Skip focus adjustment steps (recommended: true) |
| `raspi_camera.skip_brightness_adjust` | boolean | Skip brightness adjustment steps (recommended: true) |
| `raspi_camera.auto_focus` | boolean | Enable auto-focus (if supported by camera) |
| `raspi_camera.auto_exposure` | boolean | Enable auto-exposure (recommended: true) |

## Installation Requirements

### Picamera2 Library

The Raspberry Pi Camera requires the `picamera2` Python library:

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-picamera2 python3-libcamera

# Enable camera interface
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable

# Reboot to apply changes
sudo reboot
```

### Verify Installation

```bash
# Test if camera is detected
libcamera-hello --list-cameras

# Test capture
libcamera-jpeg -o test.jpg
```

## Implementation Details

### Automatic Behavior Changes

When `camera_type` is set to "RASPI", the following behaviors automatically change:

1. **Camera Initialization** (`initialize_camera()`)
   - Routes to `initialize_raspi_camera()` instead of `initialize_tis_camera()`
   - Skips GStreamer pipeline setup
   - Uses Picamera2 configuration

2. **Image Capture** (`capture_image()`)
   - Ignores `focus` and `exposure_time` parameters
   - No settle delay between captures
   - Direct capture from Picamera2

3. **Fast Capture** (`capture_image_fast()`)
   - Always fast for Raspi Camera (no settings to change)
   - Prints note about skipped adjustments

4. **Camera Properties** (`set_camera_properties()`)
   - No-op for Raspi Camera
   - Prints informational message if called with parameters

5. **Camera Status** (`get_camera_status()`)
   - Returns Raspi-specific status
   - No pipeline state (not applicable)

### Code Flow Example

```python
# config.json
"camera_type": "RASPI"

# Client app initialization
camera.initialize_camera()
  ↓
get_camera_type() returns "RASPI"
  ↓
initialize_raspi_camera(width=1920, height=1080)
  ↓
PiCam = Picamera2()
PiCam.configure({"size": (1920, 1080)})
PiCam.start()

# Inspection workflow
camera.capture_image(focus=305, exposure=1200)
  ↓
is_raspi_camera() returns True
  ↓
Print: "Note: Focus and exposure parameters ignored for Raspi Camera"
  ↓
capture_raspi_image()
  ↓
img = PiCam.capture_array()  # No focus/exposure adjustments
  ↓
Convert RGB to BGR
  ↓
Validate image
  ↓
Return image
```

## Performance Comparison

| Operation | TIS Camera | Raspi Camera | Improvement |
|-----------|-----------|--------------|-------------|
| **Initialization** | 5-7 seconds | 1-2 seconds | 3-5x faster |
| **First Capture** | Immediate (fast mode) | Immediate | Same |
| **Subsequent Captures** | 3-5 seconds (with settle delay) | Immediate | 3-5x faster |
| **ROI Group Changes** | 3-5 seconds per group | Immediate | 3-5x faster |
| **Total Inspection Time** | Depends on ROI groups | Much faster | Significant |

## Migration Guide

### From TIS to Raspi Camera

1. **Update Configuration**
   ```bash
   nano /home/pi/feyes/client/config/system/camera.json
   ```
   Change `"camera_type": "TIS"` to `"camera_type": "RASPI"`

2. **Install Dependencies**
   ```bash
   sudo apt install -y python3-picamera2
   ```

3. **Enable Camera**
   ```bash
   sudo raspi-config
   # Enable camera interface
   ```

4. **Restart Application**
   ```bash
   ./kill_client.sh
   ./launch_client.sh
   ```

5. **Verify**
   - Check logs for "Raspberry Pi Camera initialized successfully"
   - Verify no focus/brightness adjustment messages
   - Test image capture

### From Raspi to TIS Camera

1. **Update Configuration**
   Change `"camera_type": "RASPI"` back to `"camera_type": "TIS"`

2. **Verify TIS SDK**
   ```bash
   # Check if TIS module is available
   python3 -c "import TIS; print('TIS module OK')"
   ```

3. **Restart Application**

## Troubleshooting

### Raspi Camera Not Found

```
Error: Picamera2 module not available
```

**Solution:**
```bash
sudo apt install -y python3-picamera2 python3-libcamera
sudo reboot
```

### Camera Interface Not Enabled

```
Error: Failed to initialize Raspi Camera
```

**Solution:**
```bash
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot
```

### Image Validation Fails

```
Image too dark/bright or low contrast
```

**Solution:**
- Check lighting conditions
- Clean camera lens
- Adjust `raspi_camera.auto_exposure` setting
- Verify camera is properly focused

### Focus/Brightness Messages Still Appearing

```
Note: Focus and exposure parameters ignored for Raspi Camera
```

This is **informational only** and does not indicate an error. The system is correctly skipping those adjustments.

## API Changes

### New Functions

- `initialize_raspi_camera(width, height)` - Initialize Raspberry Pi Camera
- `capture_raspi_image()` - Capture from Raspberry Pi Camera
- `is_raspi_camera()` - Check if Raspi Camera is configured
- `should_skip_focus_adjust()` - Check if focus adjustment should be skipped
- `should_skip_brightness_adjust()` - Check if brightness adjustment should be skipped

### Modified Functions

- `initialize_camera()` - Now routes to appropriate camera type
- `capture_image()` - Handles both camera types
- `capture_image_fast()` - Optimized for both camera types
- `set_camera_properties()` - No-op for Raspi Camera
- `get_camera_status()` - Returns camera-specific status

## Best Practices

### For TIS Camera
- Use per-ROI focus and exposure settings
- Allow 3-second settle delay after settings changes
- Validate pipeline state before capture

### For Raspi Camera
- Set `skip_focus_adjust: true` and `skip_brightness_adjust: true`
- Enable `auto_exposure: true` for best results
- Use lower resolution (1920x1080) for faster processing
- Ensure adequate lighting conditions

## Future Enhancements

Potential improvements for Raspi Camera support:

1. **HDR Mode** - Enable High Dynamic Range for better image quality
2. **Manual Controls** - Add optional manual focus/exposure override
3. **Multiple Cameras** - Support multiple Raspi Cameras simultaneously
4. **Video Streaming** - Add live preview support
5. **Advanced Features** - Utilize Raspi Camera's AI capabilities

## Related Documentation

- [Camera Implementation Details](./CAMERA_IMPROVEMENTS.md)
- [System Configuration](../config/system/camera.json)
- [TIS Camera Specification](./PROJECT_INSTRUCTIONS.md)
- [Picamera2 Documentation](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2025 | Initial Raspberry Pi Camera support |
