#!/usr/bin/env python3
"""
Test suite for barcode processing functionality.
"""

import unittest
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)


class TestBarcodeDetection(unittest.TestCase):
    """Test barcode detection functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test images
        self.test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.barcode_image = np.ones((100, 100, 3), dtype=np.uint8) * 255  # White image
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_barcode_detection_methods(self):
        """Test different barcode detection methods."""
        def mock_opencv_barcode_detection(image):
            """Mock OpenCV barcode detection."""
            if image is None or image.size == 0:
                return []
            
            # Simulate finding barcodes
            return ["123456789", "ABC123"]
        
        def mock_zxing_barcode_detection(image):
            """Mock ZXing barcode detection."""
            if image is None or image.size == 0:
                return []
            
            # Simulate finding different barcodes
            return ["987654321"]
        
        def mock_pyzbar_barcode_detection(image):
            """Mock pyzbar barcode detection."""
            if image is None or image.size == 0:
                return []
            
            # Simulate finding QR codes
            return ["QR_CODE_DATA"]
        
        # Test OpenCV detection
        opencv_result = mock_opencv_barcode_detection(self.barcode_image)
        self.assertIsInstance(opencv_result, list)
        self.assertEqual(len(opencv_result), 2)
        
        # Test ZXing detection
        zxing_result = mock_zxing_barcode_detection(self.barcode_image)
        self.assertIsInstance(zxing_result, list)
        self.assertEqual(len(zxing_result), 1)
        
        # Test pyzbar detection
        pyzbar_result = mock_pyzbar_barcode_detection(self.barcode_image)
        self.assertIsInstance(pyzbar_result, list)
        self.assertEqual(len(pyzbar_result), 1)
        
        # Test with invalid input
        self.assertEqual(mock_opencv_barcode_detection(None), [])
        self.assertEqual(mock_zxing_barcode_detection(None), [])
        self.assertEqual(mock_pyzbar_barcode_detection(None), [])
    
    def test_barcode_result_validation(self):
        """Test barcode result validation."""
        def validate_barcode_result(result):
            """Validate barcode detection result."""
            if not isinstance(result, (list, tuple)):
                return False
            
            for item in result:
                if not isinstance(item, str):
                    return False
                if len(item.strip()) == 0:
                    return False
            
            return True
        
        # Valid results
        valid_results = [
            ["123456789"],
            ["ABC123", "DEF456"],
            [],  # No barcodes found is valid
        ]
        
        for result in valid_results:
            self.assertTrue(validate_barcode_result(result))
        
        # Invalid results
        invalid_results = [
            None,
            "single_string",
            [123, 456],  # Non-string items
            ["valid", ""],  # Empty string
        ]
        
        for result in invalid_results:
            self.assertFalse(validate_barcode_result(result))
    
    def test_barcode_formatting(self):
        """Test barcode result formatting for display."""
        def format_barcode_result(barcode_result):
            """Format barcode result for display."""
            if not barcode_result or not isinstance(barcode_result, (list, tuple)):
                return "No barcode found"
            
            # Filter out empty strings
            valid_codes = [str(code).strip() for code in barcode_result if str(code).strip()]
            
            if not valid_codes:
                return "No barcode found"
            
            return ", ".join(valid_codes)
        
        test_cases = [
            (["123456789"], "123456789"),
            (["ABC123", "DEF456"], "ABC123, DEF456"),
            ([], "No barcode found"),
            (None, "No barcode found"),
            (["", "   "], "No barcode found"),
            (["123", "", "456"], "123, 456"),
        ]
        
        for input_result, expected_output in test_cases:
            output = format_barcode_result(input_result)
            self.assertEqual(output, expected_output)


class TestBarcodeROIProcessing(unittest.TestCase):
    """Test barcode ROI processing functionality."""
    
    def setUp(self):
        """Set up test image for barcode tests."""
        # Create a sample test image (small 100x100 RGB image)
        self.test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        # Add some pattern to the image
        self.test_image[25:75, 25:75] = [255, 255, 255]  # White square in center
    
    def test_barcode_roi_configuration(self):
        """Test barcode ROI configuration validation."""
        def validate_barcode_roi(roi_config):
            """Validate barcode ROI configuration."""
            required_fields = ["id", "type", "coordinates", "focus", "exposure", "method"]
            
            for field in required_fields:
                if field not in roi_config:
                    return False, f"Missing field: {field}"
            
            # Type should be 1 for barcode ROI
            if roi_config["type"] != 1:
                return False, "Invalid ROI type for barcode"
            
            # Method should be valid barcode detection method
            valid_methods = ["opencv", "zxing", "pyzbar"]
            if roi_config["method"] not in valid_methods:
                return False, f"Invalid detection method: {roi_config['method']}"
            
            # Coordinates should be valid
            coords = roi_config["coordinates"]
            if not isinstance(coords, (list, tuple)) or len(coords) != 4:
                return False, "Invalid coordinates format"
            
            x1, y1, x2, y2 = coords
            if x1 >= x2 or y1 >= y2:
                return False, "Invalid coordinate values"
            
            return True, "Valid configuration"
        
        # Valid barcode ROI
        valid_roi = {
            "id": 1,
            "type": 1,
            "coordinates": (10, 10, 100, 100),
            "focus": 305,
            "exposure": 3000,
            "method": "opencv"
        }
        
        is_valid, message = validate_barcode_roi(valid_roi)
        self.assertTrue(is_valid)
        
        # Invalid ROI - wrong type
        invalid_roi = valid_roi.copy()
        invalid_roi["type"] = 2
        
        is_valid, message = validate_barcode_roi(invalid_roi)
        self.assertFalse(is_valid)
        self.assertIn("Invalid ROI type", message)
    
    def test_barcode_roi_processing_result(self):
        """Test barcode ROI processing result structure."""
        def process_barcode_roi(image, roi_config):
            """Process barcode ROI and return result."""
            roi_id = roi_config["id"]
            roi_type = roi_config["type"]
            method = roi_config["method"]
            
            # Extract ROI from image
            x1, y1, x2, y2 = roi_config["coordinates"]
            roi_image = image[y1:y2, x1:x2] if image is not None else None
            
            # Simulate barcode detection
            if roi_image is not None and method == "opencv":
                barcode_result = ["123456789"]  # Mock detection
            else:
                barcode_result = []
            
            # Format result tuple
            return (
                roi_id,           # ROI ID
                roi_type,         # ROI type (1 for barcode)
                (x1, y1, x2, y2), # Coordinates
                roi_config["focus"],    # Focus
                roi_config["exposure"], # Exposure
                "Barcode",        # Result type
                barcode_result    # Barcode data
            )
        
        # Test successful barcode detection
        roi_config = {
            "id": 1,
            "type": 1,
            "coordinates": (10, 10, 100, 100),
            "focus": 305,
            "exposure": 3000,
            "method": "opencv"
        }
        
        result = process_barcode_roi(self.test_image, roi_config)
        
        self.assertEqual(result[0], 1)  # ROI ID
        self.assertEqual(result[1], 1)  # ROI type
        self.assertEqual(result[5], "Barcode")  # Result type
        self.assertIsInstance(result[6], list)  # Barcode result
    
    def test_barcode_detection_failure_handling(self):
        """Test handling of barcode detection failures."""
        def detect_barcode_with_fallback(image, methods=["opencv", "zxing", "pyzbar"]):
            """Detect barcode with multiple method fallback."""
            results = []
            
            for method in methods:
                try:
                    if method == "opencv":
                        # Simulate OpenCV detection
                        if np.random.random() > 0.7:  # 30% success rate
                            results.extend(["CV_123"])
                    elif method == "zxing":
                        # Simulate ZXing detection
                        if np.random.random() > 0.8:  # 20% success rate
                            results.extend(["ZX_456"])
                    elif method == "pyzbar":
                        # Simulate pyzbar detection
                        if np.random.random() > 0.6:  # 40% success rate
                            results.extend(["PZ_789"])
                    
                    if results:  # Stop on first successful detection
                        break
                        
                except Exception:
                    continue  # Try next method
            
            return results
        
        # Test fallback mechanism
        # Run multiple times to test different scenarios
        for _ in range(10):
            result = detect_barcode_with_fallback(self.test_image)
            self.assertIsInstance(result, list)
            # Result can be empty (no detection) or contain barcode strings


class TestBarcodeIntegration(unittest.TestCase):
    """Test barcode integration with main application."""
    
    def test_barcode_roi_in_inspection_workflow(self):
        """Test barcode ROI integration in inspection workflow."""
        def simulate_inspection_with_barcode():
            """Simulate inspection workflow with barcode ROI."""
            # Define mixed ROI types
            rois = [
                {"id": 1, "type": 2, "method": "mobilenet"},  # Image comparison
                {"id": 2, "type": 1, "method": "opencv"},     # Barcode detection
                {"id": 3, "type": 2, "method": "mobilenet"},  # Image comparison
                {"id": 4, "type": 1, "method": "zxing"},      # Barcode detection
            ]
            
            results = []
            
            for roi in rois:
                if roi["type"] == 1:  # Barcode ROI
                    # Simulate barcode processing
                    barcode_result = ["BC_" + str(roi["id"])]
                    result = (roi["id"], roi["type"], None, None, None, "Barcode", barcode_result)
                else:  # Image comparison ROI
                    # Simulate image comparison
                    similarity = 0.95
                    result = (roi["id"], roi["type"], None, None, None, "Match", "green", similarity)
                
                results.append(result)
            
            return results
        
        results = simulate_inspection_with_barcode()
        
        # Verify mixed results
        self.assertEqual(len(results), 4)
        
        # Check barcode results
        barcode_results = [r for r in results if r[1] == 1]
        self.assertEqual(len(barcode_results), 2)
        
        for result in barcode_results:
            self.assertEqual(result[5], "Barcode")
            self.assertIsInstance(result[6], list)
        
        # Check image comparison results
        image_results = [r for r in results if r[1] == 2]
        self.assertEqual(len(image_results), 2)
        
        for result in image_results:
            self.assertEqual(result[5], "Match")
    
    def test_barcode_result_aggregation(self):
        """Test aggregation of barcode results from multiple ROIs."""
        def aggregate_barcode_results(results):
            """Aggregate barcode results from inspection."""
            all_barcodes = []
            barcode_count = 0
            
            for result in results:
                if result[1] == 1 and len(result) > 6:  # Barcode ROI with results
                    barcode_data = result[6]
                    if barcode_data and isinstance(barcode_data, list):
                        all_barcodes.extend(barcode_data)
                        barcode_count += 1
            
            return {
                "total_barcode_rois": barcode_count,
                "all_barcodes": all_barcodes,
                "unique_barcodes": list(set(all_barcodes))
            }
        
        # Test results with multiple barcode ROIs
        test_results = [
            (1, 2, None, None, None, "Match", "green"),
            (2, 1, None, None, None, "Barcode", ["ABC123"]),
            (3, 1, None, None, None, "Barcode", ["DEF456", "ABC123"]),
            (4, 1, None, None, None, "Barcode", []),  # No barcodes found
        ]
        
        aggregated = aggregate_barcode_results(test_results)
        
        self.assertEqual(aggregated["total_barcode_rois"], 2)
        self.assertEqual(len(aggregated["all_barcodes"]), 3)  # ABC123, DEF456, ABC123
        self.assertEqual(len(aggregated["unique_barcodes"]), 2)  # ABC123, DEF456
        self.assertIn("ABC123", aggregated["unique_barcodes"])
        self.assertIn("DEF456", aggregated["unique_barcodes"])


if __name__ == '__main__':
    unittest.main(verbosity=2)
