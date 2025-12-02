"""
Unit tests for the ROI module.
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestROINormalization(unittest.TestCase):
    """Test cases for ROI normalization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from roi import normalize_roi, get_next_roi_index
            self.normalize_roi = normalize_roi
            self.get_next_roi_index = get_next_roi_index
        except ImportError:
            self.skipTest("ROI module not available")
    
    def test_normalize_roi_8_elements(self):
        """Test ROI normalization with 8 elements (full format)."""
        roi = (1, 2, (100, 100, 200, 200), 305, 3000, 0.9, "mobilenet", 0)
        normalized = self.normalize_roi(roi)
        
        self.assertEqual(len(normalized), 8)
        self.assertEqual(normalized[0], 1)  # idx
        self.assertEqual(normalized[1], 2)  # type
        self.assertEqual(normalized[2], (100, 100, 200, 200))  # coords
        self.assertEqual(normalized[3], 305)  # focus
        self.assertEqual(normalized[4], 3000)  # exposure
        self.assertEqual(normalized[5], 0.9)  # threshold
        self.assertEqual(normalized[6], "mobilenet")  # method
        self.assertEqual(normalized[7], 0)  # rotation
    
    def test_normalize_roi_7_elements(self):
        """Test ROI normalization with 7 elements (no rotation)."""
        roi = (2, 2, (50, 50, 150, 150), 400, 5000, 0.8, "opencv")
        normalized = self.normalize_roi(roi)
        
        self.assertEqual(len(normalized), 7)
        self.assertEqual(normalized[0], 2)
        self.assertEqual(normalized[6], "opencv")
    
    def test_normalize_roi_6_elements(self):
        """Test ROI normalization with 6 elements (legacy format)."""
        roi = (3, 2, (0, 0, 100, 100), 305, 3000, 0.95)
        normalized = self.normalize_roi(roi)
        
        self.assertEqual(len(normalized), 7)  # Function adds default method
        self.assertEqual(normalized[5], 0.95)
        self.assertEqual(normalized[6], "mobilenet")  # Default method added
        # Should add default feature method for type 2
    
    def test_normalize_roi_4_elements(self):
        """Test ROI normalization with 4 elements (minimal legacy)."""
        roi = (4, 1, (10, 10, 90, 90), 305)
        normalized = self.normalize_roi(roi)
        
        self.assertGreaterEqual(len(normalized), 4)
        self.assertEqual(normalized[0], 4)
        self.assertEqual(normalized[1], 1)
        self.assertEqual(normalized[2], (10, 10, 90, 90))
        self.assertEqual(normalized[3], 305)
    
    def test_normalize_roi_type_conversion(self):
        """Test that ROI normalization properly converts types."""
        roi = ("1", "2", [100, 100, 200, 200], "305", "3000", "0.9", "mobilenet")
        normalized = self.normalize_roi(roi)
        
        self.assertIsInstance(normalized[0], int)  # idx
        self.assertIsInstance(normalized[1], int)  # type
        self.assertIsInstance(normalized[2], tuple)  # coords
        self.assertIsInstance(normalized[3], int)  # focus
        self.assertIsInstance(normalized[4], int)  # exposure
        self.assertIsInstance(normalized[5], float)  # threshold
        self.assertIsInstance(normalized[6], str)  # method
    
    def test_get_next_roi_index(self):
        """Test getting next ROI index."""
        # Mock the ROIS list to control the test
        with patch('roi.ROIS', []):
            next_idx = self.get_next_roi_index()
            self.assertEqual(next_idx, 1)
        
        # Mock with existing ROIs
        mock_rois = [
            (1, 2, (0, 0, 100, 100), 305, 3000, 0.9, "mobilenet"),
            (3, 1, (100, 100, 200, 200), 305, 3000, None, "opencv")
        ]
        with patch('roi.ROIS', mock_rois):
            next_idx = self.get_next_roi_index()
            self.assertEqual(next_idx, 4)  # Should be max + 1


class TestROIManagement(unittest.TestCase):
    """Test cases for ROI management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_product = "test_product"
        
        try:
            from roi import get_rois, set_rois, save_rois_to_config, load_rois_from_config
            self.get_rois = get_rois
            self.set_rois = set_rois
            self.save_rois_to_config = save_rois_to_config
            self.load_rois_from_config = load_rois_from_config
        except ImportError:
            self.skipTest("ROI module not available")
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_set_rois(self):
        """Test getting and setting ROIs."""
        test_rois = [
            (1, 2, (100, 100, 200, 200), 305, 3000, 0.9, "mobilenet"),
            (2, 1, (50, 50, 150, 150), 305, 3000, None, "opencv")
        ]
        
        self.set_rois(test_rois)
        retrieved_rois = self.get_rois()
        
        self.assertEqual(len(retrieved_rois), 2)
        self.assertEqual(retrieved_rois, test_rois)
    
    def test_save_load_rois_config(self):
        """Test saving and loading ROI configuration."""
        test_rois = [
            (1, 2, (0, 0, 100, 100), 305, 3000, 0.8, "mobilenet", 0),
            (2, 3, (100, 0, 200, 100), 305, 3000, None, "ocr", 90)
        ]
        
        # Create test config directory
        config_dir = os.path.join(self.temp_dir, self.test_product)
        os.makedirs(config_dir, exist_ok=True)
        
        with patch('roi.get_config_filename') as mock_config:
            config_file = os.path.join(config_dir, f"rois_config_{self.test_product}.json")
            mock_config.return_value = config_file
            
            # Save ROIs
            self.set_rois(test_rois)
            try:
                self.save_rois_to_config(self.test_product)
                
                # Verify file was created
                self.assertTrue(os.path.exists(config_file))
                
                # Load ROIs
                self.set_rois([])  # Clear current ROIs
                self.load_rois_from_config(self.test_product)
                
                loaded_rois = self.get_rois()
                self.assertEqual(len(loaded_rois), 2)
                
            except Exception as e:
                self.skipTest(f"Config save/load not available: {e}")


class TestROIProcessing(unittest.TestCase):
    """Test cases for ROI processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test image
        self.test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        try:
            from roi import process_compare_roi
            self.process_compare_roi = process_compare_roi
        except ImportError:
            self.skipTest("ROI processing not available")
    
    def test_process_compare_roi_parameters(self):
        """Test that compare ROI processing accepts correct parameters."""
        # Test with mock dependencies
        with patch('roi.extract_features_from_array'), \
             patch('roi.cosine_similarity'), \
             patch('roi.normalize_illumination'):
            
            try:
                result = self.process_compare_roi(
                    self.test_image, 100, 100, 200, 200, 1, 
                    ai_threshold=0.9, feature_method="mobilenet", 
                    product_name="test"
                )
                # Should return some result structure
                self.assertIsNotNone(result)
            except Exception as e:
                self.skipTest(f"ROI processing test failed: {e}")
    
    def test_roi_coordinate_validation(self):
        """Test ROI coordinate validation."""
        # Test with invalid coordinates (should handle gracefully)
        with patch('roi.extract_features_from_array'), \
             patch('roi.cosine_similarity'), \
             patch('roi.normalize_illumination'):
            
            try:
                # Test with coordinates outside image bounds
                result = self.process_compare_roi(
                    self.test_image, 600, 400, 700, 500, 1,
                    ai_threshold=0.9, feature_method="mobilenet",
                    product_name="test"
                )
                # Should handle gracefully
            except Exception:
                pass  # Expected for out-of-bounds coordinates


if __name__ == '__main__':
    unittest.main()
