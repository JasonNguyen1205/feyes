"""
Camera handling for Visual AOI System.
"""

import json
import time
import threading
import cv2
import numpy as np
import os
from pathlib import Path

# Initialize GStreamer
try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.init(None)
    print("GStreamer initialized successfully")
except (ImportError, ValueError) as e:
    print(f"Warning: GStreamer not available ({e})")
    Gst = None
    gi = None

# Import TIS module - robust import with fallback
try:
    from . import TIS
    print("TIS module imported successfully")
except (ImportError, ValueError) as e:
    try:
        import TIS
        print("TIS module imported as standalone")
    except (ImportError, ValueError) as e:
        print(f"Warning: TIS module not available ({e})")
        TIS = None

# Try to import Picamera2 for Raspberry Pi Camera support
try:
    from picamera2 import Picamera2
    print("Picamera2 module imported successfully")
    PICAMERA2_AVAILABLE = True
except ImportError:
    print("Warning: Picamera2 module not available")
    Picamera2 = None
    PICAMERA2_AVAILABLE = False

# Import configuration values - use deprecated constants for compatibility
try:
    from .config import (DEFAULT_FOCUS, DEFAULT_EXPOSURE, FOCUS_SETTLE_DELAY, ENABLE_FAST_CAPTURE,
                       CAMERA_SERIAL, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS, CAMERA_FORMAT,
                       CAMERA_RETRY_ATTEMPTS, CAMERA_RETRY_DELAY,
                       IMAGE_MIN_BRIGHTNESS, IMAGE_MAX_BRIGHTNESS, IMAGE_MIN_CONTRAST,
                       get_camera_type, is_raspi_camera, is_tis_camera, 
                       should_skip_focus_adjust, should_skip_brightness_adjust,
                       get_raspi_camera_config)
except ImportError:
    try:
        from src.config import (DEFAULT_FOCUS, DEFAULT_EXPOSURE, FOCUS_SETTLE_DELAY, ENABLE_FAST_CAPTURE,
                           CAMERA_SERIAL, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS, CAMERA_FORMAT,
                           CAMERA_RETRY_ATTEMPTS, CAMERA_RETRY_DELAY,
                           IMAGE_MIN_BRIGHTNESS, IMAGE_MAX_BRIGHTNESS, IMAGE_MIN_CONTRAST,
                           get_camera_type, is_raspi_camera, is_tis_camera, 
                           should_skip_focus_adjust, should_skip_brightness_adjust,
                           get_raspi_camera_config)
    except ImportError:
        # Fallback values if config import fails
        DEFAULT_FOCUS = 305
        DEFAULT_EXPOSURE = 3000
        FOCUS_SETTLE_DELAY = 3.0
        ENABLE_FAST_CAPTURE = True
        CAMERA_SERIAL = "30320436"
        CAMERA_WIDTH = 7716
        CAMERA_HEIGHT = 5360
        CAMERA_FPS = "7/1"
        CAMERA_FORMAT = "BGRA"
        CAMERA_RETRY_ATTEMPTS = 3
        CAMERA_RETRY_DELAY = 1.0
        IMAGE_MIN_BRIGHTNESS = 10
        IMAGE_MAX_BRIGHTNESS = 245
        IMAGE_MIN_CONTRAST = 5
        
        # Fallback camera type functions
        def get_camera_type():
            return "TIS"
        def is_raspi_camera():
            return False
        def is_tis_camera():
            return True
        def should_skip_focus_adjust():
            return False
        def should_skip_brightness_adjust():
            return False
        def get_raspi_camera_config(key=None):
            return None

# Global camera instances
Tis = None  # TIS camera instance
PiCam = None  # Raspberry Pi camera instance

# Cache for discovered exposure property name
_exposure_property_name = None

def list_available_raspi_cameras():
    """List available Raspberry Pi cameras.
    
    Returns:
        list: List of camera info dictionaries with keys:
            - id: Camera ID (0, 1, 2, etc.)
            - model: Camera model name
            - type: Camera type (raspi)
            - display_name: Human-readable name
    """
    if not PICAMERA2_AVAILABLE or Picamera2 is None:
        print("Picamera2 module not available")
        return []
    
    try:
        cameras = []
        
        # Try to get camera list using Picamera2.global_camera_info()
        try:
            camera_list = Picamera2.global_camera_info()
            
            if camera_list:
                for idx, cam_info in enumerate(camera_list):
                    # Parse camera info
                    model = cam_info.get('Model', 'Unknown')
                    location = cam_info.get('Location', '')
                    rotation = cam_info.get('Rotation', 0)
                    
                    camera_info = {
                        'id': idx,
                        'model': model,
                        'type': 'raspi',
                        'location': location,
                        'rotation': rotation,
                        'display_name': f"Raspberry Pi Camera {idx}: {model}"
                    }
                    cameras.append(camera_info)
                    print(f"Found Raspberry Pi camera: {camera_info['display_name']}")
            else:
                print("No Raspberry Pi cameras found via global_camera_info()")
                
        except AttributeError:
            # Fallback: Try to create a Picamera2 instance to test if camera exists
            print("Using fallback method to detect Raspberry Pi camera...")
            try:
                test_cam = Picamera2()
                camera_info = {
                    'id': 0,
                    'model': 'Raspberry Pi Camera',
                    'type': 'raspi',
                    'location': 'embedded',
                    'rotation': 0,
                    'display_name': 'Raspberry Pi Camera 0'
                }
                cameras.append(camera_info)
                print(f"Found Raspberry Pi camera: {camera_info['display_name']}")
                test_cam.close()
            except Exception as e:
                print(f"No Raspberry Pi camera detected: {e}")
        
        if not cameras:
            print("No Raspberry Pi cameras found")
            
        return cameras
        
    except Exception as e:
        print(f"Error listing Raspberry Pi cameras: {e}")
        import traceback
        traceback.print_exc()
        return []


