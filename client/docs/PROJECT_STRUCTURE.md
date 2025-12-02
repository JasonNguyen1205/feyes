# Visual AOI Project Structure

## Directory Layout

```
visual-aoi/
├── src/                        # Core application modules
│   ├── __init__.py
│   ├── ai.py                   # AI processing module
│   ├── ai_pytorch.py           # PyTorch AI implementation
│   ├── barcode.py              # Barcode reading functionality
│   ├── camera.py               # Camera control and capture
│   ├── config.py               # Configuration management
│   ├── inspection.py           # Inspection logic
│   ├── ocr.py                  # OCR processing
│   ├── roi.py                  # Region of Interest management
│   ├── TIS.py                  # The Imaging Source camera interface
│   ├── ui.py                   # User interface components
│   └── utils.py                # Utility functions
├── tests/                      # All test files
│   ├── __init__.py
│   ├── test_*.py               # Unit and integration tests
│   └── test_data/              # Test data files
├── config/                     # Configuration files
│   ├── theme_settings.json
│   └── products/               # Product-specific configurations
├── docs/                       # Documentation
│   ├── README.md
│   ├── *.md                    # All documentation files
├── examples/                   # Example scripts and demos
├── scripts/                    # Build and utility scripts
├── sample_images/              # Sample images for testing
├── archive/                    # Archived old files
├── python/                     # Third-party Python examples
├── main.py                     # Main application entry point
├── requirements.txt            # Python dependencies
├── test-requirements.txt       # Test dependencies
├── pytest.ini                 # Pytest configuration
└── start_visual_aoi.sh         # Application launcher script
```

## Module Organization

### Core Modules (`src/`)
- **ai.py**: Main AI processing functionality
- **ai_pytorch.py**: PyTorch-specific AI implementations
- **barcode.py**: Barcode detection and reading
- **camera.py**: Camera control, capture, and configuration
- **config.py**: Application configuration management
- **inspection.py**: Main inspection workflow and logic
- **ocr.py**: Optical Character Recognition processing
- **roi.py**: Region of Interest definition and management
- **TIS.py**: The Imaging Source camera interface
- **ui.py**: User interface components and dialogs
- **utils.py**: Common utility functions

### Test Organization (`tests/`)
All tests are organized by functionality:
- **test_comprehensive_application.py**: End-to-end application tests
- **test_integration.py**: Integration tests between modules
- **test_*.py**: Unit tests for individual modules
- **test_data/**: Test images and configuration files

### Configuration (`config/`)
- **theme_settings.json**: UI theme configuration
- **products/**: Product-specific inspection configurations

### Documentation (`docs/`)
All documentation files including:
- Project README
- Feature implementation summaries
- Technical documentation
- Migration guides

## Dependencies

### Runtime Dependencies
See `requirements.txt` for full list including:
- OpenCV for image processing
- PyTorch for AI functionality
- EasyOCR for text recognition
- Various camera and GUI libraries

### Test Dependencies
See `test-requirements.txt` for testing frameworks and utilities.

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest tests/`
3. Start application: `python main.py` or `./start_visual_aoi.sh`

## Build and Development

Use scripts in `scripts/` directory for:
- Running tests: `scripts/run_tests.sh`
- Starting application: `scripts/start-aoi.sh`
