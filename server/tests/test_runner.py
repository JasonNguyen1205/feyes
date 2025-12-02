"""
Test runner configuration and utilities.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add src directory to Python path for testing
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Verify src path is added to Python path
if str(src_path) not in sys.path:
    raise ImportError(f"src path {src_path} not found in sys.path")


class TestLoader:
    """Custom test loader for the Visual AOI project."""
    
    @staticmethod
    def discover_tests(test_dir=None):
        """Discover and load all tests."""
        if test_dir is None:
            test_dir = Path(__file__).parent
        
        loader = unittest.TestLoader()
        suite = loader.discover(str(test_dir), pattern='test_*.py')
        return suite
    
    @staticmethod
    def run_tests(verbosity=2):
        """Run all tests with specified verbosity."""
        suite = TestLoader.discover_tests()
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        return result


class TestConfig:
    """Test configuration and utilities."""
    
    # Test data directories
    TEST_DATA_DIR = Path(__file__).parent / "test_data"
    TEMP_DIR = Path(__file__).parent / "temp"
    
    # Mock dependencies flag
    MOCK_DEPENDENCIES = True
    
    @classmethod
    def setup_test_environment(cls):
        """Set up the test environment."""
        # Create test directories if they don't exist
        cls.TEST_DATA_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)
        
        # Set environment variables for testing
        os.environ['TESTING'] = '1'
        os.environ['TEST_MODE'] = 'unit'
    
    @classmethod
    def teardown_test_environment(cls):
        """Clean up the test environment."""
        # Remove test environment variables
        os.environ.pop('TESTING', None)
        os.environ.pop('TEST_MODE', None)
        
        # Clean up temporary files
        import shutil
        if cls.TEMP_DIR.exists():
            shutil.rmtree(cls.TEMP_DIR)


def create_test_image(width=100, height=100, channels=3):
    """Create a test image for testing purposes."""
    import numpy as np
    return np.random.randint(0, 255, (height, width, channels), dtype=np.uint8)


def create_test_roi():
    """Create a test ROI for testing purposes."""
    return (1, 2, (50, 50, 150, 150), 305, 3000, 0.9, "mobilenet")


def skip_if_module_missing(module_name):
    """Decorator to skip tests if a module is missing."""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            try:
                __import__(module_name)
                return test_func(*args, **kwargs)
            except ImportError:
                import unittest
                raise unittest.SkipTest(f"Module {module_name} not available")
        return wrapper
    return decorator


def mock_opencv_if_missing():
    """Mock OpenCV if it's not available."""
    try:
        import cv2
        return cv2
    except ImportError:
        from unittest.mock import MagicMock
        cv2 = MagicMock()
        cv2.SIFT_create = MagicMock()
        cv2.ORB_create = MagicMock()
        cv2.BFMatcher = MagicMock()
        cv2.COLOR_BGR2GRAY = 6
        cv2.COLOR_BGRA2BGR = 1
        cv2.COLOR_BGR2LAB = 44
        cv2.COLOR_LAB2BGR = 56
        return cv2


def mock_camera_if_missing():
    """Mock camera (TIS) if it's not available."""
    try:
        # Try to import TIS from src
        from src import get_tis_module
        TIS = get_tis_module()
        if TIS is None:
            raise ImportError("TIS module not available")
        return TIS.TIS
    except ImportError:
        # Mock TIS module
        from unittest.mock import MagicMock
        TIS = MagicMock()
        TIS.SinkFormats = MagicMock()
        TIS.SinkFormats.BGRA = "BGRA"
        return TIS


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        TestConfig.setup_test_environment()
        self.test_image = create_test_image()
        self.test_roi = create_test_roi()
    
    def tearDown(self):
        """Clean up test fixtures."""
        TestConfig.teardown_test_environment()
    
    def assertImageValid(self, image):
        """Assert that an image is valid."""
        import numpy as np
        self.assertIsInstance(image, np.ndarray)
        self.assertGreaterEqual(len(image.shape), 2)
        self.assertLessEqual(len(image.shape), 3)
    
    def assertROIValid(self, roi):
        """Assert that an ROI is valid."""
        self.assertIsInstance(roi, tuple)
        self.assertGreaterEqual(len(roi), 3)
        
        # Check coordinates
        if len(roi) >= 3:
            x, y, w, h = roi[2]
            self.assertIsInstance(x, int)
            self.assertIsInstance(y, int)
            self.assertIsInstance(w, int)
            self.assertIsInstance(h, int)


if __name__ == '__main__':
    # Run tests when this file is executed directly
    print("Setting up test environment...")
    TestConfig.setup_test_environment()
    
    print("Discovering and running tests...")
    result = TestLoader.run_tests()
    
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Clean up
    TestConfig.teardown_test_environment()
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
