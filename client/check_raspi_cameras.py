#!/usr/bin/env python3
"""
Simple script to check for available Raspberry Pi cameras on the device.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Raspberry Pi Camera Detection")
print("=" * 70)
print()

# Check if Picamera2 is available
print("Step 1: Checking Picamera2 module...")
try:
    from picamera2 import Picamera2
    print("✅ Picamera2 module is installed")
    PICAMERA2_AVAILABLE = True
except ImportError as e:
    print(f"❌ Picamera2 module not available: {e}")
    print("   Install with: sudo apt install -y python3-picamera2 python3-libcamera")
    PICAMERA2_AVAILABLE = False
    sys.exit(1)

print()
print("Step 2: Checking for available cameras...")
print()

cameras_found = []

# Method 1: Try global_camera_info() (newer API)
print("Method 1: Using Picamera2.global_camera_info()...")
try:
    camera_list = Picamera2.global_camera_info()
    
    if camera_list:
        print(f"✅ Found {len(camera_list)} camera(s)")
        for idx, cam_info in enumerate(camera_list):
            model = cam_info.get('Model', 'Unknown')
            location = cam_info.get('Location', 'Unknown')
            rotation = cam_info.get('Rotation', 0)
            
            print(f"\n  Camera {idx}:")
            print(f"    Model: {model}")
            print(f"    Location: {location}")
            print(f"    Rotation: {rotation}°")
            print(f"    Full info: {cam_info}")
            
            cameras_found.append({
                'id': idx,
                'model': model,
                'location': location,
                'method': 'global_camera_info'
            })
    else:
        print("⚠️  No cameras found via global_camera_info()")
        
except AttributeError:
    print("⚠️  global_camera_info() not available (older Picamera2 version)")
except Exception as e:
    print(f"❌ Error using global_camera_info(): {e}")

print()

# Method 2: Try creating a Picamera2 instance (fallback)
if not cameras_found:
    print("Method 2: Attempting to create Picamera2 instance...")
    try:
        test_cam = Picamera2()
        print("✅ Successfully created Picamera2 instance - camera detected!")
        
        # Try to get camera info
        try:
            props = test_cam.camera_properties
            print(f"  Camera properties: {props}")
        except:
            print("  (Could not retrieve detailed properties)")
        
        test_cam.close()
        
        cameras_found.append({
            'id': 0,
            'model': 'Raspberry Pi Camera',
            'location': 'embedded',
            'method': 'instance_creation'
        })
        
    except Exception as e:
        print(f"❌ Failed to create Picamera2 instance: {e}")
        print("   Possible causes:")
        print("   1. Camera interface not enabled (run: sudo raspi-config)")
        print("   2. Camera not connected properly")
        print("   3. Camera in use by another application")
        print("   4. Insufficient permissions")

print()

# Method 3: Check system devices
print("Method 3: Checking /dev/video* devices...")
try:
    import glob
    video_devices = glob.glob('/dev/video*')
    if video_devices:
        print(f"✅ Found video devices: {', '.join(video_devices)}")
        for device in video_devices:
            print(f"  {device}")
    else:
        print("❌ No /dev/video* devices found")
except Exception as e:
    print(f"❌ Error checking video devices: {e}")

print()

# Method 4: Check with libcamera-hello
print("Method 4: Checking with libcamera-hello...")
try:
    import subprocess
    result = subprocess.run(
        ['libcamera-hello', '--list-cameras'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0:
        print("✅ libcamera-hello output:")
        print(result.stdout)
    else:
        print(f"⚠️  libcamera-hello returned error code {result.returncode}")
        if result.stderr:
            print(f"Error: {result.stderr}")
except FileNotFoundError:
    print("⚠️  libcamera-hello not found (install libcamera-apps)")
except subprocess.TimeoutExpired:
    print("⚠️  libcamera-hello timed out")
except Exception as e:
    print(f"❌ Error running libcamera-hello: {e}")

print()
print("=" * 70)
print("Summary")
print("=" * 70)

if cameras_found:
    print(f"\n✅ SUCCESS: Found {len(cameras_found)} Raspberry Pi camera(s)\n")
    for cam in cameras_found:
        print(f"  • Camera {cam['id']}: {cam['model']} ({cam['method']})")
    print()
    print("You can now use the Raspberry Pi camera in the Visual AOI system.")
    print("Make sure camera_type is set to 'RASPI' in config/system/camera.json")
else:
    print("\n❌ FAILURE: No Raspberry Pi cameras detected\n")
    print("Troubleshooting steps:")
    print("  1. Enable camera interface:")
    print("     sudo raspi-config")
    print("     → Interface Options → Camera → Enable")
    print()
    print("  2. Reboot the Raspberry Pi:")
    print("     sudo reboot")
    print()
    print("  3. Verify camera connection:")
    print("     - Check cable is properly connected to CSI port")
    print("     - Blue side should face Ethernet port")
    print()
    print("  4. Test with libcamera:")
    print("     libcamera-hello --list-cameras")
    print("     libcamera-jpeg -o test.jpg")

print()
print("=" * 70)
