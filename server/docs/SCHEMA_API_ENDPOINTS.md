# Schema API Endpoints Documentation

**Version:** 1.0  
**Date:** October 3, 2025  
**Purpose:** Programmatic access to ROI and result structure specifications

---

## 🎯 Overview

The Visual AOI Server now exposes REST API endpoints that provide programmatic access to the ROI structure and inspection result specifications. This makes it easier for clients to:

- Automatically adapt to structure changes
- Validate configurations before sending
- Generate client-side code from schema
- Display structure documentation in UI
- Handle backward compatibility

---

## 📡 Available Endpoints

### 1. `/api/schema/roi` - ROI Structure Schema

**Method:** `GET`  
**Description:** Returns the complete ROI structure specification including field definitions, types, constraints, and examples.

**Response Format:**

```json
{
  "version": "3.0",
  "format": "11-field",
  "updated": "2025-10-03",
  "fields": [...],
  "roi_types": {...},
  "barcode_priority_logic": {...},
  "backward_compatible": [...],
  "example": {...}
}
```

**Usage:**

```bash
curl http://localhost:5000/api/schema/roi
```

**Response Fields:**

- **version**: Current ROI structure version (e.g., "3.0")
- **format**: Format description (e.g., "11-field")
- **updated**: Last update date (ISO 8601)
- **fields**: Array of field definitions with:
  - `index`: Field position in tuple
  - `name`: Field name
  - `type`: Data type
  - `required`: Whether field is required
  - `description`: Field purpose
  - `constraints`: Validation rules
  - `default`: Default value if not provided
  - `added_in`: Version when field was added (if applicable)
  
- **roi_types**: ROI type definitions (1=Barcode, 2=Compare, 3=OCR, 4=Color)
  - Type name and description
  - Relevant fields for this type
  - Ignored fields for this type
  - Configuration location (for Color type)
  
- **barcode_priority_logic**: Barcode selection priority rules
  - Priority levels (0-4)
  - Source for each priority
  - Description of logic
  
- **backward_compatible**: Legacy format support
  - Supported versions
  - Number of fields
  - Migration strategy
  
- **example**: Sample ROI configurations for each type

**Example Response (abbreviated):**

```json
{
  "version": "3.0",
  "format": "11-field",
  "fields": [
    {
      "index": 0,
      "name": "idx",
      "type": "int",
      "required": true,
      "description": "ROI index (1-based)",
      "constraints": "Must be unique, positive integer"
    },
    {
      "index": 10,
      "name": "is_device_barcode",
      "type": "bool | None",
      "required": false,
      "description": "Device main barcode flag (NEW in v3.0)",
      "constraints": "Only meaningful for Barcode ROIs (Type 1)",
      "default": null,
      "added_in": "3.0"
    }
  ],
  "roi_types": {
    "1": {
      "name": "Barcode",
      "description": "Barcode detection and reading",
      "relevant_fields": ["idx", "type", "coords", "focus", "exposure_time", "feature_method", "rotation", "device_location", "is_device_barcode"],
      "ignored_fields": ["ai_threshold", "expected_text"]
    }
  },
  "barcode_priority_logic": {
    "priorities": [
      {
        "priority": 0,
        "source": "ROI Barcode with is_device_barcode=True",
        "description": "Explicitly marked device identifier (NEW in v3.0)",
        "added_in": "3.0"
      }
    ]
  }
}
```

---

### 2. `/api/schema/result` - Inspection Result Structure Schema

**Method:** `GET`  
**Description:** Returns the complete inspection result structure specification including field definitions, validation rules, and examples.

**Response Format:**

```json
{
  "version": "2.0",
  "format": "JSON Object",
  "updated": "2025-10-03",
  "top_level_fields": {...},
  "roi_result_structure": {...},
  "device_summary_structure": {...},
  "overall_result_structure": {...},
  "barcode_priority_logic": {...},
  "validation_rules": {...},
  "example": {...}
}
```

**Usage:**

```bash
curl http://localhost:5000/api/schema/result
```

**Response Fields:**

- **version**: Current result structure version
- **format**: Format description
- **updated**: Last update date
- **top_level_fields**: Root-level fields in response
  - Field name
  - Type
  - Required flag
  - Description
  
