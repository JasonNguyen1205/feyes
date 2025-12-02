# Swagger/OpenAPI Documentation

**Date:** October 3, 2025  
**Status:** ✅ Active and Verified  
**Access URL:** http://localhost:5000/apidocs/

---

## 🎯 Overview

The Visual AOI Server includes comprehensive Swagger/OpenAPI documentation for all API endpoints, providing an interactive interface for exploring and testing the REST API.

---

## 📡 Access Points

### Swagger UI (Interactive Documentation)
- **URL:** http://localhost:5000/apidocs/
- **Description:** Interactive web interface for exploring and testing API endpoints
- **Features:**
  - View all available endpoints
  - See request/response schemas
  - Test endpoints directly from browser
  - View example requests and responses
  - Download OpenAPI specification

### OpenAPI Specification (JSON)
- **URL:** http://localhost:5000/apispec_1.json
- **Description:** Machine-readable OpenAPI 2.0 specification
- **Format:** JSON
- **Use Cases:**
  - Code generation
  - API client development
  - Integration testing
  - Documentation generation

---

## 🔧 Configuration

### Location
File: `server/simple_api_server.py`

### Swagger Configuration
```python
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}
```

### API Information
```python
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Visual AOI Server API",
        "description": "RESTful API server for Visual AOI inspection processing",
        "contact": {
            "responsibleOrganization": "Visual AOI Team",
            "responsibleDeveloper": "Development Team",
            "email": "support@visualaoi.com",
            "url": "https://visualaoi.com",
        },
        "termsOfService": "https://visualaoi.com/terms",
        "version": "1.0.0"
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http", "https"],
    "consumes": ["application/json"],
    "produces": ["application/json"]
}
```

---

## 📚 Documented Endpoints

### By Category

#### **Schema Endpoints** (New in v3.0)
- **GET /api/schema/roi** - ROI structure specification
- **GET /api/schema/result** - Inspection result structure specification
- **GET /api/schema/version** - Schema version information

#### **Inspection Endpoints**
- **POST /api/inspect** - Run inspection on uploaded image
- **POST /api/fast-capture** - Fast capture and inspection
- **GET /api/rois** - Get ROI configuration for product
- Various other inspection-related endpoints

#### **Product Management**
- **GET /api/products** - List available products
- **POST /api/products** - Create new product
- **DELETE /api/products/<name>** - Delete product
- Various product configuration endpoints

#### **Golden Sample Management**
- **POST /api/golden-sample/save** - Save golden sample image
- **DELETE /api/products/<name>/golden/<roi_id>** - Delete golden sample
- **POST /api/golden-sample/rename-folders** - Rename golden sample folders

#### **Session Management**
- **POST /api/initialize** - Initialize inspection session
- **GET /api/status** - Get server status
- **POST /api/cleanup** - Cleanup session resources

---

## 🎨 Swagger Documentation Format

### Endpoint Documentation Template

Each endpoint includes comprehensive documentation using YAML docstrings:

```python
@app.route('/api/endpoint', methods=['GET'])
def endpoint_function():
    """Endpoint title/summary.
    ---
    tags:
      - Category Name
    summary: Short description
    description: Detailed description of what the endpoint does
    parameters:
      - name: param_name
        in: query|path|body|formData
        type: string|integer|boolean|file
        required: true|false
        description: Parameter description
    responses:
      200:
        description: Success response description
        schema:
          type: object
          properties:
            field_name:
              type: string
              example: "example value"
      400:
        description: Error response description
    """
    # Implementation
```

### Example: Schema Endpoint Documentation

```python
@app.route('/api/schema/roi', methods=['GET'])
def get_roi_structure_schema():
    """Get ROI structure specification.
    ---
    tags:
      - Schema
    summary: Get ROI structure specification
    description: Returns the current ROI structure format, field definitions, and version information
    responses:
      200:
        description: ROI structure specification
        schema:
          type: object
          properties:
            version:
              type: string
              example: "3.0"
            format:
              type: string
              example: "11-field"
            updated:
              type: string
              format: date
            fields:
              type: array
            backward_compatible:
              type: array
            priority_logic:
              type: object
    """
```

