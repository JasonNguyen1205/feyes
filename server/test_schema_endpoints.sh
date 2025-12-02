#!/bin/bash
# Test Schema API Endpoints
# Usage: ./test_schema_endpoints.sh

BASE_URL="http://localhost:5000"

echo "======================================"
echo "Testing Schema API Endpoints"
echo "======================================"
echo ""

echo "1. Testing /api/schema/version"
echo "--------------------------------------"
curl -s "${BASE_URL}/api/schema/version" | python3 -m json.tool | head -30
echo ""
echo ""

echo "2. Testing /api/schema/roi (ROI Structure)"
echo "--------------------------------------"
echo "Getting ROI version and field count..."
curl -s "${BASE_URL}/api/schema/roi" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Version: {data['version']}\"); print(f\"Format: {data['format']}\"); print(f\"Fields: {len(data['fields'])}\"); print(f\"Updated: {data['updated']}\")"
echo ""
echo "Field 10 (is_device_barcode) details:"
curl -s "${BASE_URL}/api/schema/roi" | python3 -c "import sys, json; data=json.load(sys.stdin); field10=[f for f in data['fields'] if f['index']==10][0]; print(json.dumps(field10, indent=2))" 2>/dev/null | head -15
echo ""
echo ""

echo "3. Testing /api/schema/result (Result Structure)"
echo "--------------------------------------"
echo "Getting result structure version..."
curl -s "${BASE_URL}/api/schema/result" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Version: {data['version']}\"); print(f\"Format: {data['format']}\"); print(f\"Updated: {data['updated']}\")"
echo ""
echo "Barcode priority logic (first 2 priorities):"
curl -s "${BASE_URL}/api/schema/result" | python3 -c "import sys, json; data=json.load(sys.stdin); priorities=data['barcode_priority_logic']['priorities'][:2]; print(json.dumps(priorities, indent=2))"
echo ""
echo ""

echo "4. Testing Validation Rules"
echo "--------------------------------------"
echo "Consistency validation rules:"
curl -s "${BASE_URL}/api/schema/result" | python3 -c "import sys, json; data=json.load(sys.stdin); rules=data['validation_rules']['consistency'][:3]; [print(f\"  - {rule}\") for rule in rules]"
echo ""
echo ""

echo "5. Testing ROI Types Information"
echo "--------------------------------------"
echo "Available ROI types:"
curl -s "${BASE_URL}/api/schema/roi" | python3 -c "import sys, json; data=json.load(sys.stdin); types=data['roi_types']; [print(f\"  Type {id}: {info['name']} - {info['description']}\") for id, info in types.items()]"
echo ""
echo ""

echo "======================================"
echo "Schema API Endpoints Test Complete"
echo "======================================"
echo ""
echo "Full documentation: docs/SCHEMA_API_ENDPOINTS.md"
echo "ROI Specification: docs/ROI_DEFINITION_SPECIFICATION.md"
echo "Result Specification: docs/INSPECTION_RESULT_SPECIFICATION.md"