- **roi_result_structure**: ROI result object specification
  - **common_fields**: Fields present in all ROI types
  - **type_specific_fields**: Fields specific to barcode/compare/ocr
    - Field definitions
    - Pass conditions
    - Value constraints

- **device_summary_structure**: Device summary object specification
  - Field definitions
  - Calculation logic
  - Constraints
  
- **overall_result_structure**: Overall result object specification
  - Field definitions
  - Pass/fail logic
  
- **barcode_priority_logic**: Device barcode selection rules
  - Priority levels
  - Source descriptions
  
- **validation_rules**: Validation constraints
  - Consistency rules
  - Type validation
  - Type-specific validation
  
- **example**: Complete example response

**Example Response (abbreviated):**

```json
{
  "version": "2.0",
  "top_level_fields": {
    "roi_results": {
      "type": "array",
      "required": true,
      "description": "Array of individual ROI processing results"
    },
    "device_summaries": {
      "type": "object",
      "required": true,
      "description": "Dictionary of per-device summary statistics"
    }
  },
  "roi_result_structure": {
    "common_fields": {
      "roi_id": {"type": "int", "required": true},
      "device_id": {"type": "int", "required": true},
      "passed": {"type": "bool", "required": true}
    },
    "type_specific_fields": {
      "barcode": {
        "barcode_values": {
          "type": "array[string]",
          "required": true,
          "pass_condition": "Array not empty and first element valid"
        }
      },
      "compare": {
        "ai_similarity": {
          "type": "float",
          "range": [0.0, 1.0]
        }
      }
    }
  },
  "validation_rules": {
    "consistency": [
      "total_rois must equal len(roi_results)",
      "overall.passed must equal (passed_rois == total_rois AND total_rois > 0)"
    ]
  }
}
```

---

### 3. `/api/schema/version` - Schema Version Information

**Method:** `GET`  
**Description:** Returns version information for both ROI and result structures with change history.

**Response Format:**

```json
{
  "roi_structure": {...},
  "result_structure": {...},
  "server_version": "3.0.0",
  "api_version": "1.0",
  "endpoints": {...}
}
```

**Usage:**

```bash
curl http://localhost:5000/api/schema/version
```

**Response Fields:**

- **roi_structure**: ROI version info
  - Current version
  - Format description
  - Number of fields
  - Update date
  - Backward compatible versions
  - Change history by version
  
- **result_structure**: Result version info
  - Current version
  - Format description
  - Main sections
  - Change history
  
- **server_version**: Server software version
- **api_version**: API version
- **endpoints**: Links to schema endpoints

**Example Response:**

```json
{
  "roi_structure": {
    "version": "3.0",
    "format": "11-field",
    "fields": 11,
    "updated": "2025-10-03",
    "backward_compatible_versions": ["1.0", "1.5", "1.6", "1.7", "1.8", "1.9", "2.0"],
    "changes": {
      "3.0": "Added is_device_barcode field for device main barcode identification",
      "2.0": "Added expected_text field for OCR validation"
    }
  },
  "result_structure": {
    "version": "2.0",
    "format": "JSON Object",
    "main_sections": ["roi_results", "device_summaries", "overall_result", "processing_time"],
    "changes": {
      "2.0": "Enhanced barcode priority logic with is_device_barcode support"
    }
  },
  "endpoints": {
    "roi_schema": "/api/schema/roi",
    "result_schema": "/api/schema/result",
    "version": "/api/schema/version"
  }
}
```

---

## 💻 Client Implementation Examples

### Python Client

