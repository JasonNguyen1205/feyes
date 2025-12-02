# Session Management Fix

**Date:** October 6, 2025  
**Status:** ✅ Complete  
**Version:** 1.0

## Problem Statement

Sessions created with the Visual AOI server were not being properly closed, leading to:

- Resource leaks on the server side
- Multiple open sessions accumulating
- No cleanup on application shutdown or crashes
- Potential connection issues when restarting the application

## Root Cause Analysis

### Issues Identified

1. **No Graceful Shutdown Handler**
   - Application didn't register cleanup handlers for termination signals
   - Sessions remained open when app was killed or crashed
   - No `atexit` handler to close sessions on normal exit

2. **Missing Cleanup on Signal Termination**
   - SIGINT (Ctrl+C) and SIGTERM signals not handled
   - Abrupt termination left sessions open on server

3. **No Request Context Cleanup**
   - Flask teardown handlers not implemented
   - No error handling for request exceptions

4. **Limited Logging**
   - Session closure events not logged
   - Difficult to trace session lifecycle

## Solution Implemented

### 1. Added Import Statements

```python
import atexit      # For registering cleanup on normal exit
import signal      # For handling termination signals (SIGINT, SIGTERM)
import sys         # For sys.exit() in signal handlers
```

### 2. Enhanced Session Closure Logging

**File: `app.py`, Line ~221**

```python
def close_active_session(silent: bool = True) -> None:
    """Close the active session with the server."""
    if not state.session_id:
        return

    try:
        call_server("POST", f"/api/session/{state.session_id}/close", timeout=10)
        logger.info(f"✓ Closed session {state.session_id}")  # NEW: Log successful closure
    except Exception as exc:
        if not silent:
            raise exc
        app.logger.warning("Failed to close remote session: %s", exc)
    finally:
        state.session_id = None
        state.session_product = None
```

### 3. Added Cleanup Function

**File: `app.py`, Line ~238**

```python
def cleanup_on_shutdown() -> None:
    """Clean up resources when application shuts down."""
    logger.info("Application shutting down, cleaning up resources...")
    
    # Close active session
    if state.session_id:
        logger.info(f"Closing active session: {state.session_id}")
        close_active_session(silent=True)
    
    # Release camera resources
    try:
        if state.camera_initialized:
            logger.info("Releasing camera resources...")
            tis_camera.cleanup()
            state.camera_initialized = False
    except Exception as exc:
        logger.warning(f"Error during camera cleanup: {exc}")
    
    logger.info("✓ Cleanup completed")
```

**Features:**

- Closes any active session with the server
- Releases camera resources
- Logs all cleanup operations
- Handles errors gracefully (continues cleanup even if one step fails)

### 4. Added Signal Handler

**File: `app.py`, Line ~260**

```python
def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name}, shutting down gracefully...")
    cleanup_on_shutdown()
    sys.exit(0)
```

**Handles:**

- `SIGINT` (Ctrl+C) - User keyboard interrupt
- `SIGTERM` - System termination signal
- Other signals can be added as needed

### 5. Added Flask Teardown Handler

**File: `app.py`, Line ~773**

```python
@app.teardown_appcontext
def teardown_db(exception=None):
    """Clean up resources when request context ends."""
    if exception:
        logger.error(f"Request ended with exception: {exception}")
        # Note: We don't close sessions on every request, only on app shutdown
        # Sessions should be explicitly closed by the client or on disconnect
```

**Purpose:**

- Logs request exceptions
- Provides hook for per-request cleanup if needed
- Does NOT close sessions (sessions are long-lived, not per-request)

### 6. Enhanced Close Session API

**File: `app.py`, Line ~976**

```python
@app.route("/api/session", methods=["DELETE"])
def close_session():
    """Close the current inspection session."""
    if not state.session_id:
        logger.info("No active session to close")
        return jsonify({"status": "no-session"}), 200

    session_to_close = state.session_id
    try:
        close_active_session(silent=False)
        logger.info(f"✓ Session {session_to_close} closed successfully via API")
        return jsonify({"status": "closed", "session_id": session_to_close}), 200
    except Exception as exc:
        logger.error(f"Failed to close session {session_to_close}: {exc}")
        return jsonify({"error": str(exc)}), 502
```

**Improvements:**

- Better logging for API-initiated session closure
- Returns session ID in response
- Enhanced error messages

### 7. Registered Cleanup Handlers in Main

**File: `app.py`, Line ~1778**

```python
if __name__ == "__main__":
    # Register cleanup handlers
    atexit.register(cleanup_on_shutdown)
    signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination
    
    logger.info("Starting Visual AOI Client on port 5100...")
    logger.info("Cleanup handlers registered for graceful shutdown")
    
    try:
        app.run(debug=True, threaded=True, port=5100)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        cleanup_on_shutdown()
    except Exception as e:
        logger.error(f"Application error: {e}")
        cleanup_on_shutdown()
        raise
```

**Features:**

- Registers `atexit` handler for normal exit
- Registers signal handlers for SIGINT and SIGTERM
- Wraps `app.run()` in try-except for additional safety
- Ensures cleanup runs even on unexpected exceptions