def list_available_cameras():
    """List available cameras (both TIS and Raspberry Pi).
    
    Returns cameras based on configured camera type, or all cameras if not specified.
    """
    all_cameras = []
    
    # Check configured camera type
    try:
        camera_type = get_camera_type()
    except:
        camera_type = None
    
    if camera_type == "RASPI" or camera_type is None:
        # List Raspberry Pi cameras
        raspi_cameras = list_available_raspi_cameras()
        all_cameras.extend(raspi_cameras)
    
    if camera_type == "TIS" or camera_type is None:
        # List TIS cameras
        tis_cameras = list_available_tis_cameras()
        all_cameras.extend(tis_cameras)
    
    return all_cameras


def list_available_tis_cameras():
    """List available TIS industrial cameras."""
    if TIS is None or Gst is None:
        print("TIS module or GStreamer not available")
        return []
    
    try:
        # Use the DeviceMonitor from TIS module pattern
        monitor = Gst.DeviceMonitor.new()
        monitor.add_filter("Video/Source/tcam")
        devices = monitor.get_devices()
        
        cameras = []
        for device in devices:
            properties = device.get_properties()
            if properties:
                serial = properties.get_string("serial")
                model = properties.get_string("model") 
                type_str = properties.get_string("type")
                
                camera_info = {
                    'serial': serial or "Unknown",
                    'model': model or "TIS Camera", 
                    'type': type_str or "tcam",
                    'display_name': f"{model or 'TIS Camera'} ({serial or 'No Serial'})"
                }
                cameras.append(camera_info)
                print(f"Found TIS camera: {camera_info['display_name']}")
        
        if not cameras:
            print("No TIS cameras found")
            
        return cameras
        
    except Exception as e:
        print(f"Error listing TIS cameras: {e}")
        import traceback
        traceback.print_exc()
        return []

def validate_image(img):
    """Validate captured image quality."""
    if img is None:
        return False, "Image is None"
    
    if len(img.shape) != 3:
        return False, f"Invalid image shape: {img.shape}"
    
    height, width, channels = img.shape
    if height < 100 or width < 100:
        return False, f"Image too small: {width}x{height}"
    
    # Convert to grayscale for analysis
    if channels == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Check brightness (average pixel value)
    avg_brightness = np.mean(gray)
    if avg_brightness < IMAGE_MIN_BRIGHTNESS:
        return False, f"Image too dark: brightness={avg_brightness:.1f}"
    if avg_brightness > IMAGE_MAX_BRIGHTNESS:
        return False, f"Image too bright: brightness={avg_brightness:.1f}"
    
    # Check contrast (standard deviation)
    contrast = np.std(gray)
    if contrast < IMAGE_MIN_CONTRAST:
        return False, f"Image has low contrast: std={contrast:.1f}"
    
    return True, "Image validation passed"

def initialize_camera(serial="", width=CAMERA_WIDTH, height=CAMERA_HEIGHT, fps=CAMERA_FPS, format_type="BGRA", color=False, initial_focus=None, initial_exposure=None):
    """Initialize camera with optional initial settings for optimal fast capture.
    
    Automatically detects camera type from config and initializes the appropriate camera.
    
    Args:
        serial: Camera serial number (TIS only)
        width: Image width
        height: Image height  
        fps: Frames per second (TIS only)
        format_type: Image format ("BGRA", "BGRX", "GRAY8", "GRAY16_LE") - TIS only
        color: Color mode
        initial_focus: Initial focus value (if provided, sets camera to this value during init) - TIS only
        initial_exposure: Initial exposure value (if provided, sets camera to this value during init) - TIS only
        
    Returns:
        True if successful, False otherwise
    """
    # Detect camera type from config
    camera_type = get_camera_type()
    print(f"Initializing camera type: {camera_type}")
    
    if is_raspi_camera():
        return initialize_raspi_camera(width, height)
    else:
        return initialize_tis_camera(serial, width, height, fps, format_type, color, initial_focus, initial_exposure)


def initialize_tis_camera(serial="", width=CAMERA_WIDTH, height=CAMERA_HEIGHT, fps=CAMERA_FPS, format_type="BGRA", color=False, initial_focus=None, initial_exposure=None):
    """Initialize TIS industrial camera with optional initial settings for optimal fast capture.
    
    Args:
        serial: Camera serial number
        width: Image width
        height: Image height  
        fps: Frames per second
        format_type: Image format ("BGRA", "BGRX", "GRAY8", "GRAY16_LE")
        color: Color mode
        initial_focus: Initial focus value (if provided, sets camera to this value during init)
        initial_exposure: Initial exposure value (if provided, sets camera to this value during init)
        
    Returns:
        True if successful, False otherwise
    """
    global Tis, DEFAULT_FOCUS, DEFAULT_EXPOSURE
    
    try:
        # Create TIS camera instance
        if TIS is None:
            error_msg = "❌ CAMERA ERROR: TIS module not available. Please ensure TIS camera SDK is properly installed."
            print(error_msg)
            raise RuntimeError(error_msg)
            
        Tis = TIS.TIS()  # Correct way to instantiate the TIS class from TIS module
        
        # Convert format string to SinkFormats enum
        format_map = {
            "BGRA": TIS.SinkFormats.BGRA,
            "BGRX": TIS.SinkFormats.BGRX,
            "BGR": TIS.SinkFormats.BGRA,  # Map BGR to BGRA for compatibility
            "GRAY8": TIS.SinkFormats.GRAY8,
            "GRAY16_LE": TIS.SinkFormats.GRAY16_LE
        }
        
        sink_format = format_map.get(format_type, TIS.SinkFormats.BGRA)
        print(f"Using sink format: {sink_format} (from format_type: {format_type})")
        
        # Open the camera with specified parameters
        if not Tis.open_device(serial, width, height, fps, sink_format, color):
            error_msg = f"❌ CAMERA ERROR: Failed to open TIS camera device (Serial: {serial or 'auto-detect'})"
            print(error_msg)
            print("   Troubleshooting:")
            print("   1. Check if camera is physically connected")
            print("   2. Verify camera serial number is correct")
            print("   3. Ensure no other application is using the camera")
            print("   4. Check camera permissions (user in 'video' group)")
            Tis = None
            raise RuntimeError(error_msg)
        
        # Start pipeline - this must reach PLAYING state for captures to work
        if not Tis.start_pipeline():
            error_msg = "❌ CAMERA PIPELINE ERROR: Failed to start TIS camera pipeline"
            print(error_msg)
            print("   Troubleshooting:")
            print("   1. Check if GStreamer is properly installed")
            print("   2. Verify camera firmware is up to date")
            print("   3. Check system logs for GStreamer errors: journalctl -xe")
            Tis = None
            raise RuntimeError(error_msg)
        
        # CRITICAL: Wait for pipeline to stabilize in PLAYING state before property setting
        # This matches the successful simple script pattern
        print("Waiting for pipeline to stabilize in PLAYING state...")
        import time
        time.sleep(2)  # Same delay as working simple script
        
        # Now that pipeline is stable in PLAYING state, configure camera
        print("Pipeline stable, configuring camera for manual mode...")
        
        # CRITICAL: Disable ALL auto modes first for stable operation
        # This must be done BEFORE setting any manual properties
        disable_all_auto_modes()
        
        # Determine initial settings - use provided values or defaults
        focus_value = initial_focus if initial_focus is not None else DEFAULT_FOCUS
        exposure_value = initial_exposure if initial_exposure is not None else DEFAULT_EXPOSURE
        
        print(f"\nSetting manual camera properties:")
        print(f"  Focus: {focus_value}")
        print(f"  Exposure: {exposure_value}")
        
        # Set initial camera properties for optimal fast capture
        success = set_camera_properties(
            focus=focus_value,
            exposure_time=exposure_value,
            skip_settle_delay=True  # Skip delay during init
        )
        
        if success:
            print(f"✅ Camera properties set successfully")
        else:
            print("⚠️  Warning: Some camera properties failed to set")
        
        print("✅ Camera initialized in FULL MANUAL MODE - ready for stable operation")
        return True
        
    except RuntimeError as e:
        # Re-raise RuntimeError with our informative messages
        Tis = None
        raise
    except Exception as e:
        error_msg = f"❌ CAMERA INITIALIZATION ERROR: Unexpected error during camera initialization"
        print(error_msg)
        print(f"   Error details: {str(e)}")
        print("   Troubleshooting:")
        print("   1. Check system logs for detailed error information")
        print("   2. Verify all camera SDK dependencies are installed")
        print("   3. Try power-cycling the camera")
        import traceback
        traceback.print_exc()
        Tis = None
        raise RuntimeError(f"{error_msg}: {str(e)}")


