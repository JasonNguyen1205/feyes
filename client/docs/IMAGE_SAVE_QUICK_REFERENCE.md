# Image Save Debugging - Quick Reference Card

**Version:** 1.0  
**Date:** October 3, 2025  
**For:** Visual AOI Client - Image Capture & Save

---

## 🔍 Quick Diagnostics

### Check if Image Save is Working

```bash
# 1. Monitor logs during capture
tail -f ~/visual-aoi-client/client_app.log | grep -E "save|capture|✓|ERROR"

# 2. Check if files are being created
watch -n 1 'ls -lh /mnt/visual-aoi-shared/sessions/*/input/'

# 3. Count captured images
ls /mnt/visual-aoi-shared/sessions/$(ls -t /mnt/visual-aoi-shared/sessions/ | head -1)/input/ | wc -l
```

---

## ❌ Common Error Messages & Fixes

### Error: "Shared folder not accessible"

**Message in log:**
```
ERROR: Shared folder not accessible: /mnt/visual-aoi-shared
```

**Fix:**
```bash
# Check if mounted
df -h | grep visual-aoi-shared

# If not mounted, mount it
sudo mount -t nfs server:/path/to/share /mnt/visual-aoi-shared
# or
sudo mount -t cifs //server/share /mnt/visual-aoi-shared -o username=user
```

---

### Error: "Cannot write to shared folder"

**Message in log:**
```
ERROR: Cannot write to shared folder: [Errno 13] Permission denied
```

**Fix:**
```bash
# Check permissions
ls -ld /mnt/visual-aoi-shared

# Fix permissions (adjust as needed)
sudo chmod 775 /mnt/visual-aoi-shared
sudo chown $USER:$USER /mnt/visual-aoi-shared
```

---

### Error: "Failed to capture image - buffer_data is None"

**Message in log:**
```
ERROR: Failed to capture image with fast capture - buffer_data is None
```

**Fix:**
1. Check camera connection (USB cable)
2. Restart camera
3. Reinitialize camera in client
4. Check TIS camera drivers

```bash
# Check USB devices
lsusb | grep "Imaging"

# Restart udev if needed
sudo udevadm control --reload-rules
```

---

### Error: "Captured image has zero size"

**Message in log:**
```
ERROR: Captured image has zero size
```

**Fix:**
1. Check camera settings (exposure, focus)
2. Check lighting conditions
3. Verify camera lens cap is off
4. Try manual capture test

---

### Error: "cv2.imwrite failed"

**Message in log:**
```
ERROR: cv2.imwrite failed to write image to /mnt/.../capture_F325_E1500.jpg
```

**Fix:**
```bash
# Check disk space
df -h /mnt/visual-aoi-shared

# Check if path is too long
echo "/mnt/visual-aoi-shared/sessions/{session_id}/input/capture_F325_E1500.jpg" | wc -c
# Should be < 255 characters

# Test write manually
touch /mnt/visual-aoi-shared/test.txt
rm /mnt/visual-aoi-shared/test.txt
```

---

### Error: "Image file not found after write"

**Message in log:**
```
ERROR: Image file not found after write: /mnt/.../capture_F325_E1500.jpg
```

**Fix:**
```bash
# Check if network mount has sync issues
sudo mount -o remount,sync /mnt/visual-aoi-shared

# Check mount status
mount | grep visual-aoi-shared

# Try manual sync
sync
```

---

## ✅ Expected Log Output (Success)

```
INFO: ✓ Shared folder verified: /mnt/visual-aoi-shared
INFO: ✓ Can create session directory: /mnt/visual-aoi-shared/sessions/20251003_103000
INFO: Starting fast capture...
INFO: Buffer captured successfully, size: 41472000
INFO: Fast capture successful - image shape: (5360, 7716, 4), dtype: uint8
INFO: Attempting to save captured image for group 1/3
INFO: Preparing to save image: shape=(5360, 7716, 4), dtype=uint8
INFO: Creating directories: /mnt/visual-aoi-shared/sessions/20251003_103000/input
INFO: Directories verified: input_dir exists=True
INFO: Saving image to: /mnt/visual-aoi-shared/sessions/20251003_103000/input/capture_F325_E1500.jpg
INFO: ✓ Image saved successfully: .../capture_F325_E1500.jpg (size: 12456789 bytes)
INFO: ✓ Successfully captured and saved image for group (F:325, E:1500)
INFO:   Metadata: {'image_filename': 'capture_F325_E1500.jpg', 'focus': 325, 'exposure': 1500, 'rois': [1, 2, 3]}
```

**Look for:** ✓ checkmarks at each step

---

## 🔧 Manual Verification Commands

### Before Running Client

