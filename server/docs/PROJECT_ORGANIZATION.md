# Project Organization Guide

## 📁 Directory Structure Overview

This document explains the organized structure of the Visual AOI project after cleanup.

### Root Level Files
```
visual-aoi/
├── main.py                    # 🚀 Main application entry point
├── README.md                  # 📖 Project overview and usage guide
├── LICENSE                    # ⚖️ Project license
├── requirements.txt           # 📦 Python dependencies
├── test-requirements.txt      # 🧪 Testing dependencies
├── pytest.ini                # ⚙️ Test configuration
└── .gitignore                 # 🚫 Git ignore patterns
```

### Core Application (`src/`)
The main application code is organized in the `src/` directory:

```
src/
├── __init__.py               # Package initialization
├── main modules:
│   ├── inspection.py         # 🎯 Main inspection coordination
│   ├── camera.py             # 📷 TIS camera integration
│   ├── ui.py                 # 🖥️ Tkinter GUI interface
│   └── config.py             # ⚙️ Configuration management
├── processing modules:
│   ├── ai.py                 # 🤖 AI/ML functionality (MobileNet)
│   ├── barcode.py            # 🏷️ Barcode detection (Dynamsoft)
│   ├── ocr.py                # 📝 Optical Character Recognition
│   └── roi.py                # 🎯 Region of Interest management
├── support modules:
│   ├── TIS.py                # 📡 TIS camera SDK wrapper
│   └── utils.py              # 🛠️ Utility functions
```

### Testing (`tests/`)
Comprehensive test suite for all modules:

```
tests/
├── README.md                 # Testing documentation
├── __init__.py               # Test package initialization
├── unit tests:
│   ├── test_ai.py            # AI module tests
│   ├── test_barcode.py       # Barcode detection tests
│   ├── test_camera.py        # Camera integration tests
│   ├── test_config.py        # Configuration tests
│   ├── test_ocr.py           # OCR functionality tests
│   ├── test_roi.py           # ROI management tests
│   └── test_utils.py         # Utility function tests
├── integration tests:
│   ├── test_integration.py   # End-to-end tests
│   ├── test_camera_improvements.py  # Camera improvement tests
│   └── test_*.py             # Additional test modules
├── test_data/                # Test data files
│   └── sample files for testing
└── test_runner.py            # Test execution utilities
```

### Configuration (`config/`)
Product-specific configurations and settings:

```
config/
└── products/                 # Product configurations
    └── {product_id}/         # Individual product directories
        ├── rois_config_{product_id}.json    # ROI definitions
        ├── golden_rois/      # Reference images
        │   └── roi_{id}/     # Individual ROI references
        └── (runtime files)   # Generated during operation
```

### Documentation (`docs/`)
Project documentation and guides:

```
docs/
├── CAMERA_IMPROVEMENTS.md    # Camera system enhancements
├── REFACTORING_SUMMARY.md    # Development history
└── PROJECT_ORGANIZATION.md   # This file
```

### Examples and Samples (`examples/`, `sample_images/`)
Example code and test images:

```
examples/
├── ai-visual.py              # AI functionality examples
└── barcode_reader_sample.py  # Barcode detection examples

sample_images/
├── roi*.jpg                  # Sample ROI images for testing
└── test_capture.jpg          # Test capture image
```

### Utilities (`scripts/`)
Operational scripts and utilities:

```
scripts/
├── run_tests.sh              # Test execution script
└── start-aoi.sh              # Application startup script
```

### Archive (`archive/`)
Historical versions and deprecated code:

```
archive/
├── main_old.py               # Original monolithic version
└── main_new.py               # Intermediate refactored version
```

### SDK and Examples (`python/`)
TIS camera SDK examples and documentation:

```
python/
├── python-common/            # Common SDK utilities
├── Multiple-Cameras-Triggered/  # Multi-camera examples
├── Auto Focus On Push/       # Focus control examples
├── capture-sequence/         # Sequence capture examples
└── (other SDK examples)
```

## 🎯 Organization Principles

### 1. **Separation of Concerns**
- Core application logic in `src/`
- Tests isolated in `tests/`
- Documentation in `docs/`
- Examples separate from production code

### 2. **Modularity**
- Each module has a single responsibility
- Clear interfaces between components
- Independent testing of each module

### 3. **Configuration Management**
- External configuration files
- Product-specific settings
- Environment-specific parameters

### 4. **Clean Root Directory**
- Minimal files in root
- Clear entry point (`main.py`)
- Essential project files only

## 📝 File Naming Conventions

### Python Modules
- **snake_case** for all Python files
- **Descriptive names** indicating functionality
- **test_** prefix for test files

### Configuration Files
- **Product ID** in configuration file names
- **Descriptive suffixes** (e.g., `_config`, `_settings`)
- **JSON format** for structured configuration

### Documentation
- **UPPERCASE** for major documentation files
- **Descriptive names** with underscores
- **Markdown format** for documentation

## 🔧 Maintenance Guidelines

### Adding New Features
1. **Create module** in appropriate `src/` subdirectory
2. **Add configuration** options to `config.py`
3. **Write tests** in `tests/` directory
4. **Update documentation** in `docs/`
5. **Add examples** if applicable

### Organizing New Files
1. **Follow existing structure** patterns
2. **Use appropriate subdirectories**
3. **Update .gitignore** for new file types
4. **Document new organization** in this file

### Cleanup Checklist
- [ ] Remove unused files
- [ ] Clean up __pycache__ directories
- [ ] Organize imports in Python files
- [ ] Update documentation
- [ ] Review .gitignore patterns
- [ ] Archive old versions

## 🚀 Benefits of This Organization

### Development Benefits
- **Faster navigation** - clear structure
- **Easier debugging** - isolated components
- **Better testing** - organized test suite
- **Simplified maintenance** - logical grouping

### Deployment Benefits
- **Clean packaging** - only necessary files
- **Clear dependencies** - separated requirements
- **Easy configuration** - external settings
- **Reliable testing** - comprehensive test coverage

### Team Benefits
- **Clear onboarding** - documented structure
- **Consistent patterns** - standardized organization
- **Efficient collaboration** - logical file placement
- **Reduced confusion** - obvious file locations

---

This organization supports scalable development while maintaining clarity and simplicity for the Visual AOI system.
