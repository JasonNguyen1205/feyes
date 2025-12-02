"""
Configuration management for Visual AOI system.
"""

import os
import sys
import json

# ========== CONSTANTS ==========
GOLDEN_ROI_DIR = "golden_rois"
AI_THRESHOLD = 0.9  # Default, but per-ROI threshold is used for compare ROIs

# Display settings
FONT_SCALE = 0.5
THICKNESS = 2
PADDING = 10

# Camera configuration file
CAMERA_CONFIG_FILE = "config/system/camera.json"

# Camera configuration - loaded from config file
_camera_config = None

def load_camera_config():
    """Load camera configuration from JSON file."""
    global _camera_config
    if _camera_config is None:
        try:
            if os.path.exists(CAMERA_CONFIG_FILE):
                with open(CAMERA_CONFIG_FILE, 'r') as f:
                    _camera_config = json.load(f)
            else:
                # Fallback to default values if config file doesn't exist
                _camera_config = {
                    "camera_hardware": {
                        "serial": "30320436",
                        "width": 7716,
                        "height": 5360,
                        "fps": "7/1",
                        "format": "BGRA"
                    },
                    "camera_defaults": {
                        "focus": 305,
                        "exposure": 3000
                    },
                    "camera_validation": {
                        "retry_attempts": 3,
                        "retry_delay": 1.0,
                        "image_min_brightness": 10,
                        "image_max_brightness": 245,
                        "image_min_contrast": 5
                    },
                    "camera_performance": {
                        "focus_settle_delay": 3.0,
                        "enable_fast_capture": True,
                        "max_threads": 16
                    }
                }
        except Exception as e:
            print(f"Error loading camera config: {e}")
            # Use default fallback configuration
            _camera_config = {
                "camera_hardware": {"serial": "30320436", "width": 7716, "height": 5360, "fps": "7/1", "format": "BGRA"},
                "camera_defaults": {"focus": 305, "exposure": 3000},
                "camera_validation": {"retry_attempts": 3, "retry_delay": 1.0, "image_min_brightness": 10, "image_max_brightness": 245, "image_min_contrast": 5},
                "camera_performance": {"focus_settle_delay": 3.0, "enable_fast_capture": True, "max_threads": 16}
            }
    return _camera_config

def get_camera_config(section=None, key=None):
    """Get camera configuration value(s)."""
    config = load_camera_config()
    if section is None:
        return config
    if section not in config:
        return None
    if key is None:
        return config[section]
    return config[section].get(key)

# Camera settings - now loaded from config
def get_default_focus():
    return get_camera_config("camera_defaults", "focus")

def get_default_exposure():
    return get_camera_config("camera_defaults", "exposure")

# Camera hardware configuration - now loaded from config
def get_camera_serial():
    return get_camera_config("camera_hardware", "serial")

def get_camera_width():
    return get_camera_config("camera_hardware", "width")

def get_camera_height():
    return get_camera_config("camera_hardware", "height")

def get_camera_fps():
    return get_camera_config("camera_hardware", "fps")

def get_camera_format():
    return get_camera_config("camera_hardware", "format")

# Camera validation settings - now loaded from config
def get_camera_retry_attempts():
    return get_camera_config("camera_validation", "retry_attempts")

def get_camera_retry_delay():
    return get_camera_config("camera_validation", "retry_delay")

def get_image_min_brightness():
    return get_camera_config("camera_validation", "image_min_brightness")

def get_image_max_brightness():
    return get_camera_config("camera_validation", "image_max_brightness")

def get_image_min_contrast():
    return get_camera_config("camera_validation", "image_min_contrast")

# Performance settings - now loaded from config
def get_focus_settle_delay():
    return get_camera_config("camera_performance", "focus_settle_delay")

def get_enable_fast_capture():
    return get_camera_config("camera_performance", "enable_fast_capture")

def get_max_threads():
    return get_camera_config("camera_performance", "max_threads")

