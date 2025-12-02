"""
AI and machine learning functionality for Visual AOI system.
Uses PyTorch MobileNetV2 for better RTX 5080 compatibility.
"""

import threading
import cv2
import numpy as np
from PIL import Image
from numpy.linalg import norm
import os

# Allow users to force CPU mode by setting environment variable
FORCE_CPU_MODE = os.environ.get('VISUAL_AOI_FORCE_CPU', 'false').lower() == 'true'

# Import PyTorch components
try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
    from torchvision.models import mobilenet_v2
    PYTORCH_AVAILABLE = True
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
except ImportError as e:
    print(f"PyTorch not available: {e}")
    PYTORCH_AVAILABLE = False
    torch = None
    transforms = None
    mobilenet_v2 = None

# Configure PyTorch GPU safely with better error handling
def configure_pytorch_gpu():
    """Configure PyTorch GPU settings safely for RTX 5080"""
    if not PYTORCH_AVAILABLE:
        print("PyTorch not available, using fallback methods")
        return False, torch.device('cpu') if torch else None
        
    if FORCE_CPU_MODE:
        print("CPU mode forced by environment variable VISUAL_AOI_FORCE_CPU")
        return False, torch.device('cpu')
        
    try:
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            print(f"Detected {device_count} GPU(s)")
            
            for i in range(device_count):
                gpu_name = torch.cuda.get_device_name(i)
                capability = torch.cuda.get_device_capability(i)
                cc_major, cc_minor = capability
                
                if "RTX 5080" in gpu_name or cc_major >= 12:
                    print(f"  GPU {i}: {gpu_name} (compute capability {cc_major}.{cc_minor})")
                    print(f"    ✓ RTX 5080 detected - PyTorch has better support than TensorFlow")
                else:
                    print(f"  GPU {i}: {gpu_name} (compute capability {cc_major}.{cc_minor})")
            
            print("PyTorch GPU configuration completed")
            return True, torch.device('cuda:0')
        else:
            print("No CUDA GPUs detected, using CPU")
            return False, torch.device('cpu')
    except Exception as e:
        print(f"GPU configuration failed: {e}")
        print("Falling back to CPU mode")
        return False, torch.device('cpu')

# Configure GPU/CPU
if PYTORCH_AVAILABLE:
    gpu_available, device = configure_pytorch_gpu()
    print(f"Using device: {device}")
    if gpu_available:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
else:
    gpu_available, device = False, None

# ========== PYTORCH MOBILENET MODEL ==========
# Initialize as None, will be loaded later to avoid import-time conflicts
mobilenet_model = None
mobilenet_predict_lock = threading.Lock()
model_device = None  # Track which device the model was loaded on

# Image preprocessing for MobileNetV2
if PYTORCH_AVAILABLE:
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
else:
    preprocess = None

def initialize_mobilenet_model():
    """Initialize PyTorch MobileNetV2 model with proper error handling and RTX 5080 support"""
    global mobilenet_model, model_device
    if mobilenet_model is not None:
        return True
        
    if not PYTORCH_AVAILABLE:
        print("PyTorch not available, falling back to OpenCV features")
        return False
        
    print("Loading PyTorch MobileNetV2 model...")
    
    try:
        # Load pre-trained MobileNetV2 model with updated weights parameter
        from torchvision.models import MobileNet_V2_Weights
        mobilenet_model = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V2)
        
        # Remove the classification layer to get feature vectors
        mobilenet_model.classifier = nn.Identity()
        mobilenet_model.eval()  # Set to evaluation mode
        
        # Move model to appropriate device
        mobilenet_model = mobilenet_model.to(device)
        model_device = str(device)
        
        print(f"PyTorch MobileNetV2 model loaded successfully on {device}")
        
        # Test model with dummy input to ensure it works
        if gpu_available:
            print("Testing model with dummy input...")
            with torch.no_grad():
                dummy_input = torch.randn(1, 3, 224, 224).to(device)
                output = mobilenet_model(dummy_input)
                print(f"✓ Model test successful - output shape: {output.shape}")
        
        return True
        
    except Exception as e:
        print(f"Error loading PyTorch MobileNetV2 model: {e}")
        
        if "CUDA" in str(e) and gpu_available:
            print("GPU error detected, falling back to CPU...")
            try:
                # Fallback to CPU device
                cpu_device = torch.device('cpu')
                mobilenet_model = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)
                mobilenet_model.classifier = nn.Identity()
                mobilenet_model.eval()
                mobilenet_model = mobilenet_model.to(cpu_device)
                model_device = str(cpu_device)
                print(f"PyTorch MobileNetV2 model loaded successfully on CPU")
                return True
            except Exception as cpu_error:
                print(f"CPU fallback also failed: {cpu_error}")
        
        print("Continuing without AI model - AI comparison will be disabled")
        mobilenet_model = None
        model_device = None
        return False

def ai_extract_features_from_array(img_array):
    """Extract features using PyTorch MobileNetV2."""
    if not PYTORCH_AVAILABLE or mobilenet_model is None:
        print("PyTorch MobileNetV2 not available, falling back to OpenCV")
        return opencv_extract_features_from_array(img_array)
    
    try:
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        
        # Preprocess image
        input_tensor = preprocess(img_pil).unsqueeze(0)
        
        # Move tensor to the same device as the model
        if model_device and 'cuda' in model_device:
            input_tensor = input_tensor.to(device)
        else:
            input_tensor = input_tensor.to('cpu')
        
        # Extract features
        with torch.no_grad():
            features = mobilenet_model(input_tensor)
        
        return features.cpu().numpy().flatten()
    except Exception as e:
        print(f"PyTorch feature extraction error: {e}")
        print("Falling back to OpenCV features...")
        return opencv_extract_features_from_array(img_array)