def initialize_raspi_camera(width=1920, height=1080):
    """Initialize Raspberry Pi Camera.
    
    The Raspi Camera does NOT need focus and brightness adjustment steps,
    so they are automatically skipped based on config.
    
    Args:
        width: Image width (default: 1920)
        height: Image height (default: 1080)
        
    Returns:
        True if successful, False otherwise
    """
    global PiCam
    
    try:
        if not PICAMERA2_AVAILABLE or Picamera2 is None:
            error_msg = "❌ CAMERA ERROR: Picamera2 module not available. Please install: sudo apt install -y python3-picamera2"
            print(error_msg)
            raise RuntimeError(error_msg)
        
        print("Initializing Raspberry Pi Camera...")
        
        # Clean up existing camera instance if present
        if PiCam is not None:
            print("Cleaning up existing Raspberry Pi Camera instance...")
            try:
                PiCam.stop()
            except Exception:
                pass
            try:
                PiCam.close()
            except Exception:
                pass
            PiCam = None
            time.sleep(0.5)  # Brief wait for camera release
        
        # Get Raspi Camera configuration
        raspi_config = get_raspi_camera_config()
        if raspi_config:
            width = raspi_config.get('width', width)
            height = raspi_config.get('height', height)
        
        # Create Picamera2 instance
        PiCam = Picamera2()
        
        # Configure camera
        config = PiCam.create_still_configuration(
            main={"size": (width, height), "format": "RGB888"}
        )
        PiCam.configure(config)
        
        # Start camera
        PiCam.start()
        
        # Brief wait for camera to stabilize
        time.sleep(1)
        
        print(f"✅ Raspberry Pi Camera initialized successfully ({width}x{height})")
        print("   NOTE: Focus and brightness adjustments are SKIPPED for Raspi Camera (per config)")
        
        return True
        
    except Exception as e:
        error_msg = f"❌ RASPI CAMERA INITIALIZATION ERROR: {str(e)}"
        print(error_msg)
        print("   Troubleshooting:")
        print("   1. Check if camera is enabled: sudo raspi-config")
        print("   2. Verify camera is connected properly")
        print("   3. Ensure picamera2 is installed: sudo apt install -y python3-picamera2")
        print("   4. Check camera permissions")
        import traceback
        traceback.print_exc()
        PiCam = None
        raise RuntimeError(f"{error_msg}: {str(e)}")
        print("   2. Verify all camera SDK dependencies are installed")
        print("   3. Try power-cycling the camera")
        import traceback
        traceback.print_exc()
        Tis = None
        raise RuntimeError(f"{error_msg}: {str(e)}")

def capture_image_fast(camera=None):
    """Fast capture using current camera settings (no property changes or delays).
    
    This function assumes the camera is already configured with the correct
    focus and exposure settings. It performs an immediate capture without
    applying any settings changes or settle delays.
    
    For Raspi Camera: Always uses fast capture as no focus/brightness adjustments needed.
    For TIS Camera: Uses fast capture only when camera already at desired settings.
    
    Use this when:
    - Camera was just initialized with desired settings
    - Capturing first ROI group (camera already at those settings)
    - Need fastest possible capture time
    - Using Raspi Camera (always fast)
    
    Args:
        camera: Camera instance (for compatibility, not used currently)
        
    Returns:
        Captured image or None
    """
    if is_raspi_camera():
        print("Fast capture: Raspi Camera (no focus/brightness adjustments needed)")
        return capture_raspi_image()
    else:
        print("Fast capture: using current TIS camera settings (no changes, no delay)")
        return capture_tis_image_fast()