def save_camera_config(config):
    """Save camera configuration to JSON file."""
    try:
        # Ensure config directory exists
        os.makedirs(os.path.dirname(CAMERA_CONFIG_FILE), exist_ok=True)
        
        with open(CAMERA_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Reset cached config to force reload
        global _camera_config
        _camera_config = None
        
        print(f"Camera configuration saved to: {CAMERA_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"Error saving camera configuration: {e}")
        return False

def update_camera_config(section, key, value):
    """Update a specific camera configuration value."""
    config = load_camera_config().copy()
    if section not in config:
        config[section] = {}
    config[section][key] = value
    return save_camera_config(config)

# Backward compatibility constants (deprecated - use functions above)
DEFAULT_FOCUS = 305  # Deprecated: use get_default_focus()
DEFAULT_EXPOSURE = 3000  # Deprecated: use get_default_exposure()
CAMERA_SERIAL = "30320436"  # Deprecated: use get_camera_serial()
CAMERA_WIDTH = 7716  # Deprecated: use get_camera_width()
CAMERA_HEIGHT = 5360  # Deprecated: use get_camera_height()
CAMERA_FPS = "7/1"  # Deprecated: use get_camera_fps()
CAMERA_FORMAT = "BGRA"  # Deprecated: use get_camera_format()
CAMERA_RETRY_ATTEMPTS = 3  # Deprecated: use get_camera_retry_attempts()
CAMERA_RETRY_DELAY = 1.0  # Deprecated: use get_camera_retry_delay()
IMAGE_MIN_BRIGHTNESS = 10  # Deprecated: use get_image_min_brightness()
IMAGE_MAX_BRIGHTNESS = 245  # Deprecated: use get_image_max_brightness()
IMAGE_MIN_CONTRAST = 5  # Deprecated: use get_image_min_contrast()
FOCUS_SETTLE_DELAY = 3.0  # Deprecated: use get_focus_settle_delay()
ENABLE_FAST_CAPTURE = True  # Deprecated: use get_enable_fast_capture()
MAX_THREADS = 16  # Deprecated: use get_max_threads()

# Sample ROI configurations (for reference)
SAMPLE_ROIS = [
    (1, 2, (0, 0, 100, 100), 305, 3000, 0.9, "mobilenet"),
    (5, 1, (10, 10, 50, 50), 305, 3000, None, "opencv"),
]

# Global variables
PRODUCT_NAME = None
# Use functions instead of hardcoded values
default_focus = get_default_focus()
default_exposure = get_default_exposure()

# Theme configuration file
THEME_CONFIG_FILE = "config/theme_settings.json"
DEFAULT_THEME = "light"  # Default to light mode (iOS theme)

def load_theme_preference():
    """Load theme preference from config file."""
    try:
        if os.path.exists(THEME_CONFIG_FILE):
            with open(THEME_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('theme', DEFAULT_THEME)
        return DEFAULT_THEME
    except Exception as e:
        print(f"Error loading theme preference: {e}")
        return DEFAULT_THEME

def save_theme_preference(theme):
    """Save theme preference to config file."""
    try:
        # Ensure config directory exists
        os.makedirs(os.path.dirname(THEME_CONFIG_FILE), exist_ok=True)
        
        config = {'theme': theme}
        with open(THEME_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Theme preference saved: {theme}")
        return True
    except Exception as e:
        print(f"Error saving theme preference: {e}")
        return False

def set_product_name(product_name):
    """Set the product name globally."""
    global PRODUCT_NAME
    PRODUCT_NAME = product_name
    print(f"Product name set to: {PRODUCT_NAME}")

def get_product_name():
    """Get the current product name."""
    global PRODUCT_NAME
    return PRODUCT_NAME

def get_config_filename(product_name):
    """Get the configuration filename for a given product."""
    return os.path.join("config", "products", product_name, f"rois_config_{product_name}.json")

def get_golden_roi_dir(product_name, idx):
    """Get the golden ROI directory for a given product and ROI index."""
    if not isinstance(idx, (int, float)) or idx < 0:
        raise ValueError(f"Invalid ROI index: {idx}")
    return os.path.join("config", "products", product_name, GOLDEN_ROI_DIR, f"roi_{int(idx)}")

def setup_environment():
    """Setup environment variables and global exception handler."""
    os.environ['NO_PROXY'] = '10.100.27.167'
    
    def global_exception_handler(exctype, value, tb):
        print("Unhandled exception:", value)
        import traceback
        traceback.print_exception(exctype, value, tb)
    
    sys.excepthook = global_exception_handler
    
    # Suppress warnings
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