```bash
# 1. Verify shared folder
ls -la /mnt/visual-aoi-shared/

# 2. Check write permission
touch /mnt/visual-aoi-shared/.write_test && rm /mnt/visual-aoi-shared/.write_test && echo "OK"

# 3. Check disk space
df -h /mnt/visual-aoi-shared | tail -1

# 4. Check camera
lsusb | grep "Imaging"
```

### During Capture

```bash
# 1. Watch for new files
watch -n 1 'ls -lht /mnt/visual-aoi-shared/sessions/*/input/ | head -5'

# 2. Monitor disk usage
watch -n 2 'df -h /mnt/visual-aoi-shared'

# 3. Follow logs
tail -f ~/visual-aoi-client/client_app.log
```

### After Capture

```bash
# 1. Count images
SESSION_ID=$(ls -t /mnt/visual-aoi-shared/sessions/ | head -1)
echo "Session: $SESSION_ID"
ls /mnt/visual-aoi-shared/sessions/$SESSION_ID/input/ | wc -l

# 2. Check image sizes
ls -lh /mnt/visual-aoi-shared/sessions/$SESSION_ID/input/

# 3. Verify images are valid
for img in /mnt/visual-aoi-shared/sessions/$SESSION_ID/input/*.jpg; do
    file "$img"
done
```

---

## 📊 Image Properties Reference

### Expected Values

| Property | Expected Value | Notes |
|----------|---------------|-------|
| **Image shape** | `(5360, 7716, 4)` or `(5360, 7716, 3)` | Full resolution TIS camera |
| **Image dtype** | `uint8` | 8-bit color channels |
| **Image size** | `> 0` pixels | Must have data |
| **File size** | 5-20 MB | Depends on content |
| **File format** | JPEG | Quality 95 |
| **Filename** | `capture_F{focus}_E{exposure}.jpg` | Descriptive naming |

### Troubleshooting by Image Size

| Image Size | Issue | Fix |
|------------|-------|-----|
| 0 bytes | cv2.imwrite failed | Check disk space, permissions |
| < 1 MB | Very dark/blank image | Check exposure, lighting |
| 1-5 MB | Normal but low detail | Check focus, check product |
| 5-20 MB | Normal | ✓ Good |
| > 50 MB | Wrong format/uncompressed | Check cv2.imwrite parameters |

---

## 🚨 Emergency Recovery

### If Client Freezes During Save

```bash
# 1. Check if process is hung
ps aux | grep client_app_simple.py

# 2. Check mount status
mount | grep visual-aoi-shared

# 3. Kill frozen process
pkill -9 -f client_app_simple.py

# 4. Remount shared folder
sudo umount /mnt/visual-aoi-shared
sudo mount /mnt/visual-aoi-shared

# 5. Restart client
cd ~/visual-aoi-client
python client/client_app_simple.py
```

---

### If Images Not Appearing

```bash
# 1. Check network connectivity
ping server_ip

# 2. Check mount is responsive
ls /mnt/visual-aoi-shared/
# If hangs, mount is frozen

# 3. Force unmount and remount
sudo umount -f /mnt/visual-aoi-shared
sudo mount /mnt/visual-aoi-shared

# 4. Verify with test write
echo "test" > /mnt/visual-aoi-shared/test.txt
cat /mnt/visual-aoi-shared/test.txt
rm /mnt/visual-aoi-shared/test.txt
```

---

## 📞 Support Checklist

When reporting issues, provide:

- [ ] Client log file: `~/visual-aoi-client/client_app.log`
- [ ] Session ID experiencing issues
- [ ] Error message from dialog
- [ ] Output of: `df -h /mnt/visual-aoi-shared`
- [ ] Output of: `mount | grep visual-aoi-shared`
- [ ] Output of: `ls -la /mnt/visual-aoi-shared/sessions/{session_id}/`
- [ ] Camera model and serial number
- [ ] Network status: `ping server_ip`

---

## 🔗 Related Documentation

- **Full debugging guide:** `docs/IMAGE_SAVE_DEBUGGING.md`
- **Implementation summary:** `docs/INSPECTION_FLOW_DEBUG_SUMMARY.md`
- **Inspection flow analysis:** `docs/INSPECTION_FLOW_ANALYSIS.md`
- **Test suite:** `tests/test_image_save_debugging.py`

---

## 📝 Quick Notes

**Shared Folder Path:** `/mnt/visual-aoi-shared`  
**Session Path:** `/mnt/visual-aoi-shared/sessions/{session_id}/`  
**Input Images:** `/mnt/visual-aoi-shared/sessions/{session_id}/input/`  
**Output Results:** `/mnt/visual-aoi-shared/sessions/{session_id}/output/`  
**Image Format:** `capture_F{focus}_E{exposure}.jpg`  
**Image Quality:** 95 (high quality JPEG)

---

**Version:** 1.0  
**Last Updated:** October 3, 2025  
**Status:** ✅ Production Ready
