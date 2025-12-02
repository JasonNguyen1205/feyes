#!/bin/bash

# Swagger Documentation Verification Script
# Tests that Swagger/OpenAPI documentation is properly configured and accessible

echo "================================================"
echo "Visual AOI Server - Swagger Documentation Test"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASS_COUNT=0
FAIL_COUNT=0

# Function to test an endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected="$3"
    
    echo -n "Testing $name... "
    
    response=$(curl -s "$url" 2>/dev/null)
    exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}FAIL${NC} (Connection failed)"
        ((FAIL_COUNT++))
        return 1
    fi
    
    if [ -z "$expected" ]; then
        # Just check if we got any response
        if [ -n "$response" ]; then
            echo -e "${GREEN}PASS${NC}"
            ((PASS_COUNT++))
            return 0
        else
            echo -e "${RED}FAIL${NC} (Empty response)"
            ((FAIL_COUNT++))
            return 1
        fi
    else
        # Check if response contains expected string
        if echo "$response" | grep -q "$expected"; then
            echo -e "${GREEN}PASS${NC}"
            ((PASS_COUNT++))
            return 0
        else
            echo -e "${RED}FAIL${NC} (Expected: $expected)"
            ((FAIL_COUNT++))
            return 1
        fi
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local name="$1"
    local url="$2"
    local jq_query="$3"
    local expected="$4"
    
    echo -n "Testing $name... "
    
    result=$(curl -s "$url" 2>/dev/null | jq -r "$jq_query" 2>/dev/null)
    
    if [ "$result" = "$expected" ]; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS_COUNT++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (Got: $result, Expected: $expected)"
        ((FAIL_COUNT++))
        return 1
    fi
}

# Test 1: Server is running
echo "1. Server Status"
echo "----------------"
test_endpoint "Server connectivity" "http://localhost:5000/api/status" ""
echo ""

# Test 2: Swagger UI is accessible
echo "2. Swagger UI"
echo "-------------"
test_endpoint "Swagger UI HTML" "http://localhost:5000/apidocs/" "<title>Flasgger</title>"
echo ""

# Test 3: OpenAPI spec is available
echo "3. OpenAPI Specification"
echo "------------------------"
test_json_endpoint "API spec available" "http://localhost:5000/apispec_1.json" ".swagger" "2.0"
test_json_endpoint "API title" "http://localhost:5000/apispec_1.json" ".info.title" "Visual AOI Server API"
test_json_endpoint "API version" "http://localhost:5000/apispec_1.json" ".info.version" "1.0.0"
echo ""

# Test 4: Schema endpoints are documented
echo "4. Schema Endpoints in Swagger"
echo "-------------------------------"

# Check if schema endpoints exist in the spec
schema_roi=$(curl -s "http://localhost:5000/apispec_1.json" 2>/dev/null | jq -r '.paths["/api/schema/roi"] | type' 2>/dev/null)
schema_result=$(curl -s "http://localhost:5000/apispec_1.json" 2>/dev/null | jq -r '.paths["/api/schema/result"] | type' 2>/dev/null)
schema_version=$(curl -s "http://localhost:5000/apispec_1.json" 2>/dev/null | jq -r '.paths["/api/schema/version"] | type' 2>/dev/null)

echo -n "Testing /api/schema/roi documented... "
if [ "$schema_roi" = "object" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL_COUNT++))
fi

echo -n "Testing /api/schema/result documented... "
if [ "$schema_result" = "object" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL_COUNT++))
fi

echo -n "Testing /api/schema/version documented... "
if [ "$schema_version" = "object" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL_COUNT++))
fi

echo ""

# Test 5: Endpoint documentation details
echo "5. Endpoint Documentation Quality"
echo "---------------------------------"

# Check if ROI schema endpoint has proper documentation
roi_summary=$(curl -s "http://localhost:5000/apispec_1.json" 2>/dev/null | jq -r '.paths["/api/schema/roi"].get.summary' 2>/dev/null)
roi_tags=$(curl -s "http://localhost:5000/apispec_1.json" 2>/dev/null | jq -r '.paths["/api/schema/roi"].get.tags[0]' 2>/dev/null)
roi_description=$(curl -s "http://localhost:5000/apispec_1.json" 2>/dev/null | jq -r '.paths["/api/schema/roi"].get.description' 2>/dev/null)

echo -n "Testing ROI schema has summary... "
if [ -n "$roi_summary" ] && [ "$roi_summary" != "null" ]; then
    echo -e "${GREEN}PASS${NC} ($roi_summary)"
    ((PASS_COUNT++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL_COUNT++))
fi

echo -n "Testing ROI schema has tags... "
if [ "$roi_tags" = "Schema" ]; then
    echo -e "${GREEN}PASS${NC} (Tag: Schema)"
    ((PASS_COUNT++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL_COUNT++))
fi

echo -n "Testing ROI schema has description... "
if [ -n "$roi_description" ] && [ "$roi_description" != "null" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS_COUNT++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL_COUNT++))
fi

echo ""

# Test 6: Count total documented endpoints
echo "6. Documentation Coverage"
echo "-------------------------"

total_paths=$(curl -s "http://localhost:5000/apispec_1.json" 2>/dev/null | jq -r '.paths | keys | length' 2>/dev/null)
echo "Total documented endpoints: $total_paths"

if [ "$total_paths" -gt 20 ]; then
    echo -e "${GREEN}Good coverage${NC} ($total_paths endpoints)"
    ((PASS_COUNT++))
else
    echo -e "${YELLOW}Moderate coverage${NC} ($total_paths endpoints)"
fi

echo ""

# Summary
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "Passed: ${GREEN}$PASS_COUNT${NC}"
echo -e "Failed: ${RED}$FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Swagger documentation is properly configured and accessible."
    echo "Access it at: http://localhost:5000/apidocs/"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Please check:"
    echo "1. Server is running: ./start_server.sh"
    echo "2. Flasgger is installed: pip install flasgger"
    echo "3. Check server logs for errors"
    exit 1
fi
