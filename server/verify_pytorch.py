#!/usr/bin/env python3
"""
Verification script for PyTorch installation and GPU availability.
This script checks if PyTorch is properly installed with CUDA support.
"""

import sys

print("=" * 80)
print("PYTORCH INSTALLATION VERIFICATION")
print("=" * 80)

# Test 1: Import PyTorch
print("\n1. PYTORCH IMPORT TEST")
print("-" * 80)
try:
    import torch
    print(f"✓ PyTorch imported successfully")
    print(f"  Version: {torch.__version__}")
except ImportError as e:
    print(f"✗ Failed to import PyTorch: {e}")
    sys.exit(1)

# Test 2: Check CUDA availability
print("\n2. CUDA AVAILABILITY")
print("-" * 80)
cuda_available = torch.cuda.is_available()
print(f"  CUDA available: {cuda_available}")

if cuda_available:
    print(f"  CUDA version: {torch.version.cuda}")
    print(f"  cuDNN version: {torch.backends.cudnn.version()}")
    print(f"  Number of GPUs: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        print(f"\n  GPU {i}:")
        print(f"    Name: {torch.cuda.get_device_name(i)}")
        print(f"    Compute Capability: {torch.cuda.get_device_capability(i)}")
        props = torch.cuda.get_device_properties(i)
        print(f"    Total Memory: {props.total_memory / 1024**3:.2f} GB")
else:
    print("  ⚠️  CUDA not available - PyTorch will use CPU")
    print("  Note: System will still work, but slower than GPU")

# Test 3: Test torchvision
print("\n3. TORCHVISION TEST")
print("-" * 80)
try:
    import torchvision
    print(f"✓ torchvision imported successfully")
    print(f"  Version: {torchvision.__version__}")
except ImportError as e:
    print(f"✗ Failed to import torchvision: {e}")

# Test 4: Test MobileNetV2 model loading
print("\n4. MOBILENETV2 MODEL TEST")
print("-" * 80)
try:
    from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
    print("✓ Attempting to load MobileNetV2 model...")
    
    model = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V2)
    print(f"✓ MobileNetV2 model loaded successfully")
    
    if cuda_available:
        model = model.to('cuda:0')
        print(f"✓ Model moved to GPU successfully")
    else:
        print(f"ℹ️  Model running on CPU")
    
    # Test inference
    import torch.nn as nn
    model.classifier = nn.Identity()
    model.eval()
    
    # Create dummy input
    dummy_input = torch.randn(1, 3, 224, 224)
    if cuda_available:
        dummy_input = dummy_input.to('cuda:0')
    
    with torch.no_grad():
        features = model(dummy_input)
    
    print(f"✓ Test inference successful")
    print(f"  Feature vector size: {features.shape[1]}")
    
except Exception as e:
    print(f"✗ Model test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test Visual AOI AI module
print("\n5. VISUAL AOI AI MODULE TEST")
print("-" * 80)
try:
    sys.path.insert(0, '.')
    from src.ai_pytorch import initialize_mobilenet_model, extract_features_from_array
    
    print("✓ Attempting to initialize Visual AOI AI module...")
    success = initialize_mobilenet_model()
    
    if success:
        print("✓ Visual AOI AI module initialized successfully")
        print("  → MobileNetV2 model ready for inspection")
        
        # Test feature extraction
        import numpy as np
        test_img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        features = extract_features_from_array(test_img, feature_method="mobilenet")
        
        if features is not None and len(features) > 0:
            print(f"✓ Feature extraction test passed")
            print(f"  Feature dimensions: {len(features)}")
        else:
            print("✗ Feature extraction returned empty result")
    else:
        print("✗ Visual AOI AI module initialization failed")
        
except Exception as e:
    print(f"✗ Visual AOI AI module test failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if cuda_available:
    print("\n✅ PyTorch with CUDA support is properly installed!")
    print(f"   Using GPU: {torch.cuda.get_device_name(0)}")
    print(f"   Compare ROIs with feature_method='mobilenet' will use GPU acceleration")
else:
    print("\n⚠️  PyTorch installed but CUDA not available")
    print("   Compare ROIs will use CPU (slower but functional)")

print("\n" + "=" * 80)