```python
import requests
import json

class AOIClient:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.roi_schema = None
        self.result_schema = None
        
    def fetch_schemas(self):
        """Fetch and cache schema definitions."""
        # Get ROI schema
        response = requests.get(f'{self.base_url}/api/schema/roi')
        self.roi_schema = response.json()
        
        # Get result schema
        response = requests.get(f'{self.base_url}/api/schema/result')
        self.result_schema = response.json()
        
        print(f"ROI Schema Version: {self.roi_schema['version']}")
        print(f"Result Schema Version: {self.result_schema['version']}")
        
    def validate_roi(self, roi):
        """Validate ROI against current schema."""
        if not self.roi_schema:
            self.fetch_schemas()
        
        expected_fields = len(self.roi_schema['fields'])
        if len(roi) != expected_fields:
            print(f"Warning: ROI has {len(roi)} fields, expected {expected_fields}")
            print(f"ROI will be auto-upgraded to v{self.roi_schema['version']}")
        
        return True
    
    def get_field_info(self, field_name):
        """Get information about a specific field."""
        if not self.roi_schema:
            self.fetch_schemas()
        
        for field in self.roi_schema['fields']:
            if field['name'] == field_name:
                return field
        return None
    
    def validate_result(self, result):
        """Validate inspection result against schema."""
        if not self.result_schema:
            self.fetch_schemas()
        
        # Check required top-level fields
        for field_name, field_spec in self.result_schema['top_level_fields'].items():
            if field_spec['required'] and field_name not in result:
                print(f"Error: Missing required field '{field_name}'")
                return False
        
        # Check consistency rules
        if result['overall_result']['total_rois'] != len(result['roi_results']):
            print("Error: total_rois doesn't match roi_results length")
            return False
        
        return True

# Usage
client = AOIClient()
client.fetch_schemas()

# Validate an ROI
roi = [1, 1, [50, 50, 150, 100], 305, 3000, None, 'barcode', 0, 1, None, True]
if client.validate_roi(roi):
    print("ROI is valid")

# Get field information
field_info = client.get_field_info('is_device_barcode')
print(f"Field: {field_info['name']}")
print(f"Type: {field_info['type']}")
print(f"Description: {field_info['description']}")
print(f"Added in: {field_info.get('added_in', 'original')}")
```

### JavaScript Client

```javascript
class AOIClient {
  constructor(baseUrl = 'http://localhost:5000') {
    this.baseUrl = baseUrl;
    this.roiSchema = null;
    this.resultSchema = null;
  }
  
  async fetchSchemas() {
    // Get ROI schema
    const roiResponse = await fetch(`${this.baseUrl}/api/schema/roi`);
    this.roiSchema = await roiResponse.json();
    
    // Get result schema
    const resultResponse = await fetch(`${this.baseUrl}/api/schema/result`);
    this.resultSchema = await resultResponse.json();
    
    console.log(`ROI Schema Version: ${this.roiSchema.version}`);
    console.log(`Result Schema Version: ${this.resultSchema.version}`);
  }
  
  validateROI(roi) {
    if (!this.roiSchema) {
      throw new Error('Schema not loaded. Call fetchSchemas() first.');
    }
    
    const expectedFields = this.roiSchema.fields.length;
    if (roi.length !== expectedFields) {
      console.warn(`ROI has ${roi.length} fields, expected ${expectedFields}`);
      console.warn(`ROI will be auto-upgraded to v${this.roiSchema.version}`);
    }
    
    return true;
  }
  
  getFieldInfo(fieldName) {
    if (!this.roiSchema) {
      throw new Error('Schema not loaded. Call fetchSchemas() first.');
    }
    
    return this.roiSchema.fields.find(f => f.name === fieldName);
  }
  
  validateResult(result) {
    if (!this.resultSchema) {
      throw new Error('Schema not loaded. Call fetchSchemas() first.');
    }
    
    // Check required top-level fields
    for (const [fieldName, fieldSpec] of Object.entries(this.resultSchema.top_level_fields)) {
      if (fieldSpec.required && !(fieldName in result)) {
        console.error(`Missing required field '${fieldName}'`);
        return false;
      }
    }
    
    // Check consistency
    if (result.overall_result.total_rois !== result.roi_results.length) {
      console.error('total_rois doesn\'t match roi_results length');
      return false;
    }
    
    return true;
  }
}

// Usage
const client = new AOIClient();

await client.fetchSchemas();

// Validate an ROI
const roi = [1, 1, [50, 50, 150, 100], 305, 3000, null, 'barcode', 0, 1, null, true];
if (client.validateROI(roi)) {
  console.log('ROI is valid');
}

// Get field information
const fieldInfo = client.getFieldInfo('is_device_barcode');
console.log(`Field: ${fieldInfo.name}`);
console.log(`Type: ${fieldInfo.type}`);
console.log(`Description: ${fieldInfo.description}`);
console.log(`Added in: ${fieldInfo.added_in || 'original'}`);
```

---

## 🔄 Use Cases

### 1. Automatic Client Adaptation

Clients can fetch the schema on startup and adapt their validation logic:

