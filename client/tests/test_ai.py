"""
Unit tests for AI module (TensorFlow functionality removed).
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestAIFeatureMatching(unittest.TestCase):
    """Test AI feature matching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test images
        self.test_image1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.test_image2 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.grayscale_image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    
    @patch('ai.cv2')
    def test_sift_feature_extraction(self, mock_cv2):
        """Test SIFT feature extraction."""
        try:
            from ai import extract_sift_features
            
            # Mock SIFT detector and features
            mock_sift = MagicMock()
            mock_cv2.SIFT_create.return_value = mock_sift
            mock_keypoints = [MagicMock(), MagicMock()]
            mock_descriptors = np.random.rand(100, 128).astype(np.float32)
            mock_sift.detectAndCompute.return_value = (mock_keypoints, mock_descriptors)
            
            keypoints, descriptors = extract_sift_features(self.grayscale_image)
            
            # Verify SIFT was used
            mock_cv2.SIFT_create.assert_called_once()
            mock_sift.detectAndCompute.assert_called_once_with(self.grayscale_image, None)
            
            self.assertEqual(keypoints, mock_keypoints)
            self.assertEqual(descriptors.shape, (100, 128))
            
        except ImportError as e:
            self.skipTest(f"AI module not available: {e}")
    
    def test_mobilenet_functionality_removed(self):
        """Test that TensorFlow/MobileNet functionality was properly removed."""
        try:
            import ai
            # These should not exist after TensorFlow removal
            self.assertFalse(hasattr(ai, 'tf'))
            self.assertFalse(hasattr(ai, 'load_mobilenet_model'))
            
        except ImportError as e:
            self.skipTest(f"AI module not available: {e}")


class TestAIImageProcessing(unittest.TestCase):
    """Test AI image processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    def test_normalize_illumination(self):
        """Test illumination normalization."""
        try:
            from ai import normalize_illumination
            
            # Test with sample image
            result = normalize_illumination(self.test_image)
            
            # Should return same shape
            self.assertEqual(result.shape, self.test_image.shape)
            # Result should be numpy array
            self.assertIsInstance(result, np.ndarray)
            
        except ImportError as e:
            self.skipTest(f"AI module not available: {e}")


if __name__ == '__main__':
    unittest.main()