---

## ✅ Verification

### Quick Verification Commands

```bash
# Test Swagger UI is accessible
curl -s http://localhost:5000/apidocs/ | grep -o "<title>.*</title>"
# Expected output: <title>Flasgger</title>

# Test OpenAPI spec is available
curl -s http://localhost:5000/apispec_1.json | jq '.info.title'
# Expected output: "Visual AOI Server API"

# List all documented endpoints
curl -s http://localhost:5000/apispec_1.json | jq '.paths | keys'

# Check schema endpoints are documented
curl -s http://localhost:5000/apispec_1.json | jq '.paths | keys | map(select(contains("schema")))'
# Expected output: ["/api/schema/result", "/api/schema/roi", "/api/schema/version"]

# View specific endpoint documentation
curl -s http://localhost:5000/apispec_1.json | jq '.paths["/api/schema/roi"]'
```

### Automated Verification Script

See: `verify_swagger.sh` (created alongside this document)

```bash
# Run verification
./verify_swagger.sh
```

---

## 🌐 Using Swagger UI

### Accessing the Interface

1. **Start the server:**
   ```bash
   ./start_server.sh
   ```

2. **Open Swagger UI:**
   - Navigate to: http://localhost:5000/apidocs/
   - Or if accessing remotely: http://<server-ip>:5000/apidocs/

3. **Explore endpoints:**
   - Browse by tags/categories
   - Click on endpoints to expand details
   - View request/response schemas
   - See example values

4. **Test endpoints:**
   - Click "Try it out" button
   - Fill in parameters
   - Click "Execute"
   - View response

### Using the OpenAPI Spec

#### Generate Client Code
```bash
# Install OpenAPI Generator
npm install -g @openapitools/openapi-generator-cli

# Generate Python client
openapi-generator-cli generate \
  -i http://localhost:5000/apispec_1.json \
  -g python \
  -o ./generated-client

# Generate TypeScript client
openapi-generator-cli generate \
  -i http://localhost:5000/apispec_1.json \
  -g typescript-axios \
  -o ./generated-client-ts
```

#### Import into Postman
1. Open Postman
2. Click "Import"
3. Enter URL: `http://localhost:5000/apispec_1.json`
4. Click "Import"
5. Collection created with all endpoints

#### Use with API Testing Tools
```python
# Python example with requests
import requests

# Get the spec
spec = requests.get('http://localhost:5000/apispec_1.json').json()

# Iterate through endpoints
for path, methods in spec['paths'].items():
    for method, details in methods.items():
        print(f"{method.upper()} {path}: {details.get('summary', 'No summary')}")
```

---

## 📦 Dependencies

### Required Package
```plaintext
flasgger>=0.9.0  # For Swagger/OpenAPI documentation
```

### Installation
```bash
# Already included in requirements.txt
pip install flasgger

# Or install all dependencies
pip install -r requirements.txt
```

### Verification
```bash
# Check if flasgger is installed
python -c "import flasgger; print(flasgger.__version__)"
```

---

## 🔄 Maintenance

### Adding Documentation to New Endpoints

When creating new endpoints, add Swagger documentation:

```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    """Endpoint summary.
    ---
    tags:
      - Appropriate Category
    summary: Brief description
    description: Detailed description
    parameters:
      - name: parameter_name
        in: body
        required: true
        schema:
          type: object
          properties:
            field:
              type: string
    responses:
      200:
        description: Success
        schema:
          type: object
          properties:
            result:
              type: string
      400:
        description: Bad request
    """
    # Implementation
    pass
```

### Updating API Information

To update API metadata, modify `swagger_template` in `server/simple_api_server.py`:

```python
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Your API Title",
        "description": "Your API Description",
        "version": "x.y.z",  # Update version
        # ... other fields
    }
}
```

### Regenerating Documentation

Documentation is automatically generated from docstrings. To refresh:

1. Update endpoint docstrings
2. Restart the server
3. Refresh Swagger UI page

---

## 🎯 Best Practices

### Documentation Guidelines