```python
def initialize():
    # Fetch current schema
    schema = requests.get('http://server/api/schema/version').json()
    
    # Check if we support this version
    roi_version = schema['roi_structure']['version']
    if roi_version != '3.0':
        print(f"Warning: Server using ROI v{roi_version}, client expects v3.0")
        print("Client will adapt to server version")
    
    # Load full schema for validation
    roi_schema = requests.get('http://server/api/schema/roi').json()
    return roi_schema
```

### 2. Configuration Validation

Validate ROI configurations before sending:

```python
def validate_roi_config(rois, schema):
    """Validate ROI configuration against schema."""
    expected_fields = len(schema['fields'])
    
    for roi in rois:
        if len(roi) < expected_fields:
            print(f"ROI {roi[0]}: Has {len(roi)} fields, will be auto-upgraded")
        
        # Validate ROI type
        roi_type = roi[1]
        if roi_type not in [1, 2, 3]:
            print(f"ROI {roi[0]}: Invalid type {roi_type}")
            return False
        
        # Type-specific validation
        type_info = schema['roi_types'][str(roi_type)]
        print(f"ROI {roi[0]}: Type {type_info['name']}")
        
    return True
```

### 3. Dynamic UI Generation

Generate UI forms based on schema:

```python
def generate_roi_form(schema):
    """Generate HTML form from ROI schema."""
    html = "<form>"
    
    for field in schema['fields']:
        field_name = field['name']
        field_type = field['type']
        description = field['description']
        required = field['required']
        
        html += f"<div class='field'>"
        html += f"<label>{field_name} {'*' if required else ''}</label>"
        html += f"<input type='text' name='{field_name}' placeholder='{description}' />"
        html += f"<span class='help'>{description}</span>"
        html += f"</div>"
    
    html += "</form>"
    return html
```

### 4. Result Parsing with Validation

Parse inspection results with schema-based validation:

```python
def parse_result(response, schema):
    """Parse and validate inspection result."""
    # Validate structure
    for field_name, field_spec in schema['top_level_fields'].items():
        if field_spec['required'] and field_name not in response:
            raise ValueError(f"Missing required field: {field_name}")
    
    # Extract data
    roi_results = response['roi_results']
    device_summaries = response['device_summaries']
    overall = response['overall_result']
    
    # Validate consistency
    if overall['total_rois'] != len(roi_results):
        raise ValueError("Inconsistent ROI counts")
    
    return {
        'passed': overall['passed'],
        'rois': roi_results,
        'devices': device_summaries,
        'time': response['processing_time']
    }
```

### 5. Version Compatibility Checking

Check version compatibility and handle differences:

```python
def check_compatibility(server_version, client_version):
    """Check if client is compatible with server."""
    version_info = requests.get('http://server/api/schema/version').json()
    
    server_roi_version = version_info['roi_structure']['version']
    compatible_versions = version_info['roi_structure']['backward_compatible_versions']
    
    if client_version in compatible_versions:
        print(f"✓ Client v{client_version} is compatible with server v{server_roi_version}")
        return True
    else:
        print(f"✗ Client v{client_version} may not be compatible with server v{server_roi_version}")
        print(f"  Supported versions: {', '.join(compatible_versions)}")
        return False
```

---

## 🧪 Testing

### Manual Testing

```bash
# 1. Get version information
curl http://localhost:5000/api/schema/version | jq

# 2. Get ROI schema
curl http://localhost:5000/api/schema/roi | jq

# 3. Get result schema
curl http://localhost:5000/api/schema/result | jq

# 4. Check specific field
curl http://localhost:5000/api/schema/roi | jq '.fields[] | select(.name == "is_device_barcode")'

# 5. Check barcode priority logic
curl http://localhost:5000/api/schema/result | jq '.barcode_priority_logic'

# 6. Get validation rules
curl http://localhost:5000/api/schema/result | jq '.validation_rules'
```

### Automated Testing