## Session Lifecycle

### 1. Session Creation

```
Client → POST /api/session → Server
  ├─ Closes existing session if any
  ├─ Creates new session with server
  ├─ Stores session_id and product
  └─ Initializes camera with ROI group settings
```

### 2. Session Usage

```
Client → POST /api/inspect → Server (requires session_id)
  └─ Uses active session for inspection operations
```

### 3. Session Closure (Multiple Paths)

**Path A: Explicit API Call**

```
Client → DELETE /api/session → Server
  └─ close_active_session() → Server closes session
```

**Path B: New Session Creation**

```
Client → POST /api/session (new product)
  ├─ close_active_session() (old session)
  └─ Create new session
```

**Path C: Server Disconnect**

```
Client → POST /api/server/disconnect
  ├─ close_active_session()
  └─ Set connected=False
```

**Path D: Application Shutdown (NEW)**

```
System Signal (SIGINT/SIGTERM) OR Normal Exit
  └─ signal_handler() / atexit
      └─ cleanup_on_shutdown()
          ├─ close_active_session()
          └─ Release camera resources
```

## Testing Checklist

- [x] Normal shutdown with `Ctrl+C` closes session
- [x] `kill` command (SIGTERM) closes session
- [x] Normal exit closes session
- [x] DELETE /api/session API works
- [x] Creating new session closes old one
- [x] Server disconnect closes session
- [x] Camera resources released on shutdown
- [x] All cleanup operations logged
- [x] Errors during cleanup don't crash app

## Verification Commands

### 1. Check Active Sessions on Server

```bash
curl http://10.100.27.156:5000/api/sessions
```

### 2. Test Normal Shutdown

```bash
# Start app
python3 app.py

# In another terminal
curl -X POST http://127.0.0.1:5100/api/server/connect \
  -H "Content-Type: application/json" \
  -d '{"server_url": "http://10.100.27.156:5000"}'

curl -X POST http://127.0.0.1:5100/api/session \
  -H "Content-Type: application/json" \
  -d '{"product": "20003548"}'

# Press Ctrl+C in first terminal
# Check logs for: "✓ Closed session <id>"
```

### 3. Test Signal Termination

```bash
# Start app
python3 app.py

# Create session (as above)

# In another terminal
pkill -TERM -f "python3 app.py"

# Check logs for cleanup messages
```

### 4. Monitor Logs

```bash
# Look for these log messages:
# - "Starting Visual AOI Client on port 5100..."
# - "Cleanup handlers registered for graceful shutdown"
# - "Created session <id> for product <name>"
# - "✓ Closed session <id>"
# - "Application shutting down, cleaning up resources..."
# - "✓ Cleanup completed"
```

## Benefits

### 1. Resource Management

- ✅ Sessions properly closed on all exit paths
- ✅ Camera resources released
- ✅ No orphaned sessions on server

### 2. Reliability

- ✅ Graceful shutdown on signals
- ✅ Cleanup on exceptions
- ✅ Server state remains clean

### 3. Debugging

- ✅ All session operations logged
- ✅ Clear lifecycle visibility
- ✅ Error tracking improved

### 4. Maintenance

- ✅ Consistent cleanup logic
- ✅ Centralized resource management
- ✅ Easy to extend with new cleanup tasks

## Known Limitations

1. **Debug Mode Signal Handling**
   - Flask debug mode reloader may interfere with signal handlers
   - Workaround: Use `use_reloader=False` if needed
   - Current: Works correctly with `debug=True`

2. **Forceful Termination**
   - `kill -9` (SIGKILL) cannot be caught
   - Sessions may remain open in this case
   - Server should have timeout mechanism for stale sessions

3. **Network Failures**
   - Session closure may fail if server unreachable
   - Logged as warning, continues cleanup
   - Client state cleared regardless

## Future Enhancements

1. **Session Timeout Monitoring**
   - Add periodic heartbeat to server
   - Detect stale sessions
   - Auto-close after inactivity

2. **Reconnection Logic**
   - Attempt to restore previous session on reconnect
   - Session persistence across client restarts

3. **Health Check Integration**
   - Include session status in health endpoint
   - Alert on session leaks

4. **Metrics Collection**
   - Track session creation/closure rates
   - Monitor session durations
   - Identify resource leak patterns

## Related Documentation

- [Client-Server Architecture](CLIENT_SERVER_ARCHITECTURE.md)
- [Project Structure](PROJECT_STRUCTURE.md)
- [Camera Improvements](CAMERA_IMPROVEMENTS.md)

## Changelog

### v1.0 (October 6, 2025)

- ✅ Added `atexit` cleanup handler
- ✅ Added signal handlers (SIGINT, SIGTERM)
- ✅ Added `cleanup_on_shutdown()` function
- ✅ Added Flask teardown handler
- ✅ Enhanced session closure logging
- ✅ Wrapped main execution in try-except
- ✅ Camera cleanup on shutdown
- ✅ Comprehensive error handling
