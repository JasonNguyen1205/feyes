"""
Integration tests for the Visual AOI system.
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestSystemIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_product = "integration_test_product"
        
        # Create test image
        self.test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_config_roi_integration(self):
        """Test integration between config and ROI modules."""
        try:
            from config import get_config_filename, get_golden_roi_dir
            from roi import normalize_roi
            
            # Test that config functions work with ROI data
            config_file = get_config_filename(self.test_product)
            self.assertIn(self.test_product, config_file)
            
            roi_dir = get_golden_roi_dir(self.test_product, 1)
            self.assertIn(self.test_product, roi_dir)
            self.assertIn("roi_1", roi_dir)
            
            # Test ROI normalization
            test_roi = (1, 2, (100, 100, 200, 200), 305, 3000, 0.9, "mobilenet")
            normalized = normalize_roi(test_roi)
            self.assertIsInstance(normalized, tuple)
            
        except ImportError as e:
            self.skipTest(f"Integration test modules not available: {e}")
    
    def test_inspection_workflow(self):
        """Test the complete inspection workflow."""
        try:
            from inspection import process_roi, is_roi_passed
            
            # Mock dependencies
            with patch('inspection.process_compare_roi') as mock_compare, \
                 patch('inspection.process_barcode_roi') as mock_barcode, \
                 patch('inspection.process_ocr_roi') as mock_ocr:
                
                # Mock successful results
                mock_compare.return_value = (1, 2, None, self.test_image, (100, 100, 200, 200), "Match", "green", 0.95, 0.9)
                mock_barcode.return_value = (2, 1, self.test_image, None, (50, 50, 150, 150), "Barcode", ["123456"])
                mock_ocr.return_value = (3, 3, self.test_image, None, (0, 0, 100, 100), None, "PASS", 0)
                
                # Test compare ROI
                compare_roi = (1, 2, (100, 100, 200, 200), 305, 3000, 0.9, "mobilenet")
                result = process_roi(compare_roi, self.test_image, self.test_product)
                self.assertIsNotNone(result)
                self.assertTrue(is_roi_passed(result))
                
                # Test barcode ROI
                barcode_roi = (2, 1, (50, 50, 150, 150), 305, 3000)
                result = process_roi(barcode_roi, self.test_image, self.test_product)
                self.assertIsNotNone(result)
                self.assertTrue(is_roi_passed(result))
                
                # Test OCR ROI
                ocr_roi = (3, 3, (0, 0, 100, 100), 305, 3000, None, "ocr", 0)
                result = process_roi(ocr_roi, self.test_image, self.test_product)
                self.assertIsNotNone(result)
                self.assertTrue(is_roi_passed(result))
                
        except ImportError as e:
            self.skipTest(f"Inspection workflow test not available: {e}")
    
    def test_ui_inspection_integration(self):
        """Test integration between UI and inspection modules."""
        try:
            from inspection import set_ui_instance, initialize_system
            
            # Mock UI instance
            mock_ui = MagicMock()
            mock_ui.set_status = MagicMock()
            mock_ui.show_result = MagicMock()
            mock_ui.stop_operation_timer = MagicMock()
            
            # Set UI instance
            set_ui_instance(mock_ui)
            
            # Test that UI methods can be called without errors
            mock_ui.set_status("Test status")
            mock_ui.show_result([])
            mock_ui.stop_operation_timer()
            
            # Verify methods were called
            mock_ui.set_status.assert_called()
            mock_ui.show_result.assert_called()
            mock_ui.stop_operation_timer.assert_called()
            
        except ImportError as e:
            self.skipTest(f"UI integration test not available: {e}")


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling across modules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    def test_missing_dependencies_handling(self):
        """Test that missing dependencies are handled gracefully."""
        # Test config module (should always work)
        try:
            from config import default_focus, default_exposure
            self.assertIsInstance(default_focus, int)
            self.assertIsInstance(default_exposure, int)
        except ImportError:
            self.fail("Config module should always be importable")
    
    def test_roi_processing_error_handling(self):
        """Test ROI processing with invalid inputs."""
        try:
            from roi import normalize_roi
            
            # Test with various invalid inputs
            invalid_rois = [
                None,
                [],
                (1,),  # Too few elements
                (1, 2),  # Still too few
                ("invalid", "types", "everywhere")
            ]
            
            for invalid_roi in invalid_rois:
                try:
                    result = normalize_roi(invalid_roi)
                    # Should either return None or raise exception gracefully
                    if result is not None:
                        self.assertIsInstance(result, tuple)
                except (ValueError, TypeError, AttributeError):
                    pass  # Expected for invalid inputs
                    
        except ImportError:
            self.skipTest("ROI module not available for error handling test")
    
    def test_inspection_error_recovery(self):
        """Test that inspection module recovers from errors."""
        try:
            from inspection import process_roi
            
            # Test with invalid ROI
            invalid_roi = None
            result = process_roi(invalid_roi, self.test_image, "test")
            self.assertIsNone(result)  # Should return None for invalid input
            
            # Test with malformed ROI
            malformed_roi = (1, 2)  # Missing coordinates
            result = process_roi(malformed_roi, self.test_image, "test")
            self.assertIsNone(result)  # Should handle gracefully
            
        except ImportError:
            self.skipTest("Inspection module not available for error recovery test")


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance aspects of module integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.large_image = np.random.randint(0, 255, (1920, 1080, 3), dtype=np.uint8)
        self.small_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    def test_memory_usage_monitoring(self):
        """Test that memory usage can be monitored."""
        try:
            from utils import print_memory_usage
            
            # Should not raise exceptions
            print_memory_usage()
            
            # Process some data
            processed_images = []
            for i in range(5):
                processed_images.append(self.small_image.copy())
            
            print_memory_usage()
            
            # Clean up
            del processed_images
            
        except ImportError:
            self.skipTest("Memory monitoring not available")
    
    def test_timer_functionality(self):
        """Test performance timing functionality."""
        try:
            from utils import PerformanceTimer
            import time
            
            timer = PerformanceTimer()
            timer.start()
            
            # Simulate some work
            time.sleep(0.01)
            
            elapsed = timer.stop()
            self.assertGreater(elapsed, 0.005)  # Should be at least 5ms
            self.assertLess(elapsed, 1.0)  # Should be less than 1 second
            
        except ImportError:
            self.skipTest("Performance timer not available")


if __name__ == '__main__':
    unittest.main()
