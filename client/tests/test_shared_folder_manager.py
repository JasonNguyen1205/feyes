#!/usr/bin/env python3
"""
Unit tests for SharedFolderManager

Tests all functionality of the shared folder management system.
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from client.shared_folder_manager import SharedFolderManager


class TestSharedFolderManager(unittest.TestCase):
    """Test suite for SharedFolderManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        self.sfm = SharedFolderManager(base_path=self.test_dir)
        self.test_session_id = "test_session_001"
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    # =========================================================================
    # Connection Tests
    # =========================================================================
    
    def test_check_server_connection_success(self):
        """Test successful server connection check."""
        # Test directory should be accessible
        self.assertTrue(self.sfm.check_server_connection())
    
    def test_check_server_connection_failure(self):
        """Test failed server connection check."""
        # Create SFM with non-existent path
        sfm = SharedFolderManager(base_path="/nonexistent/path/12345")
        self.assertFalse(sfm.check_server_connection())
    
    # =========================================================================
    # Directory Path Tests
    # =========================================================================
    
    def test_get_session_directory(self):
        """Test getting session directory path."""
        session_dir = self.sfm.get_session_directory(self.test_session_id)
        
        self.assertIsInstance(session_dir, Path)
        self.assertEqual(session_dir.name, self.test_session_id)
        self.assertIn("sessions", str(session_dir))
    
    def test_get_session_input_directory(self):
        """Test getting session input directory path."""
        input_dir = self.sfm.get_session_input_directory(self.test_session_id)
        
        self.assertIsInstance(input_dir, Path)
        self.assertEqual(input_dir.name, "input")
        self.assertIn(self.test_session_id, str(input_dir))
    
    def test_get_session_output_directory(self):
        """Test getting session output directory path."""
        output_dir = self.sfm.get_session_output_directory(self.test_session_id)
        
        self.assertIsInstance(output_dir, Path)
        self.assertEqual(output_dir.name, "output")
        self.assertIn(self.test_session_id, str(output_dir))
    
    # =========================================================================
    # Session Directory Creation Tests
    # =========================================================================
    
    def test_create_session_directories(self):
        """Test creating session directories."""
        input_dir, output_dir = self.sfm.create_session_directories(self.test_session_id)
        
        # Check both directories were created
        self.assertTrue(input_dir.exists())
        self.assertTrue(output_dir.exists())
        self.assertTrue(input_dir.is_dir())
        self.assertTrue(output_dir.is_dir())
        
        # Check structure
        self.assertEqual(input_dir.name, "input")
        self.assertEqual(output_dir.name, "output")
        self.assertEqual(input_dir.parent.name, self.test_session_id)
    
    def test_create_session_directories_idempotent(self):
        """Test that creating directories multiple times is safe."""
        # Create once
        input_dir1, output_dir1 = self.sfm.create_session_directories(self.test_session_id)
        
        # Create again - should not fail
        input_dir2, output_dir2 = self.sfm.create_session_directories(self.test_session_id)
        
        # Should return same paths
        self.assertEqual(input_dir1, input_dir2)
        self.assertEqual(output_dir1, output_dir2)
    
    # =========================================================================
    # Image Save/Read Tests
    # =========================================================================
    
    def test_save_captured_image(self):
        """Test saving a captured image."""
        self.sfm.create_session_directories(self.test_session_id)
        
        test_data = b"fake_image_data_12345"
        filename = "test_capture.jpg"
        
        image_path = self.sfm.save_captured_image(
            self.test_session_id, test_data, filename
        )
        
        # Check file was created
        self.assertTrue(image_path.exists())
        self.assertEqual(image_path.name, filename)
        
        # Verify content
        with open(image_path, 'rb') as f:
            saved_data = f.read()
        self.assertEqual(saved_data, test_data)
    
    def test_save_captured_image_with_metadata(self):
        """Test saving image with metadata."""
        self.sfm.create_session_directories(self.test_session_id)
        
        test_data = b"fake_image_data"
        filename = "test_capture_with_meta.jpg"
        metadata = {
            'focus': 325,
            'exposure': 1500,
            'timestamp': '2025-10-03T10:30:00',
            'rois': [1, 2, 3]
        }
        
        image_path = self.sfm.save_captured_image(
            self.test_session_id, test_data, filename, metadata=metadata
        )
        
        # Check metadata file was created
        metadata_path = image_path.parent / f"{filename}.metadata.json"
        self.assertTrue(metadata_path.exists())
        
        # Verify metadata content
        with open(metadata_path, 'r') as f:
            saved_metadata = json.load(f)
        self.assertEqual(saved_metadata, metadata)
    
    def test_read_roi_image_success(self):
        """Test reading an ROI image successfully."""
        # Create session and save test image
        output_dir = self.sfm.get_session_output_directory(self.test_session_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_data = b"roi_image_data"
        filename = "roi_1_captured.jpg"
        test_path = output_dir / filename
        
        with open(test_path, 'wb') as f:
            f.write(test_data)
        
        # Read the image
        read_data = self.sfm.read_roi_image(self.test_session_id, filename)
        
        self.assertIsNotNone(read_data)
        self.assertEqual(read_data, test_data)
    
    def test_read_roi_image_not_found(self):
        """Test reading non-existent ROI image."""
        self.sfm.create_session_directories(self.test_session_id)
        
        read_data = self.sfm.read_roi_image(
            self.test_session_id, "nonexistent.jpg"
        )
        
        self.assertIsNone(read_data)
    
    def test_get_roi_image_path_success(self):
        """Test getting ROI image path when file exists."""
        # Create session and test image
        output_dir = self.sfm.get_session_output_directory(self.test_session_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = "roi_2_captured.jpg"
        test_path = output_dir / filename
        test_path.touch()
        
        # Get path
        returned_path = self.sfm.get_roi_image_path(self.test_session_id, filename)
        
        self.assertIsNotNone(returned_path)
        self.assertEqual(returned_path, test_path)
    
    def test_get_roi_image_path_not_found(self):
        """Test getting ROI image path when file doesn't exist."""
        self.sfm.create_session_directories(self.test_session_id)
        
        returned_path = self.sfm.get_roi_image_path(
            self.test_session_id, "missing.jpg"
        )
        
        self.assertIsNone(returned_path)
    
    # =========================================================================
    # Golden Image Tests
    # =========================================================================
    
    def test_read_golden_image(self):
        """Test reading a golden image."""
        output_dir = self.sfm.get_session_output_directory(self.test_session_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_data = b"golden_image_data"
        filename = "roi_1_golden.jpg"
        test_path = output_dir / filename
        
        with open(test_path, 'wb') as f:
            f.write(test_data)
        
        read_data = self.sfm.read_golden_image(self.test_session_id, filename)
        
        self.assertIsNotNone(read_data)
        self.assertEqual(read_data, test_data)
    
    def test_get_golden_image_path(self):
        """Test getting golden image path."""
        output_dir = self.sfm.get_session_output_directory(self.test_session_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = "roi_3_golden.jpg"
        test_path = output_dir / filename
        test_path.touch()
        
        returned_path = self.sfm.get_golden_image_path(self.test_session_id, filename)
        
        self.assertIsNotNone(returned_path)
        self.assertEqual(returned_path, test_path)
    
    # =========================================================================
    # Results JSON Tests
    # =========================================================================
    
    def test_read_results_json(self):
        """Test reading results JSON file."""
        output_dir = self.sfm.get_session_output_directory(self.test_session_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_results = {
            'overall_result': {'passed': True, 'total_rois': 5},
            'roi_results': []
        }
        
        results_path = output_dir / "results.json"
        with open(results_path, 'w') as f:
            json.dump(test_results, f)
        
        read_results = self.sfm.read_results_json(self.test_session_id)
        
        self.assertIsNotNone(read_results)
        self.assertEqual(read_results, test_results)
    
    def test_read_results_json_not_found(self):
        """Test reading non-existent results JSON."""
        self.sfm.create_session_directories(self.test_session_id)
        
        read_results = self.sfm.read_results_json(self.test_session_id)
        
        self.assertIsNone(read_results)
    
    # =========================================================================
    # List Images Tests
    # =========================================================================
    
    def test_list_session_images_input(self):
        """Test listing images in input directory."""
        input_dir = self.sfm.get_session_input_directory(self.test_session_id)
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test images
        test_files = ["image1.jpg", "image2.png", "image3.bmp", "not_image.txt"]
        for filename in test_files:
            (input_dir / filename).touch()
        
        images = self.sfm.list_session_images(self.test_session_id, directory="input")
        
        # Should only return image files
        self.assertEqual(len(images), 3)
        self.assertIn("image1.jpg", images)
        self.assertIn("image2.png", images)
        self.assertIn("image3.bmp", images)
        self.assertNotIn("not_image.txt", images)
    
    def test_list_session_images_output(self):
        """Test listing images in output directory."""
        output_dir = self.sfm.get_session_output_directory(self.test_session_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test images
        test_files = ["roi_1.jpg", "roi_2.jpg"]
        for filename in test_files:
            (output_dir / filename).touch()
        
        images = self.sfm.list_session_images(self.test_session_id, directory="output")
        
        self.assertEqual(len(images), 2)
        self.assertIn("roi_1.jpg", images)
        self.assertIn("roi_2.jpg", images)
    
    def test_list_session_images_empty_directory(self):
        """Test listing images in empty directory."""
        self.sfm.create_session_directories(self.test_session_id)
        
        images = self.sfm.list_session_images(self.test_session_id, directory="input")
        
        self.assertEqual(len(images), 0)
    
    # =========================================================================
    # Session Cleanup Tests
    # =========================================================================
    
    def test_cleanup_session_keep_output(self):
        """Test cleaning up session while keeping output."""
        # Create session with files
        input_dir, output_dir = self.sfm.create_session_directories(self.test_session_id)
        
        (input_dir / "input_file.jpg").touch()
        (output_dir / "output_file.jpg").touch()
        
        # Cleanup (keep output)
        success = self.sfm.cleanup_session(self.test_session_id, keep_output=True)
        
        self.assertTrue(success)
        self.assertFalse(input_dir.exists())  # Input deleted
        self.assertTrue(output_dir.exists())  # Output kept
    
    def test_cleanup_session_delete_all(self):
        """Test cleaning up entire session."""
        # Create session with files
        input_dir, output_dir = self.sfm.create_session_directories(self.test_session_id)
        session_dir = self.sfm.get_session_directory(self.test_session_id)
        
        (input_dir / "input_file.jpg").touch()
        (output_dir / "output_file.jpg").touch()
        
        # Cleanup (delete all)
        success = self.sfm.cleanup_session(self.test_session_id, keep_output=False)
        
        self.assertTrue(success)
        self.assertFalse(session_dir.exists())  # Entire session deleted
    
    def test_cleanup_session_not_found(self):
        """Test cleaning up non-existent session."""
        success = self.sfm.cleanup_session("nonexistent_session")
        
        self.assertFalse(success)
    
    # =========================================================================
    # Golden Samples Tests
    # =========================================================================
    
    def test_get_golden_samples_directory(self):
        """Test getting golden samples directory."""
        product_name = "test_product"
        golden_dir = self.sfm.get_golden_samples_directory(product_name)
        
        self.assertIsInstance(golden_dir, Path)
        self.assertEqual(golden_dir.name, product_name)
        self.assertIn("golden_samples", str(golden_dir))
    
    def test_list_golden_samples(self):
        """Test listing golden samples for a product."""
        product_name = "test_product"
        golden_dir = self.sfm.get_golden_samples_directory(product_name)
        golden_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test golden samples
        test_samples = [
            "roi_1_sample_1.jpg",
            "roi_1_sample_2.jpg",
            "roi_2_sample_1.jpg",
            "roi_3_sample_1.png"
        ]
        for sample in test_samples:
            (golden_dir / sample).touch()
        
        samples = self.sfm.list_golden_samples(product_name)
        
        self.assertEqual(len(samples), 4)
        for sample in test_samples:
            self.assertIn(sample, samples)
    
    def test_list_golden_samples_filtered_by_roi(self):
        """Test listing golden samples filtered by ROI ID."""
        product_name = "test_product"
        golden_dir = self.sfm.get_golden_samples_directory(product_name)
        golden_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test golden samples
        test_samples = [
            "roi_1_sample_1.jpg",
            "roi_1_sample_2.jpg",
            "roi_2_sample_1.jpg"
        ]
        for sample in test_samples:
            (golden_dir / sample).touch()
        
        # Filter for ROI 1
        samples = self.sfm.list_golden_samples(product_name, roi_id=1)
        
        self.assertEqual(len(samples), 2)
        self.assertIn("roi_1_sample_1.jpg", samples)
        self.assertIn("roi_1_sample_2.jpg", samples)
        self.assertNotIn("roi_2_sample_1.jpg", samples)
    
    # =========================================================================
    # Temporary Directory Tests
    # =========================================================================
    
    def test_create_temp_directory(self):
        """Test creating temporary directory."""
        temp_dir = self.sfm.create_temp_directory(prefix="test_")
        
        self.assertTrue(temp_dir.exists())
        self.assertTrue(temp_dir.is_dir())
        self.assertIn("temp", str(temp_dir))
        self.assertTrue(temp_dir.name.startswith("test_"))
    
    def test_cleanup_temp_directories(self):
        """Test cleaning up old temporary directories."""
        temp_path = self.sfm.temp_path
        temp_path.mkdir(parents=True, exist_ok=True)
        
        # Create old temp directory
        old_temp = temp_path / "old_temp"
        old_temp.mkdir()
        
        # Set modification time to 25 hours ago
        old_time = datetime.now() - timedelta(hours=25)
        os.utime(old_temp, (old_time.timestamp(), old_time.timestamp()))
        
        # Create new temp directory
        new_temp = temp_path / "new_temp"
        new_temp.mkdir()
        
        # Cleanup directories older than 24 hours
        count = self.sfm.cleanup_temp_directories(max_age_hours=24)
        
        self.assertEqual(count, 1)
        self.assertFalse(old_temp.exists())
        self.assertTrue(new_temp.exists())
    
    # =========================================================================
    # Disk Usage Tests
    # =========================================================================
    
    def test_get_disk_usage(self):
        """Test getting disk usage statistics."""
        # Create some test data
        self.sfm.create_session_directories(self.test_session_id)
        input_dir = self.sfm.get_session_input_directory(self.test_session_id)
        
        # Create test file
        test_file = input_dir / "test.jpg"
        test_data = b"x" * 1024  # 1KB
        with open(test_file, 'wb') as f:
            f.write(test_data)
        
        usage = self.sfm.get_disk_usage()
        
        self.assertIsInstance(usage, dict)
        self.assertIn('total', usage)
        self.assertIn('sessions', usage)
        self.assertIn('golden_samples', usage)
        self.assertIn('temp', usage)
        
        # Should have at least 1KB in sessions
        self.assertGreaterEqual(usage['sessions'], 1024)


class TestSharedFolderManagerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.sfm = SharedFolderManager(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_save_image_creates_directories(self):
        """Test that saving image creates directories if they don't exist."""
        test_data = b"test"
        
        # Don't create directories first
        image_path = self.sfm.save_captured_image(
            "auto_session", test_data, "auto.jpg"
        )
        
        self.assertTrue(image_path.exists())
    
    def test_list_images_invalid_directory_type(self):
        """Test listing images with invalid directory type."""
        images = self.sfm.list_session_images("test", directory="invalid")
        
        self.assertEqual(len(images), 0)
    
    def test_get_disk_usage_empty(self):
        """Test disk usage on empty directories."""
        usage = self.sfm.get_disk_usage()
        
        # Should return zeros or very small values
        self.assertGreaterEqual(usage['total'], 0)
        self.assertGreaterEqual(usage['sessions'], 0)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSharedFolderManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSharedFolderManagerEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
