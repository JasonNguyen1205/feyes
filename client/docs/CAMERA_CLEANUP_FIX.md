# Camera Cleanup Function Fix

**Date:** October 8, 2025  
**Priority:** 🔧 Bug Fix  
**Status:** ✅ Fixed

## Problem

Application was throwing an error on shutdown:

```
WARNING:__main__:Error during camera cleanup: module 'src.camera' has no attribute 'cleanup'
```

## Root Cause

**File:** `app.py` line 268

The cleanup handler was trying to call `tis_camera.cleanup()`:

```python
# In cleanup_on_shutdown()
try:
    if state.camera_initialized:
        logger.info("Releasing camera resources...")
        tis_camera.cleanup()  # ❌ This function didn't exist
        state.camera_initialized = False
except Exception as exc:
    logger.warning(f"Error during camera cleanup: {exc}")
```

**The Issue:**

- `app.py` imports: `from src import camera as tis_camera`
- `tis_camera` is the `camera.py` module
- The module didn't have a `cleanup()` function
- Only the `TIS.TIS()` class had `stop_pipeline()` method

## Solution

**File:** `src/camera.py`

Added a module-level `cleanup()` function that properly shuts down the camera:

```python
def cleanup():
    """Clean up camera resources on shutdown."""
    global Tis
    try:
        if Tis is None:
            print("Camera cleanup: No camera to clean up")
            return True
        
        print("Camera cleanup: Stopping pipeline...")
        Tis.stop_pipeline()
        
        # Clear the global Tis reference
        Tis = None
        
        print("✓ Camera cleanup completed successfully")
        return True
        
    except Exception as e:
        print(f"Error during camera cleanup: {e}")
        return False
```

## How It Works

**Cleanup Flow:**

```
1. Application shutdown triggered (Ctrl+C, SIGTERM, etc.)
   ↓
2. signal_handler() or cleanup_on_shutdown() called
   ↓
3. Check if camera is initialized
   ↓
4. Call tis_camera.cleanup()
   ↓
5. cleanup() function stops GStreamer pipeline
   ↓
6. Sets Tis = None to release resources
   ↓
7. Returns success
```

**GStreamer Pipeline Shutdown:**

- `Tis.stop_pipeline()` transitions pipeline to PAUSED then READY state
- This releases camera device lock
- Prevents "device busy" errors on restart

## Verification

**Before Fix:**

```bash
$ python3 app.py
# Press Ctrl+C
WARNING:__main__:Error during camera cleanup: module 'src.camera' has no attribute 'cleanup'
```

**After Fix:**

```bash
$ python3 app.py
# Press Ctrl+C
INFO:__main__:Releasing camera resources...
Camera cleanup: Stopping pipeline...
✓ Camera cleanup completed successfully
INFO:__main__:✓ Cleanup completed
```

## Testing

### Test 1: Normal Shutdown

```bash
# Terminal 1
python3 app.py

# Wait for camera to initialize
# Press Ctrl+C

# Expected output:
# INFO:__main__:Received signal SIGINT, shutting down gracefully...
# INFO:__main__:Releasing camera resources...
# Camera cleanup: Stopping pipeline...
# ✓ Camera cleanup completed successfully
```

### Test 2: Multiple Shutdown Attempts

```bash
# Start and stop multiple times
for i in {1..3}; do
    echo "=== Attempt $i ==="
    timeout 5 python3 app.py &
    sleep 3
    kill $!
    sleep 1
done

# Should see clean shutdown each time with no errors
```

### Test 3: Camera Not Initialized

```bash
# Start app and immediately shut down (before camera init)
python3 app.py &
PID=$!
sleep 0.5
kill $PID

# Should see:
# Camera cleanup: No camera to clean up
# (No error messages)
```

## Related Code

### Camera Initialization

**File:** `src/camera.py` line 188

```python
def init_camera():
    global Tis
    # ...
    Tis = TIS.TIS()  # Create camera instance
    # ...
```

### TIS Pipeline Stop

**File:** `src/TIS.py` line 351

```python
def stop_pipeline(self):
    self.pipeline.set_state(Gst.State.PAUSED)
    self.pipeline.set_state(Gst.State.READY)
```

### Cleanup Handler

**File:** `app.py` line 260

```python
def cleanup_on_shutdown():
    """Clean up resources before shutdown."""
    # ...
    try:
        if state.camera_initialized:
            logger.info("Releasing camera resources...")
            tis_camera.cleanup()  # ✅ Now works correctly
            state.camera_initialized = False
    except Exception as exc:
        logger.warning(f"Error during camera cleanup: {exc}")
```

## Benefits

✅ **Proper Resource Cleanup:**

- GStreamer pipeline stopped gracefully
- Camera device released
- No resource leaks

✅ **Clean Application Shutdown:**

- No error messages on exit
- Proper signal handling
- Clean logs

✅ **Prevent Device Lock:**

- Camera properly released
- Can restart application immediately
- No "device busy" errors

✅ **Better Error Handling:**

- Graceful handling of uninitialized camera
- Clear error messages if cleanup fails
- Returns boolean success/failure

## Edge Cases Handled

### 1. Camera Not Initialized

```python
if Tis is None:
    print("Camera cleanup: No camera to clean up")
    return True
```

**Result:** Silent success, no errors

### 2. Pipeline Already Stopped

```python
try:
    Tis.stop_pipeline()
except Exception as e:
    print(f"Error during camera cleanup: {e}")
    return False
```

**Result:** Error logged but doesn't crash

### 3. Multiple Cleanup Calls

```python
Tis = None  # Clears global reference
# Next call will see Tis is None and return early
```

**Result:** Safe to call multiple times

## Summary

### Problem

❌ Missing `cleanup()` function in camera module  
❌ Error on shutdown: "module 'src.camera' has no attribute 'cleanup'"  
❌ Camera resources not properly released  

### Solution

✅ Added module-level `cleanup()` function  
✅ Properly stops GStreamer pipeline  
✅ Clears global Tis reference  
✅ Handles edge cases gracefully  

### Result

🎯 **Clean application shutdown with no errors**  
🛡️ **Proper camera resource cleanup**  
📊 **Safe to restart immediately**

**File Modified:** `src/camera.py` (added `cleanup()` function at line 707)
