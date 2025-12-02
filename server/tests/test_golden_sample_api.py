#!/usr/bin/env python3
"""
Test Golden Sample Management API Endpoints
Tests the enhanced golden sample API with file paths instead of Base64.
"""

import pytest
import requests
import json
import os
import base64
from io import BytesIO
from PIL import Image

# Server configuration
BASE_URL = "http://localhost:5000"
TEST_PRODUCT = "20003548"  # Product with existing golden samples
TEST_ROI_ID = 3  # ROI with existing golden sample


class TestGoldenSampleAPI:
    """Test suite for golden sample management API endpoints."""
    
    @pytest.fixture(scope="class")
    def server_url(self):
        """Server base URL fixture."""
        return BASE_URL
    
    def test_list_products_with_golden_samples(self, server_url):
        """Test GET /api/golden-sample/products endpoint."""
        url = f"{server_url}/api/golden-sample/products"
        response = requests.get(url)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert 'products' in data
        assert 'total_products' in data
        assert isinstance(data['products'], list)
        assert data['total_products'] == len(data['products'])
        
        # Check product structure
        if data['products']:
            product = data['products'][0]
            assert 'product_name' in product
            assert 'total_rois' in product
            assert 'total_samples' in product
            assert 'total_size' in product
            assert 'rois' in product
            
        print(f"✓ Found {data['total_products']} products with golden samples")
        for product in data['products'][:5]:  # Show first 5
            print(f"  - {product['product_name']}: {product['total_rois']} ROIs, "
                  f"{product['total_samples']} samples, {product['total_size']} bytes")
    
    def test_get_golden_samples_with_file_paths(self, server_url):
        """Test GET /api/golden-sample/<product>/<roi_id> returns file paths."""
        url = f"{server_url}/api/golden-sample/{TEST_PRODUCT}/{TEST_ROI_ID}"
        response = requests.get(url)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert 'golden_samples' in data
        assert isinstance(data['golden_samples'], list)
        
        if data['golden_samples']:
            sample = data['golden_samples'][0]
            
            # Verify all expected fields
            assert 'name' in sample
            assert 'type' in sample
            assert 'is_best' in sample
            assert 'created_time' in sample
            assert 'file_size' in sample
            assert 'file_path' in sample
            
            # Verify file_path format
            assert sample['file_path'].startswith('/mnt/visual-aoi-shared/golden/')
            assert TEST_PRODUCT in sample['file_path']
            assert f"roi_{TEST_ROI_ID}" in sample['file_path']
            
            # Verify image_data is NOT included by default
            assert 'image_data' not in sample
            
            print(f"✓ Found {len(data['golden_samples'])} golden samples for {TEST_PRODUCT} ROI {TEST_ROI_ID}")
            for s in data['golden_samples']:
                print(f"  - {s['name']}: {s['file_size']} bytes, path: {s['file_path']}")
    
    def test_get_golden_samples_with_images_flag(self, server_url):
        """Test GET with include_images=true returns Base64 data (backward compatibility)."""
        url = f"{server_url}/api/golden-sample/{TEST_PRODUCT}/{TEST_ROI_ID}?include_images=true"
        response = requests.get(url)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        if data['golden_samples']:
            sample = data['golden_samples'][0]
            
            # Should include both file_path AND image_data
            assert 'file_path' in sample
            assert 'image_data' in sample
            
            # Verify image_data format
            if sample['image_data']:
                assert sample['image_data'].startswith('data:image/jpeg;base64,')
                print(f"✓ Base64 data included when include_images=true")
    
    def test_get_golden_samples_metadata(self, server_url):
        """Test GET /api/golden-sample/<product>/<roi_id>/metadata endpoint."""
        url = f"{server_url}/api/golden-sample/{TEST_PRODUCT}/{TEST_ROI_ID}/metadata"
        response = requests.get(url)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert 'product_name' in data
        assert 'roi_id' in data
        assert 'golden_samples' in data
        assert 'total_samples' in data
        assert 'total_size' in data
        
        assert data['product_name'] == TEST_PRODUCT
        assert data['roi_id'] == TEST_ROI_ID
        
        # Verify no image data or file paths
        if data['golden_samples']:
            sample = data['golden_samples'][0]
            assert 'image_data' not in sample
            assert 'file_path' not in sample
            
            # Should have metadata only
            assert 'name' in sample
            assert 'type' in sample
            assert 'file_size' in sample
            
        print(f"✓ Metadata endpoint returns {data['total_samples']} samples, "
              f"{data['total_size']} bytes total (no image data)")
    
    def test_download_golden_sample(self, server_url):
        """Test GET /api/golden-sample/<product>/<roi_id>/download/<filename> endpoint."""
        url = f"{server_url}/api/golden-sample/{TEST_PRODUCT}/{TEST_ROI_ID}/download/best_golden.jpg"
        response = requests.get(url)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify content type
        assert 'image/jpeg' in response.headers.get('Content-Type', '')
        
        # Verify image data is valid
        assert len(response.content) > 0
        
        # Try to open as image
        try:
            img = Image.open(BytesIO(response.content))
            print(f"✓ Downloaded golden sample: {img.format}, {img.size}, {len(response.content)} bytes")
        except Exception as e:
            pytest.fail(f"Downloaded content is not a valid image: {e}")
    
    def test_download_nonexistent_file(self, server_url):
        """Test download endpoint with nonexistent file returns 404."""
        url = f"{server_url}/api/golden-sample/{TEST_PRODUCT}/{TEST_ROI_ID}/download/nonexistent.jpg"
        response = requests.get(url)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert 'error' in data
        print(f"✓ Download nonexistent file returns 404: {data['error']}")
    
    def test_download_path_traversal_protection(self, server_url):
        """Test download endpoint blocks path traversal attempts."""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "best_golden.jpg/../../../secrets.txt"
        ]
        
        for filename in malicious_filenames:
            url = f"{server_url}/api/golden-sample/{TEST_PRODUCT}/{TEST_ROI_ID}/download/{filename}"
            response = requests.get(url)
            
            # Should return either 400 (validation error) or 404 (file not found after security check)
            assert response.status_code in [400, 404], f"Path traversal not properly handled for: {filename}"
            
            # Try to parse JSON if response is JSON
            try:
                data = response.json()
                assert 'error' in data
            except:
                # Non-JSON error response is also acceptable (e.g., Flask 404 page)
                pass
        
        print(f"✓ Path traversal protection working")
    
    def test_restore_golden_sample_validation(self, server_url):
        """Test restore endpoint validates backup filename format."""
        url = f"{server_url}/api/golden-sample/restore"
        
        # Test invalid filename format
        invalid_data = {
            'product_name': TEST_PRODUCT,
            'roi_id': TEST_ROI_ID,
            'backup_filename': 'invalid_filename.jpg'
        }
        
        response = requests.post(url, json=invalid_data)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert 'error' in data
        assert 'original_' in data['error'] or 'format' in data['error'].lower()
        
        print(f"✓ Restore endpoint validates backup filename format: {data['error']}")
    
    def test_response_size_comparison(self, server_url):
        """Compare response sizes: file paths vs Base64 data."""
        # Get with file paths (default)
        url_paths = f"{server_url}/api/golden-sample/{TEST_PRODUCT}/{TEST_ROI_ID}"
        response_paths = requests.get(url_paths)
        size_paths = len(response_paths.content)
        
        # Get with Base64 data
        url_images = f"{server_url}/api/golden-sample/{TEST_PRODUCT}/{TEST_ROI_ID}?include_images=true"
        response_images = requests.get(url_images)
        size_images = len(response_images.content)
        
        # Calculate size reduction
        if size_images > 0:
            reduction_percent = ((size_images - size_paths) / size_images) * 100
            print(f"\n✓ Response size comparison:")
            print(f"  - With file paths: {size_paths:,} bytes")
            print(f"  - With Base64 data: {size_images:,} bytes")
            print(f"  - Size reduction: {reduction_percent:.1f}% ({size_images - size_paths:,} bytes saved)")
            
            # Should be significantly smaller
            assert size_paths < size_images, "File path response should be smaller than Base64"


def test_missing_parameters():
    """Test endpoints return proper errors for missing parameters."""
    url = f"{BASE_URL}/api/golden-sample/restore"
    
    # Missing parameters
    response = requests.post(url, json={})
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
    assert 'required' in data['error'].lower()
    print(f"✓ Missing parameters handled correctly: {data['error']}")


def test_nonexistent_product():
    """Test endpoints handle nonexistent products gracefully."""
    url = f"{BASE_URL}/api/golden-sample/nonexistent_product/1"
    response = requests.get(url)
    
    assert response.status_code == 200
    data = response.json()
    assert 'golden_samples' in data
    assert len(data['golden_samples']) == 0
    print(f"✓ Nonexistent product returns empty list")


if __name__ == '__main__':
    print("Golden Sample API Test Suite")
    print("=" * 60)
    print(f"Server: {BASE_URL}")
    print(f"Test Product: {TEST_PRODUCT}")
    print(f"Test ROI: {TEST_ROI_ID}")
    print("=" * 60)
    print("\nRunning tests...\n")
    
    # Run pytest with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
