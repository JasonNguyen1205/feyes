"""
Utility functions for Visual AOI system.
"""

import os
import time
import psutil
import tkinter as tk
import tkinter.simpledialog
import gc
from PIL import Image
import cv2
import numpy as np

def print_memory_usage():
    """Print current memory usage for debugging."""
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    print(f"DEBUG: Memory usage: {mem_mb:.2f} MB")

def get_product_name():
    """Get product name from user input."""
    root = tk.Tk()
    root.withdraw()
    pname = tkinter.simpledialog.askstring("Product Selection", "Enter or select product name:")
    root.destroy()
    return pname.strip() if pname else None

def get_thumbnail_pil(img, width, height):
    """Convert image to PIL thumbnail with specified dimensions."""
    # If img is None, return a blank image
    if img is None:
        return Image.new("RGB", (width, height), (128,128,128))
    
    # If img is a numpy array, convert to PIL
    if isinstance(img, np.ndarray):
        if img.shape[-1] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img)
    else:
        pil_img = img
    
    # Use Image.Resampling.LANCZOS for newer PIL versions
    try:
        pil_img = pil_img.resize((width, height), Image.Resampling.LANCZOS)
    except AttributeError:
        # For older PIL versions, use default resampling
        pil_img = pil_img.resize((width, height))
    
    return pil_img

def safe_parse_coords(coord_str):
    """Safely parse coordinate strings to avoid eval issues."""
    try:
        import ast
        coords = ast.literal_eval(coord_str)
        if isinstance(coords, list):
            return coords
    except Exception:
        pass
    return []

def cleanup_memory():
    """Force garbage collection and memory cleanup."""
    gc.collect()
    
def ensure_directory_exists(directory_path):
    """Ensure a directory exists, create if not."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)

def format_elapsed_time(start_time):
    """Format elapsed time from start time."""
    elapsed = int(time.time() - start_time)
    if elapsed < 60:
        return f"{elapsed}s"
    elif elapsed < 3600:
        minutes = elapsed // 60
        seconds = elapsed % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        return f"{hours}h {minutes}m {seconds}s"

def validate_roi_coordinates(x1, y1, x2, y2, img_width, img_height):
    """Validate and clamp ROI coordinates to image bounds."""
    # Ensure coordinates are within image bounds
    x1 = max(0, min(x1, img_width - 1))
    x2 = max(0, min(x2, img_width - 1))
    y1 = max(0, min(y1, img_height - 1))
    y2 = max(0, min(y2, img_height - 1))
    
    # Ensure x1 < x2 and y1 < y2
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    
    # Ensure minimum size
    if x2 - x1 < 10:
        x2 = min(x1 + 10, img_width - 1)
    if y2 - y1 < 10:
        y2 = min(y1 + 10, img_height - 1)
    
    return x1, y1, x2, y2

def is_valid_roi_size(width, height, min_size=10):
    """Check if ROI size is valid for processing."""
    return width >= min_size and height >= min_size

class PerformanceTimer:
    """Simple performance timer for measuring operation durations."""
    
    def __init__(self, name="Operation"):
        self.name = name
        self.start_time = None
        
    def start(self):
        """Start the timer."""
        self.start_time = time.time()
        print(f"Starting {self.name}...")
        
    def stop(self):
        """Stop the timer and print elapsed time."""
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            print(f"{self.name} completed in {elapsed:.2f} seconds")
            return elapsed
        return 0
        
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
