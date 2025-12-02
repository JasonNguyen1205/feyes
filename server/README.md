# Visual AOI Server

RESTful API server for Visual AOI (Automated Optical Inspection) system. This server handles all inspection processing logic including AI/ML inference, barcode reading, and OCR.

## ⚠️ CRITICAL DOCUMENTATION - READ BEFORE CODE CHANGES

**Before making ANY code changes, you MUST read:**

1. **[PROJECT_INSTRUCTIONS.md](docs/PROJECT_INSTRUCTIONS.md)** - Contains current application logic that must be preserved
2. **[ROI_DEFINITION_SPECIFICATION.md](docs/ROI_DEFINITION_SPECIFICATION.md)** - Official ROI structure format
3. **[INSPECTION_RESULT_SPECIFICATION.md](docs/INSPECTION_RESULT_SPECIFICATION.md)** - Official result structure format
4. **[CHANGE_MANAGEMENT_GUIDELINES.md](docs/CHANGE_MANAGEMENT_GUIDELINES.md)** - Safe modification procedures

**⚠️ WARNING:** Modifying code without understanding these critical logic rules will break the application!

**Update Requirements:**

- When logic changes → Update PROJECT_INSTRUCTIONS.md
- When ROI structure changes → Update ROI_DEFINITION_SPECIFICATION.md
- When result structure changes → Update INSPECTION_RESULT_SPECIFICATION.md
- When making changes → Follow CHANGE_MANAGEMENT_GUIDELINES.md

## Overview

The Visual AOI Server is the central processing hub in a distributed client-server architecture. It receives images from client applications via REST API and performs comprehensive quality inspection using multiple techniques:

- **AI-based image comparison** (MobileNet, PyTorch)
- **Barcode detection and reading** (Dynamsoft)
- **Barcode linking and validation** (External API integration)
- **Optical Character Recognition** (EasyOCR)
- **Multi-device inspection** (1-4 devices simultaneously)

## Architecture

- **Flask REST API** with JSON responses
- **Session-based workflow** with UUID tracking
- **Base64 image encoding** for transmission
- **Multi-threaded processing** for performance
- **Configurable inspection rules** per product

## Quick Start

### Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Development mode with debug logging
python server/simple_api_server.py --debug --host 0.0.0.0 --port 5000

# Production mode
python server/simple_api_server.py --host 0.0.0.0 --port 5000
```

## API Endpoints

### Health & Status

- `GET /api/health` - Server health check
- `GET /api/status` - Detailed server status
- `POST /api/initialize` - Initialize AI models

### Product Management

- `GET /api/products` - List available products

### Session Management

- `POST /api/session/create` - Create inspection session
- `GET /api/session/{id}/status` - Get session info
- `POST /api/session/{id}/close` - Close session
- `GET /api/sessions` - List active sessions

### Inspection Processing

- `POST /api/session/{id}/inspect` - Run inspection on image

## Configuration

Product configs: `config/products/{product_id}/rois_config_{product_id}.json`

ROI format (11-field): `(idx, type, coords, focus, exposure, ai_threshold, feature_method, rotation, device_location, expected_text, is_device_barcode)`

## Schema API Endpoints

Programmatic access to structure specifications:

- **`GET /api/schema/roi`** - ROI structure specification (v3.0, 11-field format)
- **`GET /api/schema/result`** - Inspection result structure specification
- **`GET /api/schema/version`** - Version information and change history

**Documentation:** See [SCHEMA_API_ENDPOINTS.md](docs/SCHEMA_API_ENDPOINTS.md) for usage examples and integration guide.

**Benefits:**

- Automatic client adaptation to structure changes
- Programmatic validation of configurations
- Version compatibility checking
- Dynamic UI generation from schema
- Easier system integration

## API Documentation

### Swagger/OpenAPI Documentation

Interactive API documentation is available via Swagger UI:

- **Swagger UI (Local):** <http://localhost:5000/apidocs/>
- **Swagger UI (Network):** <http://10.100.27.156:5000/apidocs/>
- **OpenAPI Spec (JSON):** <http://localhost:5000/apispec_1.json>

**Features:**

- Browse all API endpoints
- View request/response schemas
- Test endpoints directly from browser
- Download OpenAPI specification
- Generate client code
- Dynamic hostname (works for local and external access)

**Documentation:** See [SWAGGER_DOCUMENTATION.md](docs/SWAGGER_DOCUMENTATION.md) for details.

**Verification:**

```bash
# Verify Swagger is working
./verify_swagger.sh
```

## Shared Folder Configuration

### File Exchange Architecture

The server uses a shared folder for client-server file exchange:

- **Type:** CIFS/SMB Network Share
- **Server Path:** `/home/jason_nguyen/visual-aoi-server/shared/` (absolute path used in code)
- **Client Mount:** `/mnt/visual-aoi-shared/` (CIFS network mount)
- **Note:** Both paths point to the same physical directory (verified by inode)
- **Structure:** `sessions/<uuid>/input/` and `sessions/<uuid>/output/`

**Workflow:**

1. Client writes captured images to `sessions/<uuid>/input/`
2. Client calls API with session ID
3. Server reads from input folder (using absolute local path)
4. Server processes (AI, barcode, OCR)
5. Server writes ROI/golden images to `sessions/<uuid>/output/`
6. Client reads results from output folder (via CIFS mount)

**Documentation:** See [SHARED_FOLDER_CONFIGURATION.md](docs/SHARED_FOLDER_CONFIGURATION.md) for details.

## Testing

```bash
pytest tests/
```

## License

MIT License

---
**Version**: 1.0 (October 2025) | **Python**: 3.8+
