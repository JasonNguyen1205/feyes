# Quick Setup: Raspberry Pi Camera

## Enable Raspi Camera in 3 Steps

### 1. Edit Config File

```bash
nano /home/pi/feyes/client/config/system/camera.json
```

Change line 2:
```json
"camera_type": "RASPI",
```

### 2. Install Picamera2

```bash
sudo apt update && sudo apt install -y python3-picamera2 python3-libcamera
sudo raspi-config  # Enable camera interface
sudo reboot
```

### 3. Restart Application

```bash
cd /home/pi/feyes
./kill_client.sh
./launch_client.sh
```

## Verify

Check logs for:
```
✅ Raspberry Pi Camera initialized successfully (1920x1080)
   NOTE: Focus and brightness adjustments are SKIPPED for Raspi Camera (per config)
```

## Benefits

✅ **3-5x faster** image capture  
✅ **No settle delays** between captures  
✅ **Auto focus & exposure** - no manual tuning needed  
✅ **Simpler setup** - fewer parameters to configure

## Switch Back to TIS Camera

Edit config:
```json
"camera_type": "TIS",
```

Restart application.

---

**Full Documentation:** See [RASPI_CAMERA_SUPPORT.md](./RASPI_CAMERA_SUPPORT.md)
