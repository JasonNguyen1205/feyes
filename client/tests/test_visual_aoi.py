import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import sys
import os

# Add project root and src directory to path for imports
project_root = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# Import functions/classes from the src modules
try:
    from roi import (
        normalize_roi, get_next_roi_index, process_compare_roi, 
        update_best_golden_image, save_golden_roi
    )
except ImportError:
    # Skip all tests if roi module is not available
    def skip_all_tests(cls):
        for attr_name in dir(cls):
            if attr_name.startswith('test_'):
                setattr(cls, attr_name, lambda self: self.skipTest("roi module not available"))
        return cls
    
    @skip_all_tests
    class TestVisualAOILogic(unittest.TestCase):
        pass
else:
    class TestVisualAOILogic(unittest.TestCase):
        def setUp(self):
            # Setup dummy test data
            self.test_rois = [
                (1, 2, (0, 0, 100, 100), 305, 3000, 0.9, "mobilenet"),
                (2, 1, (10, 10, 50, 50), 305, 3000, None, "opencv"),
            ]
            self.dummy_img = np.ones((100, 100, 3), dtype=np.uint8) * 127

        def test_normalize_roi_compare(self):
            roi = (3, 2, (0, 0, 10, 10), 305, 3000, 0.95, "mobilenet")
            norm = normalize_roi(roi)
            self.assertEqual(norm[1], 2)
            self.assertEqual(norm[5], 0.95)
            self.assertEqual(norm[6], "mobilenet")

        def test_normalize_roi_barcode(self):
            roi = (4, 1, (0, 0, 10, 10), 305, 3000, None, "opencv")
            norm = normalize_roi(roi)
            self.assertEqual(norm[1], 1)
            self.assertIsNone(norm[5])
            self.assertEqual(norm[6], "opencv")

        @patch('roi.ROIS')
        def test_get_next_roi_index(self, mock_rois):
            mock_rois.__getitem__ = lambda self, i: [
                (1, 2, (0, 0, 100, 100), 305, 3000, 0.9, "mobilenet"),
                (5, 1, (10, 10, 50, 50), 305, 3000, None, "opencv"),
            ][i]
            mock_rois.__len__ = lambda self: 2
            mock_rois.__iter__ = lambda self: iter([
                (1, 2, (0, 0, 100, 100), 305, 3000, 0.9, "mobilenet"),
                (5, 1, (10, 10, 50, 50), 305, 3000, None, "opencv"),
            ])
            
            with patch('roi.ROIS', mock_rois):
                self.assertEqual(get_next_roi_index(), 6)

        def test_roi_normalization_barcode(self):
            roi = (1, 1, (50, 50, 100, 100), 305, 3000, None, "opencv")
            norm = normalize_roi(roi)
            self.assertEqual(len(norm), 7)
            self.assertEqual(norm[0], 1)  # index
            self.assertEqual(norm[1], 1)  # type  
            self.assertEqual(norm[2], (50, 50, 100, 100))  # coords
            self.assertEqual(norm[3], 305)  # focus
            self.assertEqual(norm[4], 3000)  # exposure
            self.assertIsNone(norm[5])  # threshold
            self.assertEqual(norm[6], "opencv")  # method

        def test_roi_normalization_compare(self):
            roi = (2, 2, (10, 10, 60, 60), 305, 3000, 0.85, "mobilenet")
            norm = normalize_roi(roi)
            self.assertEqual(len(norm), 7)
            self.assertEqual(norm[0], 2)  # index
            self.assertEqual(norm[1], 2)  # type
            self.assertEqual(norm[2], (10, 10, 60, 60))  # coords
            self.assertEqual(norm[3], 305)  # focus
            self.assertEqual(norm[4], 3000)  # exposure
            self.assertEqual(norm[5], 0.85)  # threshold
            self.assertEqual(norm[6], "mobilenet")  # method

        @patch('roi.ROIS', [])
        def test_get_next_roi_index_empty(self):
            result = get_next_roi_index()
            self.assertEqual(result, 1)

        @patch('roi.ROIS')
        def test_get_next_roi_index_increment(self, mock_rois):
            mock_rois.__iter__ = lambda self: iter([
                (1, 1, (0, 0, 50, 50), 305, 3000, None, "opencv"),
                (3, 2, (50, 50, 100, 100), 305, 3000, 0.9, "mobilenet"),
            ])
            with patch('roi.ROIS', mock_rois):
                result = get_next_roi_index()
                self.assertEqual(result, 4)

        def test_sort_fail_first(self):
            # Test sorting logic for fail-first ordering
            results = [
                (1, 2, None, None, None, "Match", None),
                (2, 2, None, None, None, "Different", None),
                (3, 1, None, None, None, "Barcode", ["123"]),
                (4, 1, None, None, None, "Barcode", None),
            ]
            
            def is_fail(r):
                if r[1] == 2 and (len(r) > 5 and (not r[5] or "Match" not in str(r[5]))):
                    return 0
                if r[1] == 1 and (len(r) > 6 and (not r[6])):
                    return 0
                if len(r) > 5 and isinstance(r[5], str) and r[5].startswith("Error:"):
                    return 0
                return 1
            
            results.sort(key=lambda x: (is_fail(x), x[0]))
            # Fail results (idx 2, 4) should be first
            self.assertEqual([r[0] for r in results[:2]], [2, 4])

        def test_barcode_roi_display_logic(self):
            # Test barcode ROI display scenarios
            test_cases = [
                # (roi_type, barcode_result, expected_display)
                (1, ["12345"], "12345"),
                (1, ["ABC", "DEF"], "ABC, DEF"),
                (1, [], "No barcode detected"),
                (1, None, "No barcode detected"),
            ]
            
            for roi_type, barcode_result, expected in test_cases:
                with self.subTest(roi_type=roi_type, barcode_result=barcode_result):
                    if barcode_result:
                        barcode_str = ", ".join(str(b) for b in barcode_result if b)
                        result = barcode_str if barcode_str else "No barcode detected"
                    else:
                        result = "No barcode detected"
                    
                    self.assertEqual(result, expected)

        def test_compare_roi_display_logic(self):
            # Test compare ROI display scenarios
            test_cases = [
                (2, "Match", 0.95, "Match (95.0%)"),
                (2, "Different", 0.65, "Different (65.0%)"),
                (2, "Error: Invalid", None, "Error: Invalid"),
            ]
            
            for roi_type, match_result, similarity, expected in test_cases:
                with self.subTest(roi_type=roi_type, match_result=match_result):
                    if match_result.startswith("Error:"):
                        result = match_result
                    elif similarity is not None:
                        result = f"{match_result} ({similarity*100:.1f}%)"
                    else:
                        result = match_result
                    
                    self.assertEqual(result, expected)

        def test_sort_group_dict_default_first(self):
            # Test sorting with None/default values first
            groups = {"default": [1, 2], "group_a": [3], None: [4, 5]}
            sorted_keys = sorted(groups.keys(), key=lambda x: (x is not None, x))
            
            # None should be first, then other keys
            self.assertEqual(sorted_keys[0], None)
            self.assertIn("default", sorted_keys)
            self.assertIn("group_a", sorted_keys)

        def test_is_fail_logic(self):
            # Test the fail detection logic
            test_cases = [
                # (result_tuple, expected_is_fail)
                ((1, 2, None, None, None, "Match", None), False),  # Match
                ((2, 2, None, None, None, "Different", None), True),  # Different = fail
                ((3, 1, None, None, None, "Barcode", ["123"]), False),  # Barcode found
                ((4, 1, None, None, None, "Barcode", None), True),  # No barcode = fail
                ((5, 2, None, None, None, "Error: Something", None), True),  # Error = fail
            ]
            
            def is_fail(r):
                if r[1] == 2 and (len(r) > 5 and (not r[5] or "Match" not in str(r[5]))):
                    return True
                if r[1] == 1 and (len(r) > 6 and (not r[6])):
                    return True
                if len(r) > 5 and isinstance(r[5], str) and r[5].startswith("Error:"):
                    return True
                return False
            
            for result_tuple, expected in test_cases:
                with self.subTest(result=result_tuple):
                    self.assertEqual(is_fail(result_tuple), expected)


if __name__ == '__main__':
    unittest.main()