def capture_image(camera=None, focus=None, exposure_time=None):
    """Standard capture wrapper that applies specified or config settings.
    
    For Raspi Camera: Focus and exposure parameters are IGNORED (per config).
    For TIS Camera: Applies focus and exposure settings before capture.
    
    Args:
        camera: Camera instance (for compatibility)
        focus: Focus value to use (TIS only, defaults to config)
        exposure_time: Exposure time to use (TIS only, defaults to config)
        
    Returns:
        Captured image or None
    """
    if is_raspi_camera():
        # Raspi Camera: Ignore focus/exposure parameters
        if focus is not None or exposure_time is not None:
            print("Note: Focus and exposure parameters ignored for Raspi Camera (per config)")
        return capture_raspi_image()
    else:
        # TIS Camera: Apply settings
        global Tis
        
        # Use config defaults if not specified
        focus = focus or DEFAULT_FOCUS
        exposure_time = exposure_time or DEFAULT_EXPOSURE
        
        print(f"Applying TIS camera settings before capture:")
        print(f"  Focus: {focus}")
        print(f"  Exposure: {exposure_time}")
        
        # Set camera properties (skip settle delay based on config)
        skip_delay = should_skip_focus_adjust()
        success = set_camera_properties(focus=focus, exposure_time=exposure_time, skip_settle_delay=skip_delay)
        if not success:
            print("Warning: Some camera properties failed to apply")
        
        # Capture image
        return capture_tis_image()
    if not success:
        print("Warning: Failed to set some camera properties, continuing with capture...")
    
    # Use standard capture with retries
    return capture_tis_image()

