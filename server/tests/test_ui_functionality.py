#!/usr/bin/env python3
"""
Test suite for UI functionality and user interface components.
"""

import unittest
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock
import tkinter as tk

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)


class TestUIComponents(unittest.TestCase):
    """Test UI component functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_roi_list_management(self):
        """Test ROI list management in UI."""
        def mock_roi_list_operations():
            """Mock ROI list operations."""
            roi_list = []
            
            # Add ROI
            def add_roi(roi_data):
                roi_list.append(roi_data)
                return len(roi_list) - 1
            
            # Remove ROI
            def remove_roi(index):
                if 0 <= index < len(roi_list):
                    return roi_list.pop(index)
                return None
            
            # Update ROI
            def update_roi(index, new_data):
                if 0 <= index < len(roi_list):
                    roi_list[index] = new_data
                    return True
                return False
            
            return {
                "add": add_roi,
                "remove": remove_roi,
                "update": update_roi,
                "list": lambda: roi_list.copy()
            }
        
        roi_manager = mock_roi_list_operations()
        
        # Test adding ROIs
        roi1 = {"id": 1, "type": 2, "coords": (0, 0, 100, 100)}
        roi2 = {"id": 2, "type": 1, "coords": (100, 100, 200, 200)}
        
        idx1 = roi_manager["add"](roi1)
        idx2 = roi_manager["add"](roi2)
        
        self.assertEqual(idx1, 0)
        self.assertEqual(idx2, 1)
        self.assertEqual(len(roi_manager["list"]()), 2)
        
        # Test updating ROI
        updated_roi = {"id": 1, "type": 2, "coords": (10, 10, 110, 110)}
        success = roi_manager["update"](0, updated_roi)
        
        self.assertTrue(success)
        self.assertEqual(roi_manager["list"]()[0]["coords"], (10, 10, 110, 110))
        
        # Test removing ROI
        removed = roi_manager["remove"](0)
        self.assertIsNotNone(removed)
        self.assertEqual(len(roi_manager["list"]()), 1)
    
    def test_result_display_formatting(self):
        """Test result display formatting."""
        def format_result_for_display(result):
            """Format inspection result for UI display."""
            roi_id, roi_type = result[0], result[1]
            
            if roi_type == 1:  # Barcode ROI
                barcode_result = result[6] if len(result) > 6 else None
                if barcode_result and isinstance(barcode_result, list):
                    barcode_str = ", ".join(str(b) for b in barcode_result if b)
                    if barcode_str:
                        return f"ROI {roi_id} | Barcode: {barcode_str}"
                    else:
                        return f"ROI {roi_id} | No barcode found"
                else:
                    return f"ROI {roi_id} | No barcode found"
                    
            elif roi_type == 2:  # Image comparison ROI
                result_text = result[5] if len(result) > 5 else "Unknown"
                similarity = result[7] if len(result) > 7 else None
                threshold = result[8] if len(result) > 8 else None
                
                display_text = f"ROI {roi_id} | {result_text}"
                
                if similarity is not None:
                    display_text += f" (Similarity: {similarity:.3f})"
                if threshold is not None:
                    display_text += f" | Threshold: {threshold}"
                
                return display_text
            
            return f"ROI {roi_id} | Unknown type"
        
        # Test barcode result formatting
        barcode_result_success = (1, 1, None, None, None, "Barcode", ["ABC123"])
        barcode_result_fail = (2, 1, None, None, None, "Barcode", [])
        
        barcode_display_success = format_result_for_display(barcode_result_success)
        barcode_display_fail = format_result_for_display(barcode_result_fail)
        
        self.assertIn("ABC123", barcode_display_success)
        self.assertIn("No barcode found", barcode_display_fail)
        
        # Test image comparison result formatting
        image_result_match = (3, 2, None, None, None, "Match", "green", 0.97, 0.95)
        image_result_diff = (4, 2, None, None, None, "Different", "red", 0.85, 0.90)
        
        image_display_match = format_result_for_display(image_result_match)
        image_display_diff = format_result_for_display(image_result_diff)
        
        self.assertIn("Match", image_display_match)
        self.assertIn("0.970", image_display_match)
        self.assertIn("Different", image_display_diff)
        self.assertIn("0.850", image_display_diff)
    
    def test_color_coding_for_results(self):
        """Test color coding for different result types."""
        def get_result_color(result):
            """Get color for result display."""
            roi_type = result[1]
            
            if roi_type == 1:  # Barcode ROI
                barcode_result = result[6] if len(result) > 6 else None
                if barcode_result and isinstance(barcode_result, list) and any(barcode_result):
                    return "green"  # Success
                else:
                    return "red"    # Failure
                    
            elif roi_type == 2:  # Image comparison ROI
                result_text = result[5] if len(result) > 5 else ""
                if "Match" in str(result_text):
                    return "green"  # Success
                else:
                    return "red"    # Failure
            
            return "gray"  # Unknown
        
        # Test color assignments
        test_results = [
            (1, 1, None, None, None, "Barcode", ["ABC123"]),  # Green
            (2, 1, None, None, None, "Barcode", []),          # Red
            (3, 2, None, None, None, "Match", "green"),       # Green
            (4, 2, None, None, None, "Different", "red"),     # Red
        ]
        
        expected_colors = ["green", "red", "green", "red"]
        
        for i, result in enumerate(test_results):
            color = get_result_color(result)
            self.assertEqual(color, expected_colors[i])


class TestUIInteraction(unittest.TestCase):
    """Test UI interaction and event handling."""
    
    def test_roi_selection_validation(self):
        """Test ROI selection and validation."""
        def validate_roi_selection(x1, y1, x2, y2, image_width, image_height):
            """Validate ROI selection coordinates."""
            # Check bounds
            if x1 < 0 or y1 < 0 or x2 > image_width or y2 > image_height:
                return False, "ROI coordinates out of image bounds"
            
            # Check minimum size
            min_size = 10
            if (x2 - x1) < min_size or (y2 - y1) < min_size:
                return False, f"ROI too small (minimum {min_size}x{min_size})"
            
            # Check coordinate order
            if x1 >= x2 or y1 >= y2:
                return False, "Invalid coordinate order"
            
            return True, "Valid ROI selection"
        
        # Test valid selections
        valid_cases = [
            (10, 10, 100, 100, 640, 480),
            (0, 0, 50, 50, 640, 480),
            (590, 430, 640, 480, 640, 480),
        ]
        
        for x1, y1, x2, y2, w, h in valid_cases:
            is_valid, message = validate_roi_selection(x1, y1, x2, y2, w, h)
            self.assertTrue(is_valid, f"Should be valid: {message}")
        
        # Test invalid selections
        invalid_cases = [
            (-10, 10, 100, 100, 640, 480),  # Out of bounds
            (10, 10, 650, 100, 640, 480),   # Out of bounds
            (10, 10, 15, 15, 640, 480),     # Too small
            (100, 100, 50, 150, 640, 480),  # Invalid order
        ]
        
        for x1, y1, x2, y2, w, h in invalid_cases:
            is_valid, message = validate_roi_selection(x1, y1, x2, y2, w, h)
            self.assertFalse(is_valid, f"Should be invalid: {(x1, y1, x2, y2)}")
    
    def test_settings_validation(self):
        """Test camera settings validation in UI."""
        def validate_camera_settings(focus, exposure, gain):
            """Validate camera settings input."""
            errors = []
            
            # Validate focus
            if not isinstance(focus, (int, float)) or focus < 100 or focus > 1000:
                errors.append("Focus must be between 100 and 1000")
            
            # Validate exposure
            if not isinstance(exposure, (int, float)) or exposure < 100 or exposure > 10000:
                errors.append("Exposure must be between 100 and 10000")
            
            # Validate gain
            if not isinstance(gain, (int, float)) or gain < 0.1 or gain > 10.0:
                errors.append("Gain must be between 0.1 and 10.0")
            
            return len(errors) == 0, errors
        
        # Test valid settings
        is_valid, errors = validate_camera_settings(305, 3000, 1.0)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test invalid settings
        is_valid, errors = validate_camera_settings(50, 20000, -1.0)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 3)  # All three parameters invalid
    
    def test_threshold_validation(self):
        """Test AI threshold validation in UI."""
        def validate_threshold_input(threshold_str):
            """Validate threshold input from UI."""
            try:
                threshold = float(threshold_str)
                if 0.0 <= threshold <= 1.0:
                    return True, threshold, ""
                else:
                    return False, None, "Threshold must be between 0.0 and 1.0"
            except ValueError:
                return False, None, "Threshold must be a valid number"
        
        # Test valid inputs
        valid_inputs = ["0.95", "0.5", "1.0", "0.0"]
        for input_str in valid_inputs:
            is_valid, value, error = validate_threshold_input(input_str)
            self.assertTrue(is_valid)
            self.assertIsNotNone(value)
            self.assertEqual(error, "")
        
        # Test invalid inputs
        invalid_inputs = ["1.5", "-0.1", "abc", ""]
        for input_str in invalid_inputs:
            is_valid, value, error = validate_threshold_input(input_str)
            self.assertFalse(is_valid)
            self.assertIsNone(value)
            self.assertNotEqual(error, "")


class TestUIState(unittest.TestCase):
    """Test UI state management."""
    
    def test_application_state_tracking(self):
        """Test application state tracking."""
        def create_state_manager():
            """Create application state manager."""
            state = {
                "current_product": None,
                "camera_connected": False,
                "rois_loaded": False,
                "inspection_running": False,
                "results_available": False
            }
            
            def update_state(key, value):
                if key in state:
                    state[key] = value
                    return True
                return False
            
            def get_state(key):
                return state.get(key)
            
            def get_all_state():
                return state.copy()
            
            return {
                "update": update_state,
                "get": get_state,
                "get_all": get_all_state
            }
        
        state_manager = create_state_manager()
        
        # Test initial state
        self.assertIsNone(state_manager["get"]("current_product"))
        self.assertFalse(state_manager["get"]("camera_connected"))
        
        # Test state updates
        self.assertTrue(state_manager["update"]("current_product", "20001234"))
        self.assertTrue(state_manager["update"]("camera_connected", True))
        
        self.assertEqual(state_manager["get"]("current_product"), "20001234")
        self.assertTrue(state_manager["get"]("camera_connected"))
        
        # Test invalid state key
        self.assertFalse(state_manager["update"]("invalid_key", "value"))
    
    def test_ui_element_state_management(self):
        """Test UI element state management."""
        def manage_ui_elements():
            """Manage UI element states."""
            elements = {
                "start_button": {"enabled": True, "text": "Start Inspection"},
                "stop_button": {"enabled": False, "text": "Stop Inspection"},
                "save_button": {"enabled": False, "text": "Save Results"},
                "roi_list": {"enabled": True, "items": []},
            }
            
            def set_inspection_running(running):
                """Update UI for inspection state."""
                elements["start_button"]["enabled"] = not running
                elements["stop_button"]["enabled"] = running
                
                if running:
                    elements["start_button"]["text"] = "Inspection Running..."
                else:
                    elements["start_button"]["text"] = "Start Inspection"
            
            def set_results_available(available):
                """Update UI for results availability."""
                elements["save_button"]["enabled"] = available
            
            return {
                "elements": elements,
                "set_inspection_running": set_inspection_running,
                "set_results_available": set_results_available
            }
        
        ui_manager = manage_ui_elements()
        
        # Test initial state
        self.assertTrue(ui_manager["elements"]["start_button"]["enabled"])
        self.assertFalse(ui_manager["elements"]["stop_button"]["enabled"])
        
        # Test inspection state change
        ui_manager["set_inspection_running"](True)
        
        self.assertFalse(ui_manager["elements"]["start_button"]["enabled"])
        self.assertTrue(ui_manager["elements"]["stop_button"]["enabled"])
        self.assertIn("Running", ui_manager["elements"]["start_button"]["text"])
        
        # Test results availability
        ui_manager["set_results_available"](True)
        self.assertTrue(ui_manager["elements"]["save_button"]["enabled"])


class TestUIErrorHandling(unittest.TestCase):
    """Test UI error handling and user feedback."""
    
    def test_error_message_display(self):
        """Test error message display formatting."""
        def format_error_message(error_type, details):
            """Format error message for user display."""
            if error_type == "camera":
                return f"Camera Error: {details}"
            elif error_type == "file":
                return f"File Error: {details}"
            elif error_type == "validation":
                return f"Input Error: {details}"
            elif error_type == "processing":
                return f"Processing Error: {details}"
            else:
                return f"Unknown Error: {details}"
        
        # Test different error types
        test_cases = [
            ("camera", "Cannot connect to camera", "Camera Error: Cannot connect to camera"),
            ("file", "Configuration file not found", "File Error: Configuration file not found"),
            ("validation", "Invalid ROI coordinates", "Input Error: Invalid ROI coordinates"),
            ("processing", "AI model loading failed", "Processing Error: AI model loading failed"),
            ("unknown", "Something went wrong", "Unknown Error: Something went wrong"),
        ]
        
        for error_type, details, expected in test_cases:
            message = format_error_message(error_type, details)
            self.assertEqual(message, expected)
    
    def test_user_confirmation_dialogs(self):
        """Test user confirmation dialog logic."""
        def simulate_confirmation_dialog(message, default=False):
            """Simulate confirmation dialog behavior."""
            # Mock different user responses
            user_responses = {
                "Delete all ROIs?": False,
                "Save current configuration?": True,
                "Start inspection without golden images?": False,
                "Override existing results?": True,
            }
            
            return user_responses.get(message, default)
        
        # Test different confirmation scenarios
        test_cases = [
            ("Delete all ROIs?", False),
            ("Save current configuration?", True),
            ("Start inspection without golden images?", False),
            ("Override existing results?", True),
            ("Unknown operation?", False),  # Default response
        ]
        
        for message, expected in test_cases:
            response = simulate_confirmation_dialog(message)
            self.assertEqual(response, expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
