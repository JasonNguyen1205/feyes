"""
Visual AOI - Automated Optical Inspection System

A comprehensive Python-based AOI system for industrial quality control applications.
"""

__version__ = "1.0.0"
__author__ = "Jason Nguyen"
__email__ = "jason.nguyen@example.com"

# Import core modules that don't require heavy dependencies
from . import config
from . import utils

# Import TIS module for camera interface
def get_tis_module():
    """Import TIS module on demand."""
    try:
        from . import TIS
        return TIS
    except ImportError as e:
        print(f"TIS module not available: {e}")
        return None

# Optional modules that require dependencies - import on demand only
def get_camera_module():
    """Import camera module on demand."""
    try:
        from . import camera
        return camera
    except ImportError as e:
        print(f"Camera module not available: {e}")
        return None

def get_ai_module():
    """Import AI module on demand."""
    try:
        from . import ai
        return ai
    except ImportError as e:
        print(f"AI module not available: {e}")
        return None

def get_barcode_module():
    """Import barcode module on demand."""
    try:
        from . import barcode
        return barcode
    except ImportError as e:
        print(f"Barcode module not available: {e}")
        return None

def get_ocr_module():
    """Import OCR module on demand."""
    try:
        from . import ocr
        return ocr
    except ImportError as e:
        print(f"OCR module not available: {e}")
        return None

def get_roi_module():
    """Import ROI module on demand."""
    try:
        from . import roi
        return roi
    except ImportError as e:
        print(f"ROI module not available: {e}")
        return None

def get_ui_module():
    """Import UI module on demand."""
    try:
        from . import ui
        return ui
    except ImportError as e:
        print(f"UI module not available: {e}")
        return None

def get_inspection_module():
    """Import inspection module on demand."""
    try:
        from . import inspection
        return inspection
    except ImportError as e:
        print(f"Inspection module not available: {e}")
        return None

__all__ = [
    "config",
    "utils",
    "get_tis_module",
    "get_camera_module",
    "get_ai_module", 
    "get_barcode_module",
    "get_ocr_module",
    "get_roi_module",
    "get_ui_module",
    "get_inspection_module"
]