```python
import pytest
import requests

BASE_URL = 'http://localhost:5000'

def test_schema_version_endpoint():
    """Test schema version endpoint returns correct format."""
    response = requests.get(f'{BASE_URL}/api/schema/version')
    assert response.status_code == 200
    
    data = response.json()
    assert 'roi_structure' in data
    assert 'result_structure' in data
    assert 'server_version' in data
    assert data['roi_structure']['version'] == '3.0'

def test_roi_schema_endpoint():
    """Test ROI schema endpoint returns complete specification."""
    response = requests.get(f'{BASE_URL}/api/schema/roi')
    assert response.status_code == 200
    
    data = response.json()
    assert 'version' in data
    assert 'fields' in data
    assert len(data['fields']) == 11  # 11-field format
    assert 'roi_types' in data
    assert 'barcode_priority_logic' in data

def test_result_schema_endpoint():
    """Test result schema endpoint returns complete specification."""
    response = requests.get(f'{BASE_URL}/api/schema/result')
    assert response.status_code == 200
    
    data = response.json()
    assert 'version' in data
    assert 'top_level_fields' in data
    assert 'roi_result_structure' in data
    assert 'validation_rules' in data

def test_field_10_exists():
    """Test that Field 10 (is_device_barcode) exists in schema."""
    response = requests.get(f'{BASE_URL}/api/schema/roi')
    data = response.json()
    
    field_10 = next((f for f in data['fields'] if f['index'] == 10), None)
    assert field_10 is not None
    assert field_10['name'] == 'is_device_barcode'
    assert field_10['added_in'] == '3.0'

def test_barcode_priority_includes_priority_0():
    """Test that barcode priority logic includes new Priority 0."""
    response = requests.get(f'{BASE_URL}/api/schema/result')
    data = response.json()
    
    priorities = data['barcode_priority_logic']['priorities']
    priority_0 = next((p for p in priorities if p['priority'] == 0), None)
    assert priority_0 is not None
    assert 'is_device_barcode=True' in priority_0['source']
```

---

## 📚 Benefits

### For Client Developers

1. **Self-Documenting API**: No need to refer to external documentation
2. **Automatic Validation**: Validate data against current schema programmatically
3. **Version Detection**: Automatically detect and adapt to version changes
4. **Type Safety**: Generate strongly-typed client code from schema
5. **Testing**: Easier to write schema-based tests

### For System Integration

1. **Interoperability**: Easier integration with third-party systems
2. **Code Generation**: Auto-generate client SDKs from schema
3. **Contract Testing**: Validate API contracts automatically
4. **Migration**: Easier migration when structures change
5. **Documentation**: Always up-to-date API documentation

### For Maintenance

1. **Change Management**: Clear versioning and change tracking
2. **Backward Compatibility**: Explicit compatibility information
3. **Validation**: Automated validation reduces errors
4. **Debugging**: Easier to debug structure-related issues
5. **Evolution**: Smoother API evolution over time

---

## 🔧 Integration with Existing Documentation

The schema endpoints complement the existing documentation files:

- **`docs/ROI_DEFINITION_SPECIFICATION.md`** - Human-readable detailed specification
- **`/api/schema/roi`** - Machine-readable programmatic access
- **`docs/INSPECTION_RESULT_SPECIFICATION.md`** - Human-readable result format
- **`/api/schema/result`** - Machine-readable result schema

Both formats are maintained in sync, providing the best of both worlds:

- Detailed documentation for developers
- Programmatic access for automation

---

## 📝 Schema Update Process

When structures change:

1. **Update Specification Documents** (ROI_DEFINITION_SPECIFICATION.md, etc.)
2. **Update Schema Endpoints** (server/simple_api_server.py)
3. **Increment Version Numbers**
4. **Update Change History**
5. **Test All Endpoints**
6. **Update Client Libraries**

---

## 🚀 Future Enhancements

Potential future additions to schema API:

1. **Schema Validation Endpoint**: POST endpoint to validate ROI/result against schema
2. **OpenAPI/Swagger Integration**: Generate OpenAPI spec from schema
3. **GraphQL Interface**: Query schema using GraphQL
4. **Schema Diff Endpoint**: Compare two schema versions
5. **Migration Helper**: Endpoint to upgrade old format to new
6. **Type Definitions Export**: Export TypeScript/Python type definitions

---

## 📞 Support

For questions or issues with the schema API:

1. Check this documentation
2. Test endpoints with curl/Postman
3. Review response examples
4. Check server logs for errors
5. Refer to specification documents

**Related Documentation:**

- `docs/ROI_DEFINITION_SPECIFICATION.md`
- `docs/INSPECTION_RESULT_SPECIFICATION.md`
- `docs/PROJECT_INSTRUCTIONS.md`
- `docs/ROI_V3_UPGRADE_SUMMARY.md`

---

**Version:** 1.0  
**Last Updated:** October 3, 2025  
**Status:** Active