def ai_predict(arr):
    """Predict using PyTorch MobileNetV2 model."""
    if not PYTORCH_AVAILABLE or mobilenet_model is None:
        print("Warning: PyTorch MobileNetV2 model not available, returning empty features")
        return np.array([])
    
    try:
        with mobilenet_predict_lock:
            # Convert numpy array to torch tensor
            if isinstance(arr, np.ndarray):
                tensor = torch.from_numpy(arr).float().to(device)
            else:
                tensor = arr.to(device)
            
            # Extract features
            with torch.no_grad():
                features = mobilenet_model(tensor)
        
        return features.cpu().numpy().flatten()
    except Exception as e:
        print(f"PyTorch prediction error: {e}")
        print("Falling back to OpenCV features...")
        return np.array([])

def opponent_sift_descriptors(img_bgr, nfeatures=256):
    """Extract SIFT descriptors using opponent color space."""
    # Convert to opponent color space
    if img_bgr.shape[2] == 4:
        img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_BGRA2BGR)
    b, g, r = cv2.split(img_bgr.astype(np.float32))
    O1 = (r - g) / np.sqrt(2)
    O2 = (r + g - 2 * b) / np.sqrt(6)
    O3 = (r + g + b) / np.sqrt(3)
    ops = [O1, O2, O3]

    try:
        sift = cv2.SIFT_create(nfeatures=nfeatures)
    except AttributeError:
        # Fallback for older OpenCV versions
        sift = cv2.xfeatures2d.SIFT_create(nfeatures=nfeatures)
    
    kp = sift.detect(np.nan_to_num(ops[2], nan=0, posinf=0, neginf=0).clip(0,255).astype(np.uint8), None)  # detect on intensity
    des_list = []
    for ch in ops:
        ch_clean = np.nan_to_num(ch, nan=0, posinf=0, neginf=0).clip(0,255).astype(np.uint8)
        _, des = sift.compute(ch_clean, kp)
        des_list.append(des)
    descriptors = np.hstack(des_list) if all(d is not None for d in des_list) else None
    return kp, descriptors

def opencv_extract_features_from_array(img_array):
    """Extract features using OpenCV methods (ORB/SIFT)."""
    # Convert to grayscale for feature extraction
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    
    # Use ORB (Oriented FAST and Rotated BRIEF) for feature extraction
    try:
        orb = cv2.ORB_create(nfeatures=256)
    except AttributeError:
        # Fallback for older OpenCV versions
        orb = cv2.ORB()
    
    keypoints, descriptors = opponent_sift_descriptors(img_array)
    
    # Fix: filter out None descriptors before stacking and mean
    if descriptors is not None:
        # If using opponent_sift_descriptors, descriptors may be a numpy array or None
        # If it's a numpy array, check for None rows (shouldn't happen, but be robust)
        if isinstance(descriptors, np.ndarray):
            # If all descriptors are None, fallback
            if descriptors.dtype == object:
                valid_des = [d for d in descriptors if d is not None]
                if valid_des:
                    feature_vector = np.vstack(valid_des).mean(axis=0)
                else:
                    feature_vector = np.zeros(32, dtype=np.float32)
            else:
                feature_vector = descriptors.mean(axis=0)
        else:
            # fallback: treat as no descriptors
            feature_vector = np.zeros(32, dtype=np.float32)
    else:
        feature_vector = np.zeros(32, dtype=np.float32)
    return feature_vector.flatten()

def extract_features_from_array(img_array, feature_method="mobilenet"):
    """Dispatch to the correct feature extraction method."""
    if feature_method == "mobilenet":
        if mobilenet_model is None and not initialize_mobilenet_model():
            print("Warning: MobileNetV2 model not available, falling back to OpenCV")
            return opencv_extract_features_from_array(img_array)
        return ai_extract_features_from_array(img_array)
    else:
        return opencv_extract_features_from_array(img_array)

def cosine_similarity(a, b):
    """Calculate cosine similarity between two feature vectors."""
    if norm(a) == 0 or norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (norm(a) * norm(b)))

def mse(imageA, imageB):
    """Calculate Mean Squared Error between two images."""
    return np.mean((imageA.astype("float") - imageB.astype("float")) ** 2)

def compute_ssim(grayA, grayB):
    """Calculate Structural Similarity Index between two grayscale images."""
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel)  # Use np.outer instead of @ for compatibility
    mu1 = cv2.filter2D(grayA.astype(np.float64), -1, window)[5:-5, 5:-5]
    mu2 = cv2.filter2D(grayB.astype(np.float64), -1, window)[5:-5, 5:-5]
    mu1_sq, mu2_sq, mu1_mu2 = mu1**2, mu2**2, mu1 * mu2
    sigma1_sq = cv2.filter2D((grayA**2).astype(np.float64), -1, window)[5:-5,5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D((grayB**2).astype(np.float64), -1, window)[5:-5,5:-5] - mu2_sq
    sigma12   = cv2.filter2D((grayA*grayB).astype(np.float64), -1, window)[5:-5,5:-5] - mu1_mu2
    num = (2*mu1_mu2 + C1) * (2*sigma12 + C2)
    den = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
    ssim_map = num / den
    return ssim_map.mean()

def normalize_illumination(img):
    """Normalize illumination using CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    # Denoise before illumination normalization
    img_denoised = cv2.fastNlMeansDenoisingColored(img, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)
    return img_denoised