def capture_tis_image_fast():
    """Fast capture an image from the TIS camera using current settings without delays.
    
    IMPORTANT: This function ensures a NEW frame is captured each time.
    The TIS snap_image() call clears old data before pulling a fresh frame.
    """
    if not ENABLE_FAST_CAPTURE:
        print("Fast capture optimization disabled, using normal capture")
        return capture_tis_image()
    
    if Tis is None:
        error_msg = "❌ CAPTURE ERROR: Camera not initialized. Please initialize the camera first."
        print(error_msg)
        raise RuntimeError(error_msg)
    
    try:
        print("Fast capture: Requesting NEW frame from camera...")
        
        # CRITICAL: snap_image() clears old img_mat and captures fresh frame
        # This ensures we never use cached/stale images
        raw_data = Tis.snap_image(timeout=5, convert_to_mat=True)
        if raw_data is None:
            error_msg = "❌ CAPTURE ERROR: Camera failed to capture new frame (snap_image returned None)"
            print(error_msg)
            print("   Possible causes:")
            print("   1. Camera pipeline may not be in PLAYING state")
            print("   2. Camera may have been disconnected")
            print("   3. Timeout occurred waiting for frame (5 seconds)")
            print("   Suggestion: Try re-initializing the camera")
            raise RuntimeError(error_msg)
        
        # Get the newly captured image (snap_image set this to fresh data)
        img = Tis.get_image()
        if img is None:
            error_msg = "❌ CAPTURE ERROR: Failed to retrieve image from camera buffer (get_image returned None)"
            print(error_msg)
            print("   Possible causes:")
            print("   1. Image buffer may be empty")
            print("   2. Memory allocation issue")
            print("   Suggestion: Try re-initializing the camera")
            raise RuntimeError(error_msg)
        
        # Make a copy to ensure we don't accidentally keep references to internal buffers
        img = img.copy()
        print(f"✓ Fresh image copied from camera buffer")
        
        # Convert BGRA to BGR like main_old.py does
        if len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Validate image quality
        is_valid, validation_msg = validate_image(img)
        if not is_valid:
            error_msg = f"❌ IMAGE VALIDATION ERROR: {validation_msg}"
            print(error_msg)
            print("   Possible causes:")
            print("   1. Camera settings (exposure/focus) may need adjustment")
            print("   2. Lighting conditions may be poor")
            print("   3. Camera lens may be obstructed or dirty")
            print("   Suggestion: Check camera settings and lighting")
            raise RuntimeError(error_msg)
        
        print(f"✓ Fast capture successful: {validation_msg}")
        return img
        
    except RuntimeError as e:
        # Re-raise RuntimeError with our informative messages
        raise
    except Exception as e:
        error_msg = f"❌ FAST CAPTURE ERROR: Unexpected error during image capture"
        print(error_msg)
        print(f"   Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"{error_msg}: {str(e)}")

def capture_tis_image():
    """Capture an image from the TIS camera with retry mechanism and validation."""
    if Tis is None:
        error_msg = "❌ CAPTURE ERROR: Camera not initialized. Please initialize the camera first."
        print(error_msg)
        raise RuntimeError(error_msg)
    
    for attempt in range(1, CAMERA_RETRY_ATTEMPTS + 1):
        try:
            print(f"Capture attempt {attempt}/{CAMERA_RETRY_ATTEMPTS}")
            
            # Check and handle pipeline state before capture - simplified approach
            if hasattr(Tis, 'pipeline') and Tis.pipeline is not None:
                try:
                    # Get current state
                    ret, current_state, pending = Tis.pipeline.get_state(1000000000)  # 1 second timeout
                    print(f"Pipeline state: {current_state} (3=PAUSED, 4=PLAYING)")
                    
                    if current_state == 3:  # PAUSED state
                        print("Pipeline in PAUSED state - capture will use temporary PLAYING mode")
                    
                except Exception as state_e:
                    print(f"Pipeline state check failed: {state_e}")
            
            # CRITICAL: Attempt to capture NEW image with increased timeout for problematic states
            # snap_image() clears old data and pulls fresh frame from camera
            timeout = 10 if attempt > 1 else 5  # Increase timeout on retries
            print(f"Attempt {attempt}: Requesting NEW frame with timeout={timeout}s")
            raw_data = Tis.snap_image(timeout=timeout, convert_to_mat=True)
            
            if raw_data is None:
                print(f"ERROR: TIS snap_image returned None on attempt {attempt} - no new frame")
                if attempt < CAMERA_RETRY_ATTEMPTS:
                    print(f"Retrying in {CAMERA_RETRY_DELAY}s...")
                    time.sleep(CAMERA_RETRY_DELAY)
                    continue
                else:
                    print("All capture attempts failed at snap_image stage")
                    return None
            
            # Get the newly captured image
            img = Tis.get_image()
            if img is None:
                print(f"ERROR: TIS get_image returned None on attempt {attempt}")
                if attempt < CAMERA_RETRY_ATTEMPTS:
                    print(f"Retrying in {CAMERA_RETRY_DELAY}s...")
                    time.sleep(CAMERA_RETRY_DELAY)
                    continue
                else:
                    print("All capture attempts failed at get_image stage")
                    return None
            
            # Make a copy to ensure we don't accidentally keep references to internal buffers
            # This is critical to prevent any possibility of stale data
            img = img.copy()
            print(f"✓ Fresh image copied from camera buffer (attempt {attempt})")
            
            # Convert BGRA to BGR like main_old.py does
            if len(img.shape) == 3 and img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # Validate image quality
            is_valid, validation_msg = validate_image(img)
            if not is_valid:
                print(f"Image validation failed on attempt {attempt}: {validation_msg}")
                if attempt < CAMERA_RETRY_ATTEMPTS:
                    print(f"Retrying in {CAMERA_RETRY_DELAY}s...")
                    time.sleep(CAMERA_RETRY_DELAY)
                    continue
                else:
                    print("All capture attempts failed validation")
                    return None
            
            print(f"Image captured successfully on attempt {attempt}: {validation_msg}")
            return img
            
        except Exception as e:
            print(f"Exception in capture attempt {attempt}: {e}")
            if attempt < CAMERA_RETRY_ATTEMPTS:
                print(f"Retrying in {CAMERA_RETRY_DELAY}s...")
                time.sleep(CAMERA_RETRY_DELAY)
                continue
            else:
                print("All capture attempts failed with exceptions")
                import traceback
                traceback.print_exc()
                return None
    
    return None

def capture_raspi_image():
    """Capture an image from the Raspberry Pi Camera.
    
    NOTE: Raspi Camera does NOT require focus/brightness adjustments.
    These steps are automatically skipped based on config settings.
    
    Returns:
        Captured image in BGR format or None if capture fails
    """
    global PiCam
    
    if PiCam is None:
        error_msg = "❌ CAPTURE ERROR: Raspberry Pi Camera not initialized. Please initialize the camera first."
        print(error_msg)
        raise RuntimeError(error_msg)
    
    try:
        print("Capturing image from Raspberry Pi Camera...")
        
        # Capture image from Picamera2
        # capture_array returns RGB format
        img_rgb = PiCam.capture_array()
        
        if img_rgb is None:
            error_msg = "❌ CAPTURE ERROR: Raspberry Pi Camera returned None"
            print(error_msg)
            raise RuntimeError(error_msg)
        
        # Convert RGB to BGR for OpenCV compatibility
        img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        
        # Validate image quality
        is_valid, validation_msg = validate_image(img)
        if not is_valid:
            error_msg = f"❌ IMAGE VALIDATION ERROR: {validation_msg}"
            print(error_msg)
            print("   Possible causes:")
            print("   1. Lighting conditions may be poor")
            print("   2. Camera lens may be obstructed or dirty")
            print("   3. Camera may need reconfiguration")
            raise RuntimeError(error_msg)
        
        print(f"✓ Raspi Camera capture successful: {validation_msg}")
        print("   NOTE: Focus and brightness adjustments were SKIPPED (per config)")
        return img
        
    except RuntimeError as e:
        # Re-raise RuntimeError with our informative messages
        raise
    except Exception as e:
        error_msg = f"❌ RASPI CAPTURE ERROR: Unexpected error during image capture"
        print(error_msg)
        print(f"   Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"{error_msg}: {str(e)}")


def discover_exposure_property_name():
    """Discover the correct exposure property name for this camera.
    
    Different TIS camera models use different property names:
    - Exposure Auto Reference
    - ExposureTime  
    - Exposure
    - ExposureTimeAbs
    
    Returns:
        str: The correct property name, or None if not found
    """
    global _exposure_property_name, Tis
    
    if _exposure_property_name is not None:
        return _exposure_property_name
    
    if Tis is None:
        return None
    
    try:
        # Get all available property names
        property_names = Tis.source.get_tcam_property_names()
        
        # Common exposure property name patterns
        exposure_patterns = [
            "Exposure Time (us)",  # Common format with units
            "ExposureTime",
            "Exposure",
            "ExposureTimeAbs",
            "Exposure Auto Reference"
        ]
        
        # Try exact matches first
        for pattern in exposure_patterns:
            if pattern in property_names:
                _exposure_property_name = pattern
                print(f"✓ Discovered exposure property: '{_exposure_property_name}'")
                
                # Get property details for debugging
                try:
                    prop = Tis.source.get_tcam_property(pattern)
                    prop_type = type(prop).__name__
                    print(f"  Property type: {prop_type}")
                    
                    # Try to get min/max if it's a range property
                    if hasattr(prop, 'get_range'):
                        min_val, max_val = prop.get_range()
                        print(f"  Valid range: {min_val} - {max_val}")
                    
                    # Check current value
                    current = Tis.get_property(pattern)
                    print(f"  Current value: {current}")
                except Exception as e:
                    print(f"  (Could not get property details: {e})")
                
                return _exposure_property_name
        
        # Try substring matches for properties containing "Exposure" and "Time"
        for prop_name in property_names:
            prop_lower = prop_name.lower()
            if "exposure" in prop_lower and "time" in prop_lower:
                _exposure_property_name = prop_name
                print(f"✓ Discovered exposure property (pattern match): '{_exposure_property_name}'")
                return _exposure_property_name
        
        # Last resort: any property with "exposure" in the name
        for prop_name in property_names:
            if "exposure" in prop_name.lower():
                _exposure_property_name = prop_name
                print(f"⚠ Using fallback exposure property: '{_exposure_property_name}'")
                return _exposure_property_name
        
        print("❌ No exposure property found on camera")
        print("Available properties:", property_names)
        return None
        
    except Exception as e:
        print(f"Error discovering exposure property: {e}")
        return None

def disable_all_auto_modes():
    """Disable ALL automatic modes to ensure stable manual control.
    
    Disables:
    - Auto Exposure
    - Auto Gain
    - Auto White Balance
    - Auto Focus (if exists)
    - Auto Brightness
    - Auto Iris (if exists)
    
    This ensures the camera operates in fully manual mode for maximum
    stability and repeatability in industrial AOI applications.
    
    Returns:
        bool: True if all found auto modes disabled, False on error
    """
    global Tis
    
    if Tis is None:
        print("⚠️  Camera not initialized, cannot disable auto modes")
        return False
    
    try:
        property_names = Tis.source.get_tcam_property_names()
        print("\n🔧 Disabling ALL automatic modes for stable operation...")
        
        # Define all possible auto mode property names and their off values
        auto_properties = {
            # Auto Exposure
            "Exposure Auto": ["Off", False, 0],
            "ExposureAuto": ["Off", False, 0],
            "Exposure_Auto": ["Off", False, 0],
            
            # Auto Gain
            "Gain Auto": ["Off", False, 0],
            "GainAuto": ["Off", False, 0],
            "Gain_Auto": ["Off", False, 0],
            
            # Auto White Balance
            "White Balance Auto": ["Off", False, 0],
            "WhiteBalanceAuto": ["Off", False, 0],
            "White_Balance_Auto": ["Off", False, 0],
            "Whitebalance Auto": ["Off", False, 0],
            "Balance White Auto": ["Off", False, 0],
            
            # Auto Focus (rare but exists on some models)
            "Focus Auto": ["Off", False, 0],
            "FocusAuto": ["Off", False, 0],
            "Focus_Auto": ["Off", False, 0],
            
            # Auto Brightness (rare)
            "Brightness Auto": ["Off", False, 0],
            "BrightnessAuto": ["Off", False, 0],
            
            # Auto Iris (for cameras with iris control)
            "Iris Auto": ["Off", False, 0],
            "IrisAuto": ["Off", False, 0],
        }
        
        disabled_count = 0
        found_count = 0
        
        for prop_name, off_values in auto_properties.items():
            if prop_name in property_names:
                found_count += 1
                try:
                    current = Tis.get_property(prop_name)
                    print(f"  Found {prop_name}, current value: {current}")
                    
                    # Try each possible off value
                    disabled = False
                    for off_value in off_values:
                        try:
                            Tis.set_property(prop_name, off_value)
                            new_value = Tis.get_property(prop_name)
                            print(f"    ✓ Disabled {prop_name} (set to {off_value}, confirmed: {new_value})")
                            disabled = True
                            disabled_count += 1
                            break
                        except Exception as set_error:
                            continue
                    
                    if not disabled:
                        print(f"    ⚠️  Found {prop_name} but couldn't disable it with any value")
                        
                except Exception as e:
                    print(f"    ⚠️  Error checking {prop_name}: {e}")
        
        if found_count == 0:
            print("  ℹ️  No auto mode properties found (camera may already be manual-only)")
            return True
        
        print(f"\n✅ Auto mode configuration complete: {disabled_count}/{found_count} auto modes disabled")
        return True
        
    except Exception as e:
        print(f"❌ Error disabling auto modes: {e}")
        import traceback
        traceback.print_exc()
        return False


def disable_exposure_auto():
    """Disable automatic exposure mode to allow manual control.
    
    DEPRECATED: Use disable_all_auto_modes() instead for comprehensive control.
    Kept for backward compatibility.
    
    Many TIS cameras have an Exposure Auto mode that must be disabled
    before manual exposure values can be set.
    
    Returns:
        bool: True if disabled successfully or not needed, False on error
    """
    global Tis
    
    if Tis is None:
        return False
    
    try:
        property_names = Tis.source.get_tcam_property_names()
        
        # Common auto exposure property names
        auto_exposure_names = [
            "Exposure Auto",
            "ExposureAuto", 
            "Exposure_Auto"
        ]
        
        for prop_name in auto_exposure_names:
            if prop_name in property_names:
                try:
                    current = Tis.get_property(prop_name)
                    print(f"Found {prop_name}, current value: {current}")
                    
                    # Try to set to Off/False/0
                    for off_value in [False, "Off", 0]:
                        try:
                            Tis.set_property(prop_name, off_value)
                            print(f"✓ Disabled {prop_name} (set to {off_value})")
                            return True
                        except:
                            continue
                    
                    print(f"⚠ Found {prop_name} but couldn't disable it")
                except Exception as e:
                    print(f"Error checking {prop_name}: {e}")
        
        # No auto exposure property found - probably already manual
        return True
        
    except Exception as e:
        print(f"Error disabling exposure auto: {e}")
        return False

def set_camera_properties(focus=None, exposure_time=None, skip_settle_delay=False):
    """Set camera focus and exposure properties.
    
    For Raspi Camera: This function is a no-op (properties are ignored).
    For TIS Camera: Sets focus and exposure with optional settle delay.
    
    Args:
        focus: Focus value to set (TIS only)
        exposure_time: Exposure time to set (TIS only)
        skip_settle_delay: If True, skip the settle delay for faster operation
    """
    # Skip for Raspi Camera
    if is_raspi_camera():
        if focus is not None or exposure_time is not None:
            print("Note: Camera property setting skipped for Raspi Camera (per config)")
        return True
    
    # TIS Camera property setting
    if Tis is None:
        return False
        
    try:
        success = True
        settings_changed = False
        
        if focus is not None:
            try:
                Tis.set_property("Focus", int(focus))
                print(f"Focus set to: {focus}")
                settings_changed = True
            except Exception as e:
                print(f"Warning: Failed to set Focus to {focus}: {e}")
                success = False
                
        if exposure_time is not None:
            try:
                # Note: Auto modes should already be disabled during initialization
                # but we keep this as a safety check for runtime property changes
                
                # Discover the correct exposure property name if not cached
                exposure_prop = discover_exposure_property_name()
                
                if exposure_prop:
                    try:
                        # Convert to integer and set the property
                        exposure_value = int(exposure_time)
                        Tis.set_property(exposure_prop, exposure_value)
                        print(f"{exposure_prop} set to: {exposure_value}")
                        settings_changed = True
                    except Exception as e:
                        # Get more details about the error
                        print(f"Warning: Failed to set {exposure_prop} to {exposure_time}")
                        print(f"  Error details: {e}")
                        
                        # Try to get current value and range
                        try:
                            current = Tis.get_property(exposure_prop)
                            print(f"  Current value: {current}")
                            prop = Tis.source.get_tcam_property(exposure_prop)
                            if hasattr(prop, 'get_range'):
                                min_val, max_val = prop.get_range()
                                print(f"  Valid range: {min_val} - {max_val}")
                                print(f"  Requested value {exposure_time} is {'within' if min_val <= exposure_time <= max_val else 'OUTSIDE'} range")
                        except:
                            pass
                        
                        success = False
                else:
                    print(f"Warning: Could not set exposure to {exposure_time} - property not found")
                    success = False
                    
            except Exception as e:
                print(f"Warning: Failed to set exposure to {exposure_time}: {e}")
                success = False
        
        # Add delay after camera settings change to ensure camera works properly
        # Skip delay if requested (e.g., when using default values on first capture)
        # OR if config says to skip focus adjust (for Raspi Camera compatibility mode)
        if settings_changed and not skip_settle_delay and not should_skip_focus_adjust():
            print(f"Waiting {FOCUS_SETTLE_DELAY}s for camera to settle after settings change...")
            time.sleep(FOCUS_SETTLE_DELAY)
        elif settings_changed and (skip_settle_delay or should_skip_focus_adjust()):
            print("Skipping settle delay for faster operation...")
                
        return success
    except Exception as e:
        print(f"Error setting camera properties: {e}")
        return False

def get_camera_instance():
    """Get the global camera instance (TIS or Raspi based on config)."""
    if is_raspi_camera():
        return PiCam
    else:
        return Tis


def start_live_view():
    """Start live view mode for camera (TIS or Raspi)."""
    try:
        if is_raspi_camera():
            global PiCam
            if PiCam is None:
                print("Error: Raspi Camera not initialized")
                return False
            print("Live view mode activated (Raspi Camera)")
            return True
        else:
            global Tis
            if Tis is None:
                print("Error: TIS Camera not initialized")
                return False
            # For TIS cameras, live view is typically managed by the streaming pipeline
            # The camera is already in "live" mode when initialized with streaming
            print("Live view mode activated (TIS Camera)")
            return True
        
    except Exception as e:
        print(f"Error starting live view: {e}")
        return False


def stop_live_view():
    """Stop live view mode for camera (TIS or Raspi)."""
    try:
        if is_raspi_camera():
            global PiCam
            if PiCam is None:
                print("Warning: Raspi Camera not initialized")
                return True
            print("Live view mode deactivated (Raspi Camera)")
            return True
        else:
            global Tis
            if Tis is None:
                print("Warning: TIS Camera not initialized")
                return True
            # For TIS cameras, we don't typically stop the streaming pipeline
            # unless we're shutting down the camera completely
            print("Live view mode deactivated (TIS Camera)")
            return True
        
    except Exception as e:
        print(f"Error stopping live view: {e}")
        return False


def get_camera_status():
    """Get current camera and pipeline status.
    
    Works for both TIS and Raspi cameras.
    
    Returns:
        dict: Status information including:
            - initialized: bool
            - camera_type: str (TIS or RASPI)
            - pipeline_active: bool (TIS only)
            - pipeline_state: str (TIS only)
            - serial: str or None (TIS only)
    """
    status = {
        'initialized': False,
        'camera_type': get_camera_type(),
        'pipeline_active': False,
        'pipeline_state': 'NONE',
        'serial': None
    }
    
    if is_raspi_camera():
        global PiCam
        if PiCam is None:
            print("📷 Camera status check: No Raspi Camera initialized")
            return status
        
        try:
            status['initialized'] = True
            # Raspi Camera doesn't have pipeline concept
            status['pipeline_active'] = True
            status['pipeline_state'] = 'RUNNING'
            print("📷 Raspi Camera status: Initialized and running")
            return status
        except Exception as e:
            print(f"Error getting Raspi Camera status: {e}")
            return status
    
    else:
        # TIS Camera status check
        global Tis
        
        if Tis is None:
            print("📷 Camera status check: No TIS Camera initialized")
            return status
        
        try:
            status['initialized'] = True
            
            # Check if pipeline exists and get its state
            if hasattr(Tis, 'pipeline') and Tis.pipeline is not None:
                try:
                    ret, current_state, pending = Tis.pipeline.get_state(1000000000)  # 1 second timeout
                    status['pipeline_active'] = True
                    
                    # Convert GStreamer state to readable string
                    state_names = {
                        1: 'NULL',
                        2: 'READY',
                        3: 'PAUSED',
                        4: 'PLAYING'
                    }
                    status['pipeline_state'] = state_names.get(int(current_state), 'UNKNOWN')
                    
                    # Add warning if pipeline state is not optimal
                    if int(current_state) != 4:  # Not PLAYING
                        print(f"⚠️  Warning: Pipeline state is {status['pipeline_state']}, expected PLAYING")
                        print("   This may cause capture issues. Try re-initializing the camera.")
                        
                except Exception as e:
                    error_msg = f"❌ PIPELINE STATE ERROR: Failed to get pipeline state: {e}"
                    print(error_msg)
                    print("   Possible causes:")
                    print("   1. Pipeline may have crashed")
                    print("   2. GStreamer internal error")
                    print("   Suggestion: Re-initialize the camera")
                    status['pipeline_state'] = 'ERROR'
            else:
                print("⚠️  Warning: TIS Camera initialized but no pipeline found")
            
            # Try to get serial from device
            if hasattr(Tis, 'serialnumber'):
                status['serial'] = Tis.serialnumber
                
        except Exception as e:
            error_msg = f"❌ STATUS CHECK ERROR: Error getting camera status"
            print(error_msg)
            print(f"   Error details: {str(e)}")
            status['pipeline_state'] = 'ERROR'
    
    return status


def stop_camera_pipeline():
    """Stop camera pipeline gracefully without clearing the camera instance.
    
    This is useful for temporarily stopping the pipeline before applying new settings.
    For Raspi Camera: This is a no-op.
    
    Returns:
        bool: True if successful, False otherwise
    """
    if is_raspi_camera():
        print("📷 Stop pipeline: No-op for Raspi Camera")
        return True
    
    global Tis
    
    try:
        if Tis is None:
            print("📷 No TIS camera to stop (camera not initialized)")
            return True
        
        print("⏸️  Stopping camera pipeline...")
        
        # Stop the pipeline if it exists
        if hasattr(Tis, 'pipeline') and Tis.pipeline is not None:
            try:
                # Get current state
                ret, current_state, pending = Tis.pipeline.get_state(1000000000)
                state_names = {1: 'NULL', 2: 'READY', 3: 'PAUSED', 4: 'PLAYING'}
                current_state_name = state_names.get(int(current_state), 'UNKNOWN')
                print(f"  Current pipeline state: {current_state_name}")
                
                if int(current_state) == 1:  # NULL
                    print("  Pipeline already in NULL state, no stop needed")
                    return True
                else:
                    # Stop pipeline
                    print("  Stopping pipeline...")
                    Tis.stop_pipeline()
                    
                    # Wait for pipeline to stop
                    import time
                    time.sleep(0.5)
                    
                    # Verify pipeline stopped
                    ret, new_state, pending = Tis.pipeline.get_state(1000000000)
                    new_state_name = state_names.get(int(new_state), 'UNKNOWN')
                    print(f"  Pipeline state after stop: {new_state_name}")
                    
                    print("  ✓ Pipeline stopped successfully")
                    return True
            except Exception as e:
                error_msg = f"⚠️  Warning during pipeline stop: {e}"
                print(error_msg)
                print("   Possible causes:")
                print("   1. Pipeline may have already crashed")
                print("   2. GStreamer internal error")
                return False
        else:
            print("  No pipeline found (camera may not be fully initialized)")
            return True
        
    except Exception as e:
        error_msg = f"❌ PIPELINE STOP ERROR: Error stopping camera pipeline"
        print(error_msg)
        print(f"   Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def restart_camera_pipeline():
    """Restart camera pipeline - stop and then start again.
    
    This is more reliable than reset for PLAYING pipelines.
    
    Returns:
        bool: True if successful, False otherwise
    """
    global Tis
    
    try:
        if Tis is None:
            print("📷 No camera to restart (camera not initialized)")
            return False
        
        print("🔄 Restarting camera pipeline...")
        
        # Step 1: Stop the pipeline
        if not stop_camera_pipeline():
            print("  ⚠️  Pipeline stop failed, attempting to start anyway...")
        
        # Step 2: Start the pipeline again
        print("  Starting pipeline...")
        import time
        time.sleep(0.3)  # Brief pause between stop and start
        
        if hasattr(Tis, 'start_pipeline') and callable(Tis.start_pipeline):
            if Tis.start_pipeline():
                # Wait for pipeline to stabilize
                time.sleep(0.5)
                
                # Verify pipeline is PLAYING
                if hasattr(Tis, 'pipeline') and Tis.pipeline is not None:
                    ret, current_state, pending = Tis.pipeline.get_state(1000000000)
                    state_names = {1: 'NULL', 2: 'READY', 3: 'PAUSED', 4: 'PLAYING'}
                    current_state_name = state_names.get(int(current_state), 'UNKNOWN')
                    print(f"  Pipeline state after restart: {current_state_name}")
                    
                    if int(current_state) == 4:  # PLAYING
                        print("✅ Camera pipeline restarted successfully")
                        return True
                    else:
                        print(f"  ⚠️  Pipeline in {current_state_name} state, expected PLAYING")
                        return False
                else:
                    print("  ✓ Pipeline restarted")
                    return True
            else:
                print("  ❌ Failed to start pipeline")
                return False
        else:
            print("  ❌ start_pipeline method not available")
            return False
        
    except Exception as e:
        error_msg = f"❌ PIPELINE RESTART ERROR: Error restarting camera pipeline"
        print(error_msg)
        print(f"   Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def reset_camera_pipeline():
    """Reset camera pipeline - stop existing pipeline and prepare for reinitialization.
    
    This clears the camera instance entirely. For PLAYING pipelines, consider using
    restart_camera_pipeline() instead which is more reliable.
    
    Returns:
        bool: True if successful, False otherwise
    """
    global Tis
    
    try:
        if Tis is None:
            print("📷 No camera to reset (camera not initialized)")
            return True
        
        print("🔄 Resetting camera pipeline...")
        
        # Stop the pipeline first
        stop_camera_pipeline()
        
        # Clear the global Tis reference
        print("  Clearing camera reference...")
        Tis = None
        
        print("✅ Camera pipeline reset completed successfully")
        return True
        
    except Exception as e:
        error_msg = f"❌ PIPELINE RESET ERROR: Error resetting camera pipeline"
        print(error_msg)
        print(f"   Error details: {str(e)}")
        print("   Troubleshooting:")
        print("   1. Camera may need to be power-cycled")
        print("   2. Check system logs for detailed errors")
        print("   3. Restart the application")
        import traceback
        traceback.print_exc()
        
        # Even if error occurred, clear the reference
        Tis = None
        print("  Camera reference cleared despite error")
        return False


def cleanup():
    """Clean up camera resources on shutdown (TIS or Raspi)."""
    global Tis, PiCam
    try:
        if is_raspi_camera():
            if PiCam is None:
                print("Camera cleanup: No Raspi camera to clean up")
                return True
            try:
                PiCam.stop()
            except Exception:
                pass
            try:
                PiCam.close()
            except Exception:
                pass
            PiCam = None
            print("✓ Raspi camera cleanup completed successfully")
            return True

        # TIS camera cleanup
        if Tis is None:
            print("Camera cleanup: No TIS camera to clean up")
            return True
        
        print("Camera cleanup: Stopping TIS pipeline...")
        Tis.stop_pipeline()
        
        # Clear the global Tis reference
        Tis = None
        
        print("✓ Camera cleanup completed successfully")
        return True
        
    except Exception as e:
        print(f"Error during camera cleanup: {e}")
        return False
