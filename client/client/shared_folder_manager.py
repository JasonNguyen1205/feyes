#!/usr/bin/env python3
"""
Shared Folder Manager for Visual AOI Client
Handles all operations related to accessing shared folders from the server.

This module provides a centralized interface for:
- Session directory management
- Image file operations (read/write)
- Result file access
- Golden sample management
- Temporary file handling
"""

import os
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SharedFolderManager:
    """
    Manages access to server shared folders for the Visual AOI client.
    
    Directory Structure:
        shared/
        ├── sessions/
        │   └── {session_id}/
        │       ├── input/          # Captured images from client
        │       │   ├── capture_F{focus}_E{exposure}.jpg
        │       │   └── metadata.json
        │       └── output/         # Processing results from server
        │           ├── roi_{roi_id}_captured.jpg
        │           ├── roi_{roi_id}_golden.jpg
        │           └── results.json
        ├── golden_samples/
        │   └── {product_name}/
        │       ├── roi_{roi_id}_sample_1.jpg
        │       ├── roi_{roi_id}_sample_2.jpg
        │       └── ...
        └── temp/                   # Temporary files
    """
    
    def __init__(self, base_path: str = "/mnt/visual-aoi-shared"):
        """
        Initialize the Shared Folder Manager.
        
        Args:
            base_path: Root path to the shared folder on the server
        """
        self.base_path = Path(base_path)
        self.sessions_path = self.base_path / "sessions"
        self.golden_samples_path = self.base_path / "golden_samples"
        self.temp_path = self.base_path / "temp"
        
        logger.info(f"SharedFolderManager initialized with base path: {self.base_path}")
        
    def check_server_connection(self) -> bool:
        """
        Check if the shared folder is accessible.
        
        Returns:
            True if shared folder is accessible, False otherwise
        """
        try:
            return self.base_path.exists() and os.access(str(self.base_path), os.R_OK | os.W_OK)
        except Exception as e:
            logger.error(f"Failed to check shared folder accessibility: {e}")
            return False
    
    def get_session_directory(self, session_id: str) -> Path:
        """
        Get the session directory path.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Path object to the session directory
        """
        return self.sessions_path / session_id
    
    def get_session_input_directory(self, session_id: str) -> Path:
        """
        Get the session input directory path (for captured images).
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Path object to the session input directory
        """
        return self.get_session_directory(session_id) / "input"
    
    def get_session_output_directory(self, session_id: str) -> Path:
        """
        Get the session output directory path (for results and processed images).
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Path object to the session output directory
        """
        return self.get_session_directory(session_id) / "output"
    
    def create_session_directories(self, session_id: str) -> Tuple[Path, Path]:
        """
        Create input and output directories for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Tuple of (input_dir_path, output_dir_path)
            
        Raises:
            OSError: If directory creation fails
        """
        try:
            input_dir = self.get_session_input_directory(session_id)
            output_dir = self.get_session_output_directory(session_id)
            
            input_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Created session directories for session {session_id}")
            logger.debug(f"  Input:  {input_dir}")
            logger.debug(f"  Output: {output_dir}")
            
            return input_dir, output_dir
            
        except Exception as e:
            logger.error(f"Failed to create session directories: {e}")
            raise OSError(f"Failed to create session directories: {e}")
    
    def save_captured_image(
        self, 
        session_id: str, 
        image_data: bytes, 
        filename: str,
        metadata: Optional[Dict] = None
    ) -> Path:
        """
        Save a captured image to the session input directory.
        
        Args:
            session_id: Unique session identifier
            image_data: Raw image bytes
            filename: Name for the image file
            metadata: Optional metadata to save alongside the image
            
        Returns:
            Path to the saved image file
            
        Raises:
            OSError: If file save fails
        """
        try:
            input_dir = self.get_session_input_directory(session_id)
            input_dir.mkdir(parents=True, exist_ok=True)
            
            # Save image file
            image_path = input_dir / filename
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Saved captured image: {filename} ({len(image_data)} bytes)")
            
            # Save metadata if provided
            if metadata:
                metadata_path = input_dir / f"{filename}.metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                logger.debug(f"Saved metadata for {filename}")
            
            return image_path
            
        except Exception as e:
            logger.error(f"Failed to save captured image: {e}")
            raise OSError(f"Failed to save captured image: {e}")
    
    def read_roi_image(self, session_id: str, roi_image_filename: str) -> Optional[bytes]:
        """
        Read an ROI image from the session output directory.
        
        Args:
            session_id: Unique session identifier
            roi_image_filename: Name of the ROI image file
            
        Returns:
            Image bytes if found, None otherwise
        """
        try:
            output_dir = self.get_session_output_directory(session_id)
            image_path = output_dir / roi_image_filename
            
            if not image_path.exists():
                logger.warning(f"ROI image not found: {image_path}")
                return None
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            logger.debug(f"Read ROI image: {roi_image_filename} ({len(image_data)} bytes)")
            return image_data
            
        except Exception as e:
            logger.error(f"Failed to read ROI image: {e}")
            return None
    
    def get_roi_image_path(self, session_id: str, roi_image_filename: str) -> Optional[Path]:
        """
        Get the full path to an ROI image file.
        
        Args:
            session_id: Unique session identifier
            roi_image_filename: Name of the ROI image file
            
        Returns:
            Path object if file exists, None otherwise
        """
        try:
            output_dir = self.get_session_output_directory(session_id)
            image_path = output_dir / roi_image_filename
            
            if image_path.exists():
                return image_path
            else:
                logger.warning(f"ROI image path not found: {image_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get ROI image path: {e}")
            return None
    
    def read_golden_image(self, session_id: str, golden_image_filename: str) -> Optional[bytes]:
        """
        Read a golden image from the session output directory.
        
        Args:
            session_id: Unique session identifier
            golden_image_filename: Name of the golden image file
            
        Returns:
            Image bytes if found, None otherwise
        """
        try:
            output_dir = self.get_session_output_directory(session_id)
            image_path = output_dir / golden_image_filename
            
            if not image_path.exists():
                logger.warning(f"Golden image not found: {image_path}")
                return None
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            logger.debug(f"Read golden image: {golden_image_filename} ({len(image_data)} bytes)")
            return image_data
            
        except Exception as e:
            logger.error(f"Failed to read golden image: {e}")
            return None
    
    def get_golden_image_path(self, session_id: str, golden_image_filename: str) -> Optional[Path]:
        """
        Get the full path to a golden image file.
        
        Args:
            session_id: Unique session identifier
            golden_image_filename: Name of the golden image file
            
        Returns:
            Path object if file exists, None otherwise
        """
        try:
            output_dir = self.get_session_output_directory(session_id)
            image_path = output_dir / golden_image_filename
            
            if image_path.exists():
                return image_path
            else:
                logger.warning(f"Golden image path not found: {image_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get golden image path: {e}")
            return None
    
    def read_results_json(self, session_id: str, filename: str = "results.json") -> Optional[Dict]:
        """
        Read results JSON from the session output directory.
        
        Args:
            session_id: Unique session identifier
            filename: Name of the results file
            
        Returns:
            Parsed JSON dict if found, None otherwise
        """
        try:
            output_dir = self.get_session_output_directory(session_id)
            results_path = output_dir / filename
            
            if not results_path.exists():
                logger.warning(f"Results file not found: {results_path}")
                return None
            
            with open(results_path, 'r') as f:
                results = json.load(f)
            
            logger.debug(f"Read results JSON: {filename}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to read results JSON: {e}")
            return None
    
    def list_session_images(self, session_id: str, directory: str = "input") -> List[str]:
        """
        List all image files in a session directory.
        
        Args:
            session_id: Unique session identifier
            directory: "input" or "output"
            
        Returns:
            List of image filenames
        """
        try:
            if directory == "input":
                dir_path = self.get_session_input_directory(session_id)
            elif directory == "output":
                dir_path = self.get_session_output_directory(session_id)
            else:
                logger.error(f"Invalid directory type: {directory}")
                return []
            
            if not dir_path.exists():
                logger.warning(f"Directory not found: {dir_path}")
                return []
            
            # Get all image files
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            images = [
                f.name for f in dir_path.iterdir() 
                if f.is_file() and f.suffix.lower() in image_extensions
            ]
            
            logger.debug(f"Found {len(images)} images in {directory} directory")
            return sorted(images)
            
        except Exception as e:
            logger.error(f"Failed to list session images: {e}")
            return []
    
    def cleanup_session(self, session_id: str, keep_output: bool = True) -> bool:
        """
        Clean up session directories.
        
        Args:
            session_id: Unique session identifier
            keep_output: If True, only delete input directory; if False, delete all
            
        Returns:
            True if cleanup succeeded, False otherwise
        """
        try:
            session_dir = self.get_session_directory(session_id)
            
            if not session_dir.exists():
                logger.warning(f"Session directory not found: {session_dir}")
                return False
            
            if keep_output:
                # Only delete input directory
                input_dir = self.get_session_input_directory(session_id)
                if input_dir.exists():
                    shutil.rmtree(input_dir)
                    logger.info(f"Cleaned up session input directory: {session_id}")
            else:
                # Delete entire session directory
                shutil.rmtree(session_dir)
                logger.info(f"Cleaned up entire session directory: {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup session: {e}")
            return False
    
    def get_golden_samples_directory(self, product_name: str) -> Path:
        """
        Get the golden samples directory for a product.
        
        Args:
            product_name: Product identifier
            
        Returns:
            Path to the golden samples directory
        """
        return self.golden_samples_path / product_name
    
    def list_golden_samples(self, product_name: str, roi_id: Optional[int] = None) -> List[str]:
        """
        List golden sample files for a product.
        
        Args:
            product_name: Product identifier
            roi_id: Optional ROI ID to filter samples
            
        Returns:
            List of golden sample filenames
        """
        try:
            golden_dir = self.get_golden_samples_directory(product_name)
            
            if not golden_dir.exists():
                logger.debug(f"Golden samples directory not found: {golden_dir}")
                return []
            
            # Get all image files
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
            samples = []
            
            for f in golden_dir.iterdir():
                if f.is_file() and f.suffix.lower() in image_extensions:
                    # Filter by ROI ID if specified
                    if roi_id is not None:
                        if f"roi_{roi_id}_" in f.name:
                            samples.append(f.name)
                    else:
                        samples.append(f.name)
            
            logger.debug(f"Found {len(samples)} golden samples for {product_name}" + 
                        (f" (ROI {roi_id})" if roi_id else ""))
            return sorted(samples)
            
        except Exception as e:
            logger.error(f"Failed to list golden samples: {e}")
            return []
    
    def create_temp_directory(self, prefix: str = "client_") -> Path:
        """
        Create a temporary directory.
        
        Args:
            prefix: Prefix for the temp directory name
            
        Returns:
            Path to the created temporary directory
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_dir = self.temp_path / f"{prefix}{timestamp}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Created temporary directory: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            logger.error(f"Failed to create temp directory: {e}")
            raise OSError(f"Failed to create temp directory: {e}")
    
    def cleanup_temp_directories(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary directories.
        
        Args:
            max_age_hours: Maximum age in hours for temp directories
            
        Returns:
            Number of directories cleaned up
        """
        try:
            if not self.temp_path.exists():
                return 0
            
            count = 0
            current_time = datetime.now()
            
            for temp_dir in self.temp_path.iterdir():
                if temp_dir.is_dir():
                    # Get directory modification time
                    mod_time = datetime.fromtimestamp(temp_dir.stat().st_mtime)
                    age_hours = (current_time - mod_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        shutil.rmtree(temp_dir)
                        count += 1
                        logger.debug(f"Cleaned up old temp directory: {temp_dir.name}")
            
            if count > 0:
                logger.info(f"Cleaned up {count} old temporary directories")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp directories: {e}")
            return 0
    
    def get_disk_usage(self) -> Dict[str, int]:
        """
        Get disk usage statistics for the shared folder.
        
        Returns:
            Dictionary with disk usage info:
            - total: Total size in bytes
            - sessions: Size of sessions directory
            - golden_samples: Size of golden samples directory
            - temp: Size of temp directory
        """
        try:
            def get_dir_size(path: Path) -> int:
                """Calculate total size of a directory."""
                total = 0
                if path.exists():
                    for item in path.rglob('*'):
                        if item.is_file():
                            total += item.stat().st_size
                return total
            
            usage = {
                'total': get_dir_size(self.base_path),
                'sessions': get_dir_size(self.sessions_path),
                'golden_samples': get_dir_size(self.golden_samples_path),
                'temp': get_dir_size(self.temp_path)
            }
            
            logger.debug(f"Disk usage: total={usage['total']/1024/1024:.2f}MB, "
                        f"sessions={usage['sessions']/1024/1024:.2f}MB, "
                        f"golden={usage['golden_samples']/1024/1024:.2f}MB, "
                        f"temp={usage['temp']/1024/1024:.2f}MB")
            
            return usage
            
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {'total': 0, 'sessions': 0, 'golden_samples': 0, 'temp': 0}


# Convenience function for backward compatibility
def get_shared_folder_manager(base_path: str = "/mnt/visual-aoi-shared") -> SharedFolderManager:
    """
    Get a SharedFolderManager instance.
    
    Args:
        base_path: Root path to the shared folder
        
    Returns:
        SharedFolderManager instance
    """
    return SharedFolderManager(base_path)
