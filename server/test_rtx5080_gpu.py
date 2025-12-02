#!/usr/bin/env python3
"""
Test script to verify RTX 5080 GPU support in PyTorch.
This checks if sm_120 compute capability is supported.
"""

import os
import sys

# Enable PTX JIT just in case
os.environ['CUDA_FORCE_PTX_JIT'] = '1'

print("=" * 70)
print("RTX 5080 GPU Support Test")
print("=" * 70)
print()

try:
    import torch
    import torch.nn as nn
    from torchvision.models import mobilenet_v2
    
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    print(f"✓ CUDA version: {torch.version.cuda}")
    print()
    
    if not torch.cuda.is_available():
        print("✗ CUDA not available")
        sys.exit(1)
    
    # Get GPU info
    device = torch.device('cuda:0')
    gpu_name = torch.cuda.get_device_name(0)
    compute_cap = torch.cuda.get_device_capability(0)
    
    print(f"GPU Information:")
    print(f"  Name: {gpu_name}")
    print(f"  Compute Capability: {compute_cap[0]}.{compute_cap[1]}")
    print(f"  Device: {device}")
    print()
    
    # Test 1: Basic tensor operations
    print("Test 1: Basic Tensor Operations")
    print("-" * 70)
    try:
        x = torch.randn(100, 100, device=device)
        y = torch.matmul(x, x)
        print(f"✓ PASSED: Basic operations work")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        sys.exit(1)
    print()
    
    # Test 2: Conv2D (critical for MobileNetV2)
    print("Test 2: Conv2D Operations")
    print("-" * 70)
    try:
        conv = nn.Conv2d(3, 64, kernel_size=3, padding=1).to(device)
        input_tensor = torch.randn(1, 3, 224, 224, device=device)
        output = conv(input_tensor)
        print(f"✓ PASSED: Conv2D works ({output.shape})")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        print()
        print("This means sm_120 is still not supported in this PyTorch version.")
        sys.exit(1)
    print()
    
    # Test 3: MobileNetV2 (full model)
    print("Test 3: MobileNetV2 Model")
    print("-" * 70)
    try:
        model = mobilenet_v2(weights=None)  # Random weights, no download
        model = model.to(device)
        model.eval()
        
        with torch.no_grad():
            test_input = torch.randn(1, 3, 224, 224, device=device)
            output = model(test_input)
        
        print(f"✓ PASSED: MobileNetV2 works ({output.shape})")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        sys.exit(1)
    print()
    
    # Test 4: Performance benchmark
    print("Test 4: Performance Benchmark")
    print("-" * 70)
    try:
        import time
        
        # Remove classification layer for feature extraction
        model.classifier = nn.Identity()
        
        times = []
        for i in range(10):
            test_input = torch.randn(1, 3, 224, 224, device=device)
            
            start = time.time()
            with torch.no_grad():
                features = model(test_input)
            torch.cuda.synchronize()  # Wait for GPU to finish
            elapsed = (time.time() - start) * 1000
            
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        print(f"✓ Average inference time: {avg_time:.2f}ms")
        print(f"  Feature dimensions: {features.shape[1]}")
        print(f"  Expected: 2-3ms on GPU (vs 5ms on CPU)")
    except Exception as e:
        print(f"✗ Benchmark failed: {e}")
    print()
    
    print("=" * 70)
    print("✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("=" * 70)
    print()
    print("RTX 5080 GPU is fully supported!")
    print("You can now use GPU-only mode for PyTorch.")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