1. **Always include:**
   - Clear summary (one line)
   - Detailed description
   - All parameters with types
   - All response codes
   - Example values where helpful

2. **Use appropriate tags:**
   - Group related endpoints
   - Use consistent naming
   - Keep tags organized

3. **Provide examples:**
   - Show example request bodies
   - Include sample responses
   - Use realistic data

4. **Document errors:**
   - Include all possible error responses
   - Explain error conditions
   - Provide error message format

5. **Keep it updated:**
   - Update docs when changing endpoints
   - Remove docs for deprecated endpoints
   - Version the API appropriately

### Schema Definitions

Use consistent schema definitions:

```python
responses:
  200:
    description: Success
    schema:
      type: object
      properties:
        status:
          type: string
          example: "success"
        data:
          type: object
        message:
          type: string
```

---

## 🚀 Advanced Features

### Custom Validators

Add custom validators in Swagger config:

```python
from flasgger import Swagger, swag_from

swagger_config = {
    # ... existing config
    "validator_url": "https://validator.swagger.io/validator"
}
```

### Security Definitions

Add authentication documentation:

```python
swagger_template = {
    # ... existing template
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using Bearer scheme"
        }
    },
    "security": [{"Bearer": []}]
}
```

### External Documentation

Link to external docs:

```python
@app.route('/api/endpoint')
def endpoint():
    """Endpoint summary.
    ---
    externalDocs:
      description: Find more info here
      url: https://docs.example.com/endpoint
    """
```

---

## 📊 Statistics

### Current Coverage

- **Total Endpoints Documented:** ~30+ endpoints
- **Endpoint Categories:** 4 main categories
  - Schema (3 endpoints)
  - Inspection (~15 endpoints)
  - Product Management (~8 endpoints)
  - Golden Sample Management (~4 endpoints)
  - Session Management (~3 endpoints)

- **Documentation Format:** OpenAPI 2.0 (Swagger)
- **Interactive UI:** Flasgger
- **Auto-generated:** Yes (from docstrings)

---

## 🐛 Troubleshooting

### Common Issues

#### Swagger UI Not Loading

**Symptom:** Cannot access /apidocs/
**Solution:**
```bash
# Check if flasgger is installed
pip install flasgger

# Verify server is running
curl http://localhost:5000/apidocs/

# Check server logs for errors
tail -f server.log
```

#### Missing Endpoints in Documentation

**Symptom:** Some endpoints don't appear in Swagger UI
**Solution:**
1. Ensure endpoint has docstring with `---` separator
2. Check docstring YAML syntax
3. Restart server to refresh docs
4. Check server logs for parsing errors

#### Incorrect Schema Display

**Symptom:** Schema properties not showing correctly
**Solution:**
1. Validate YAML syntax in docstring
2. Use proper indentation (2 spaces)
3. Check property type definitions
4. Test with OpenAPI validator

---

## 📖 References

### Official Documentation
- **Flasgger:** https://github.com/flasgger/flasgger
- **OpenAPI 2.0 Spec:** https://swagger.io/specification/v2/
- **Swagger UI:** https://swagger.io/tools/swagger-ui/

### Related Documentation
- `docs/SCHEMA_API_ENDPOINTS.md` - Schema endpoint details
- `docs/PROJECT_INSTRUCTIONS.md` - API endpoint logic
- `README.md` - General project overview

---

## ✨ Summary

The Visual AOI Server includes comprehensive Swagger/OpenAPI documentation that:

✅ **Covers all API endpoints** - Schema, inspection, product management, golden samples  
✅ **Interactive UI** - Test endpoints directly from browser  
✅ **Machine-readable spec** - Generate clients, integrate with tools  
✅ **Auto-generated** - Documentation from code docstrings  
✅ **Standards-compliant** - OpenAPI 2.0 (Swagger) format  
✅ **Always up-to-date** - Regenerated on server start  
✅ **Easy to extend** - Simple docstring format for new endpoints  

**Access the documentation at:** http://localhost:5000/apidocs/

---

**Status:** ✅ Active and Verified  
**Last Updated:** October 3, 2025  
**Version:** 1.0.0
