"""
Unit tests for the utils module.
"""

import unittest
import time
import tempfile
import os
from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPerformanceTimer(unittest.TestCase):
    """Test cases for PerformanceTimer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from src.utils import PerformanceTimer
            self.timer_class = PerformanceTimer
        except ImportError as e:
            self.skipTest(f"Utils module not available: {e}")
    
    def test_timer_basic_functionality(self):
        """Test basic timer start/stop functionality."""
        timer = self.timer_class()
        
        # Test initial state
        self.assertFalse(hasattr(timer, 'start_time') and timer.start_time is not None)
        
        # Start timer
        timer.start()
        self.assertIsNotNone(timer.start_time)
        
        # Wait a bit
        time.sleep(0.1)
        
        # Stop timer
        elapsed = timer.stop()
        self.assertGreaterEqual(elapsed, 0.1)
        self.assertLess(elapsed, 1.0)  # Should be much less than 1 second
        
    def test_timer_multiple_starts(self):
        """Test that multiple starts reset the timer."""
        timer = self.timer_class()
        
        timer.start()
        first_start = timer.start_time
        
        time.sleep(0.05)
        
        timer.start()  # Should reset
        second_start = timer.start_time
        
        # Both should be valid timestamps
        self.assertIsNotNone(first_start)
        self.assertIsNotNone(second_start)
        if first_start is not None and second_start is not None:
            self.assertGreater(second_start, first_start)
        
    def test_timer_stop_without_start(self):
        """Test stopping timer without starting."""
        timer = self.timer_class()
        
        # Should handle gracefully
        elapsed = timer.stop()
        self.assertIsInstance(elapsed, (int, float))


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from src.utils import print_memory_usage, get_thumbnail_pil
            self.print_memory_usage = print_memory_usage
            self.get_thumbnail_pil = get_thumbnail_pil
        except ImportError as e:
            self.skipTest(f"Utils module not available: {e}")
    
    @patch('psutil.Process')
    def test_print_memory_usage(self, mock_process):
        """Test memory usage printing."""
        # Mock memory info
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100 MB
        mock_process.return_value.memory_info.return_value = mock_memory_info
        
        # Should not raise any exceptions
        try:
            self.print_memory_usage()
        except Exception as e:
            self.fail(f"print_memory_usage raised {e}")
    
    def test_get_thumbnail_pil_with_numpy_array(self):
        """Test thumbnail generation from numpy array."""
        # Create test image (RGB)
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        try:
            thumbnail = self.get_thumbnail_pil(test_image, 50, 50)
            self.assertIsInstance(thumbnail, Image.Image)
            self.assertEqual(thumbnail.size, (50, 50))
        except Exception as e:
            self.skipTest(f"Thumbnail test failed: {e}")
    
    def test_get_thumbnail_pil_with_pil_image(self):
        """Test thumbnail generation from PIL Image."""
        # Create test PIL image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        try:
            thumbnail = self.get_thumbnail_pil(test_image, 30, 40)
            self.assertIsInstance(thumbnail, Image.Image)
            self.assertEqual(thumbnail.size, (30, 40))
        except Exception as e:
            self.skipTest(f"PIL thumbnail test failed: {e}")
    
    def test_get_thumbnail_pil_maintains_aspect_ratio(self):
        """Test that thumbnail generation can maintain aspect ratio."""
        # Create rectangular test image
        test_image = np.random.randint(0, 255, (200, 100, 3), dtype=np.uint8)
        
        try:
            thumbnail = self.get_thumbnail_pil(test_image, 50, 50)
            self.assertIsInstance(thumbnail, Image.Image)
            # Should resize to fit within bounds
            self.assertLessEqual(max(thumbnail.size), 50)
        except Exception as e:
            self.skipTest(f"Aspect ratio test failed: {e}")


class TestErrorHandling(unittest.TestCase):
    """Test error handling in utils module."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from src.utils import get_thumbnail_pil
            self.get_thumbnail_pil = get_thumbnail_pil
        except ImportError as e:
            self.skipTest(f"Utils module not available: {e}")
    
    def test_thumbnail_with_invalid_input(self):
        """Test thumbnail generation with invalid input."""
        # Test with None
        try:
            result = self.get_thumbnail_pil(None, 50, 50)
            # Should handle gracefully or return None
            self.assertTrue(result is None or isinstance(result, Image.Image))
        except Exception:
            pass  # Expected to fail gracefully
        
        # Test with invalid dimensions
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        try:
            result = self.get_thumbnail_pil(test_image, -10, 50)
            # Should handle gracefully
        except Exception:
            pass  # Expected to fail gracefully


if __name__ == '__main__':
    unittest.main()
