#!/usr/bin/env python3
"""
Example: Integration of SharedFolderManager into Visual AOI Client

This example demonstrates how to refactor the existing client_app_simple.py
to use the SharedFolderManager for all shared folder operations.
"""

import tkinter as tk
from tkinter import messagebox
import logging
from PIL import Image, ImageTk
import cv2
import os

# Import the shared folder manager
from shared_folder_manager import SharedFolderManager

logger = logging.getLogger(__name__)


class VisualAOIClientRefactored:
    """
    Refactored Visual AOI Client using SharedFolderManager.
    
    This example shows the key changes needed to integrate SharedFolderManager
    into the existing client application.
    """
    
    def __init__(self):
        """Initialize the client with SharedFolderManager."""
        # Existing initialization
        self.root = tk.Tk()
        self.session_id = None
        
        # NEW: Initialize SharedFolderManager
        self.shared_folder = SharedFolderManager()
        
        # Check if shared folder is accessible
        if not self.shared_folder.check_server_connection():
            logger.error("Shared folder not accessible!")
            messagebox.showerror(
                "Error", 
                "Cannot access server shared folder.\n"
                "Please check:\n"
                "  1. Server is running\n"
                "  2. Network connection\n"
                "  3. Folder permissions"
            )
        else:
            logger.info("Shared folder accessible")
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    def create_session(self, product_name):
        """
        Create a new inspection session.
        
        BEFORE: Manual directory creation with os.makedirs
        AFTER:  Use SharedFolderManager
        """
        try:
            # Generate session ID
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_id = f"session_{product_name}_{timestamp}"
            
            # NEW: Use SharedFolderManager to create directories
            input_dir, output_dir = self.shared_folder.create_session_directories(
                self.session_id
            )
            
            logger.info(f"Created session {self.session_id}")
            logger.info(f"  Input:  {input_dir}")
            logger.info(f"  Output: {output_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            messagebox.showerror("Error", f"Failed to create session: {e}")
            return False
    
    # =========================================================================
    # Image Capture and Storage
    # =========================================================================
    
    def save_captured_image_refactored(self, image, focus, exposure, rois):
        """
        Save captured image to shared folder.
        
        BEFORE: Manual path construction and file writing
        AFTER:  Use SharedFolderManager.save_captured_image()
        """
        try:
            # Encode image
            _, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            image_bytes = encoded.tobytes()
            
            # Create filename
            filename = f"capture_F{focus}_E{exposure}.jpg"
            
            # NEW: Use SharedFolderManager
            image_path = self.shared_folder.save_captured_image(
                session_id=self.session_id,
                image_data=image_bytes,
                filename=filename,
                metadata={
                    'focus': focus,
                    'exposure': exposure,
                    'rois': rois,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Saved image: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return None
    
    # BEFORE (old code from client_app_simple.py):
    def save_captured_image_old(self, image, group_key, focus, exposure, rois):
        """OLD METHOD - shows what we're replacing."""
        try:
            # OLD: Manual directory creation and path construction
            session_dir = f"/mnt/visual-aoi-shared/sessions/{self.session_id}"
            input_dir = os.path.join(session_dir, "input")
            output_dir = os.path.join(session_dir, "output")
            os.makedirs(input_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
            
            # OLD: Manual path construction
            image_filename = f"capture_F{focus}_E{exposure}.jpg"
            image_filepath = os.path.join(input_dir, image_filename)
            
            # OLD: Manual file writing
            cv2.imwrite(image_filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            return {
                'image_filename': image_filename,
                'focus': focus,
                'exposure': exposure,
                'rois': rois
            }
        except Exception as e:
            logger.error(f"Failed to save captured image: {e}")
            return None
    
    # =========================================================================
    # ROI Image Display
    # =========================================================================
    
    def display_roi_image_refactored(self, roi_result):
        """
        Display ROI image from shared folder.
        
        BEFORE: Manual path construction and error handling
        AFTER:  Use SharedFolderManager.get_roi_image_path()
        """
        if not roi_result.get('roi_image_file'):
            return
        
        try:
            # NEW: Use SharedFolderManager
            roi_image_path = self.shared_folder.get_roi_image_path(
                self.session_id,
                roi_result['roi_image_file']
            )
            
            if roi_image_path:
                # Load and display image
                roi_img = Image.open(roi_image_path)
                roi_img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                
                # Display in UI (simplified)
                roi_photo = ImageTk.PhotoImage(roi_img)
                # ... display code ...
                
                logger.info(f"Displayed ROI image: {roi_result['roi_image_file']}")
            else:
                logger.warning(f"ROI image not found: {roi_result['roi_image_file']}")
                # Show placeholder
                
        except Exception as e:
            logger.error(f"Failed to display ROI image: {e}")
    
    # BEFORE (old code):
    def display_roi_image_old(self, roi_result):
        """OLD METHOD - shows what we're replacing."""
        if not roi_result.get('roi_image_file'):
            return
            
        try:
            # OLD: Manual path construction
            session_dir = f"/mnt/visual-aoi-shared/sessions/{self.session_id}"
            output_dir = os.path.join(session_dir, "output")
            roi_image_path = os.path.join(output_dir, roi_result['roi_image_file'])
            
            # OLD: Manual existence check
            if os.path.exists(roi_image_path):
                roi_img = Image.open(roi_image_path)
                # ... display code ...
            else:
                # Handle missing file
                pass
        except Exception as e:
            logger.warning(f"Failed to display ROI image: {e}")
    
    # =========================================================================
    # Golden Sample Management
    # =========================================================================
    
    def browse_golden_samples(self, product_name, roi_id=None):
        """
        Browse golden samples for a product.
        
        NEW FUNCTIONALITY: Easy golden sample browsing
        """
        try:
            # Get golden samples using SharedFolderManager
            if roi_id:
                samples = self.shared_folder.list_golden_samples(
                    product_name, roi_id=roi_id
                )
                title = f"Golden Samples - {product_name} - ROI {roi_id}"
            else:
                samples = self.shared_folder.list_golden_samples(product_name)
                title = f"Golden Samples - {product_name}"
            
            if not samples:
                messagebox.showinfo(
                    "No Samples",
                    f"No golden samples found for {product_name}"
                )
                return
            
            # Create browser window
            browser_window = tk.Toplevel(self.root)
            browser_window.title(title)
            browser_window.geometry("800x600")
            
            # Display samples
            for sample in samples:
                # Get full path
                golden_dir = self.shared_folder.get_golden_samples_directory(product_name)
                sample_path = golden_dir / sample
                
                if sample_path.exists():
                    # Load and display thumbnail
                    img = Image.open(sample_path)
                    img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                    # ... display in grid ...
            
            logger.info(f"Displayed {len(samples)} golden samples")
            
        except Exception as e:
            logger.error(f"Failed to browse golden samples: {e}")
            messagebox.showerror("Error", f"Failed to browse golden samples: {e}")
    
    # =========================================================================
    # Session Cleanup
    # =========================================================================
    
    def close_session_refactored(self, keep_output=True):
        """
        Close and cleanup session.
        
        BEFORE: Manual cleanup or no cleanup
        AFTER:  Use SharedFolderManager.cleanup_session()
        """
        if not self.session_id:
            return
        
        try:
            # NEW: Use SharedFolderManager for cleanup
            success = self.shared_folder.cleanup_session(
                self.session_id,
                keep_output=keep_output  # Keep output for history
            )
            
            if success:
                if keep_output:
                    logger.info(f"Cleaned up session input: {self.session_id}")
                else:
                    logger.info(f"Cleaned up entire session: {self.session_id}")
            
            self.session_id = None
            
        except Exception as e:
            logger.error(f"Failed to cleanup session: {e}")
    
    # =========================================================================
    # Disk Usage Monitoring
    # =========================================================================
    
    def show_disk_usage(self):
        """
        Show disk usage statistics.
        
        NEW FUNCTIONALITY: Monitor shared folder disk usage
        """
        try:
            usage = self.shared_folder.get_disk_usage()
            
            # Format sizes
            def format_size(bytes_size):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if bytes_size < 1024:
                        return f"{bytes_size:.2f} {unit}"
                    bytes_size /= 1024
                return f"{bytes_size:.2f} TB"
            
            message = (
                f"Shared Folder Disk Usage:\n\n"
                f"Total:          {format_size(usage['total'])}\n"
                f"Sessions:       {format_size(usage['sessions'])}\n"
                f"Golden Samples: {format_size(usage['golden_samples'])}\n"
                f"Temp Files:     {format_size(usage['temp'])}"
            )
            
            messagebox.showinfo("Disk Usage", message)
            
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            messagebox.showerror("Error", f"Failed to get disk usage: {e}")
    
    # =========================================================================
    # Maintenance Operations
    # =========================================================================
    
    def perform_maintenance(self):
        """
        Perform maintenance operations on shared folder.
        
        NEW FUNCTIONALITY: Automated maintenance
        """
        try:
            # Cleanup old temp directories (older than 24 hours)
            cleaned_count = self.shared_folder.cleanup_temp_directories(
                max_age_hours=24
            )
            
            logger.info(f"Maintenance: Cleaned up {cleaned_count} temp directories")
            
            # Get disk usage
            usage = self.shared_folder.get_disk_usage()
            logger.info(f"Maintenance: Current disk usage: {usage['total'] / 1024 / 1024:.2f} MB")
            
            # Show results
            messagebox.showinfo(
                "Maintenance Complete",
                f"Cleaned up {cleaned_count} old temporary directories\n\n"
                f"Current disk usage: {usage['total'] / 1024 / 1024:.2f} MB"
            )
            
        except Exception as e:
            logger.error(f"Maintenance failed: {e}")
            messagebox.showerror("Error", f"Maintenance failed: {e}")


# =============================================================================
# Migration Example: Side-by-Side Comparison
# =============================================================================

def migration_example():
    """
    Side-by-side comparison of old vs new code.
    """
    
    # -------------------------------------------------------------------------
    # Example 1: Creating Session Directories
    # -------------------------------------------------------------------------
    
    # OLD WAY (scattered throughout code):
    def old_way_create_dirs(session_id):
        session_dir = f"/mnt/visual-aoi-shared/sessions/{session_id}"
        input_dir = os.path.join(session_dir, "input")
        output_dir = os.path.join(session_dir, "output")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        return input_dir, output_dir
    
    # NEW WAY (centralized):
    def new_way_create_dirs(session_id):
        sfm = SharedFolderManager()
        input_dir, output_dir = sfm.create_session_directories(session_id)
        return input_dir, output_dir
    
    # -------------------------------------------------------------------------
    # Example 2: Accessing ROI Images
    # -------------------------------------------------------------------------
    
    # OLD WAY:
    def old_way_get_roi_image(session_id, filename):
        session_dir = f"/mnt/visual-aoi-shared/sessions/{session_id}"
        output_dir = os.path.join(session_dir, "output")
        roi_image_path = os.path.join(output_dir, filename)
        
        if os.path.exists(roi_image_path):
            return roi_image_path
        return None
    
    # NEW WAY:
    def new_way_get_roi_image(session_id, filename):
        sfm = SharedFolderManager()
        return sfm.get_roi_image_path(session_id, filename)
    
    # -------------------------------------------------------------------------
    # Example 3: Listing Images
    # -------------------------------------------------------------------------
    
    # OLD WAY:
    def old_way_list_images(session_id):
        session_dir = f"/mnt/visual-aoi-shared/sessions/{session_id}"
        input_dir = os.path.join(session_dir, "input")
        
        if not os.path.exists(input_dir):
            return []
        
        images = []
        for f in os.listdir(input_dir):
            if f.endswith(('.jpg', '.jpeg', '.png')):
                images.append(f)
        return sorted(images)
    
    # NEW WAY:
    def new_way_list_images(session_id):
        sfm = SharedFolderManager()
        return sfm.list_session_images(session_id, directory="input")
    
    print("Migration examples defined - see functions above")


# =============================================================================
# Quick Start Guide
# =============================================================================

def quick_start_guide():
    """
    Quick start guide for using SharedFolderManager.
    """
    print("=" * 70)
    print("QUICK START GUIDE: SharedFolderManager")
    print("=" * 70)
    print()
    
    # Step 1: Import
    print("Step 1: Import SharedFolderManager")
    print("-" * 70)
    print("from client.shared_folder_manager import SharedFolderManager")
    print()
    
    # Step 2: Initialize
    print("Step 2: Initialize in your class __init__")
    print("-" * 70)
    print("class VisualAOIClient:")
    print("    def __init__(self):")
    print("        self.shared_folder = SharedFolderManager()")
    print()
    
    # Step 3: Use
    print("Step 3: Use SharedFolderManager methods")
    print("-" * 70)
    print("# Create session directories")
    print("input_dir, output_dir = self.shared_folder.create_session_directories(session_id)")
    print()
    print("# Get ROI image path")
    print("roi_path = self.shared_folder.get_roi_image_path(session_id, 'roi_1.jpg')")
    print()
    print("# List images")
    print("images = self.shared_folder.list_session_images(session_id, 'input')")
    print()
    
    # Step 4: Replace hardcoded paths
    print("Step 4: Replace all hardcoded paths")
    print("-" * 70)
    print("BEFORE: session_dir = f'/home/.../shared/sessions/{session_id}'")
    print("AFTER:  session_dir = self.shared_folder.get_session_directory(session_id)")
    print()
    
    print("=" * 70)
    print("Ready to refactor! See SHARED_FOLDER_ACCESS.md for full documentation")
    print("=" * 70)


if __name__ == '__main__':
    # Run quick start guide
    quick_start_guide()
    
    # Show migration examples
    print("\n")
    migration_example()
