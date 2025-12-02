"""
Unit tests for the config module.
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import (
    PRODUCT_NAME, default_focus, default_exposure, 
    get_config_filename, get_golden_roi_dir, 
    FOCUS_SETTLE_DELAY, AI_THRESHOLD
)


class TestConfig(unittest.TestCase):
    """Test cases for config module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_product = "20004960"
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_default_values(self):
        """Test that default configuration values are properly set."""
        self.assertEqual(default_focus, 305)
        self.assertEqual(default_exposure, 15000)  # Updated to match camera.json config
        self.assertEqual(FOCUS_SETTLE_DELAY, 3.0)
        self.assertEqual(AI_THRESHOLD, 0.9)
        
    def test_get_config_filename(self):
        """Test config filename generation."""
        expected = f"config/products/{self.test_product}/rois_config_{self.test_product}.json"
        result = get_config_filename(self.test_product)
        self.assertEqual(result, expected)
        
    def test_get_config_filename_with_none(self):
        """Test config filename generation with None product name."""
        with self.assertRaises(TypeError):
            get_config_filename(None)
            
    def test_get_golden_roi_dir(self):
        """Test golden ROI directory path generation."""
        test_idx = 5
        expected = f"config/products/{self.test_product}/golden_rois/roi_{test_idx}"
        result = get_golden_roi_dir(self.test_product, test_idx)
        self.assertEqual(result, expected)
        
    def test_get_golden_roi_dir_with_invalid_idx(self):
        """Test golden ROI directory with invalid index."""
        with self.assertRaises((TypeError, ValueError)):
            get_golden_roi_dir(self.test_product, "invalid")
            
    def test_product_name_environment_variable(self):
        """Test PRODUCT_NAME from environment variable."""
        with patch.dict(os.environ, {'PRODUCT_NAME': 'env_product'}):
            # Re-import to pick up environment variable
            import importlib
            import src.config
            importlib.reload(src.config)
            # Note: This test might need adjustment based on actual implementation
            
    def test_constants_are_immutable_types(self):
        """Test that configuration constants are immutable types."""
        self.assertIsInstance(default_focus, int)
        self.assertIsInstance(default_exposure, int)
        self.assertIsInstance(FOCUS_SETTLE_DELAY, (int, float))
        self.assertIsInstance(AI_THRESHOLD, (int, float))
        
    def test_threshold_values_in_valid_range(self):
        """Test that threshold values are in valid ranges."""
        self.assertGreaterEqual(AI_THRESHOLD, 0.0)
        self.assertLessEqual(AI_THRESHOLD, 1.0)
        self.assertGreater(FOCUS_SETTLE_DELAY, 0.0)
        
    def test_focus_exposure_in_valid_range(self):
        """Test that focus and exposure values are in valid ranges."""
        self.assertGreaterEqual(default_focus, 0)
        self.assertLessEqual(default_focus, 1023)
        self.assertGreaterEqual(default_exposure, 100)
        self.assertLessEqual(default_exposure, 1000000)


if __name__ == '__main__':
    unittest.main()
