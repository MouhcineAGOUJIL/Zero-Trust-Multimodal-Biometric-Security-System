import numpy as np
import dlib
import cv2
import argparse
import os
import sys

# Constants for model paths
SHAPE_PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
FACE_RECOGNITION_MODEL_PATH = "dlib_face_recognition_resnet_model_v1.dat"

# Initialize dlib models globally to avoid reloading
try:
    if os.path.exists(SHAPE_PREDICTOR_PATH) and os.path.exists(FACE_RECOGNITION_MODEL_PATH):
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
        face_rec = dlib.face_recognition_model_v1(FACE_RECOGNITION_MODEL_PATH)
        MODELS_LOADED = True
    else:
        print("[-] Dlib models not found in current directory. Feature extraction will fail.")
        MODELS_LOADED = False
except Exception as e:
    print(f"[-] Error loading dlib models: {e}")
    MODELS_LOADED = False

def extract_face_features(image_path):
    """
    Extracts the 128-dimensional face encoding from an image using dlib directly.
    Returns None if no face is found.
    """
    if not MODELS_LOADED:
        print("Error: Models not loaded.")
        return None

    try:
        if not os.path.exists(image_path):
            print(f"Error: Image file not found at {image_path}")
            return None
            
        # Load image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Could not read image {image_path}")
            return None
            
        # Convert to RGB (dlib expects RGB)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        dets = detector(rgb_img, 1)
        
        if len(dets) > 0:
            # Prepare shape predictor (just first face)
            shape = predictor(rgb_img, dets[0])
            
            # Compute face descriptor
            face_descriptor = face_rec.compute_face_descriptor(rgb_img, shape)
            
            # Convert dlib vector to numpy array
            return np.array(face_descriptor)
        else:
            print(f"Warning: No face detected in {image_path}")
            return None
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def generate_biohash(feature_vector, token_seed, hash_length=128):
    """
    Generates a BioHash (Cancelable Template) from a feature vector.
    
    Args:
        feature_vector (np.array): The original biometric feature vector (e.g., 128d face encoding).
        token_seed (int): The user-specific secret seed (the "Token").
        hash_length (int): The length of the resulting binary hash.
        
    Returns:
        np.array: A binary array (0s and 1s) representing the protected template.
    """
    # 1. Seed the random number generator to ensure reproducibility for the same token
    np.random.seed(token_seed)
    
    # 2. Generate a random orthogonal projection matrix consisting of normally distributed numbers
    # The shape should be (len(feature), hash_length)
    feature_len = len(feature_vector)
    projection_matrix = np.random.randn(feature_len, hash_length)
    
    # 3. Orthogonalize the matrix (Optional but recommended for better separation)
    # Using QR decomposition to get an orthonormal matrix
    q, _ = np.linalg.qr(projection_matrix)
    # If the feature length < hash_length, QR returns (feature_len, feature_len), 
    # so often we just use the random matrix directly if standard orthonormalization isn't trivial for those dims.
    # For simplicity and standard BioHashing, a pseudo-random projection is often sufficient.
    # We will stick to the random projection directly for this PoC to strictly follow standard BioHashing.
    
    # 4. Project the feature vector onto the random basis
    # Result = vector . matrix
    projected_vector = np.dot(feature_vector, projection_matrix)
    
    # 5. Thresholding / Binarization
    # We use 0 as the threshold (typical for zero-mean random projections)
    biohash = (projected_vector > 0).astype(int)
    
    return biohash

def match_biohash(hash1, hash2):
    """
    Calculates the normalized Hamming Distance between two BioHashes.
    Result is between 0.0 (Identical) and 1.0 (Completely different).
    """
    if len(hash1) != len(hash2):
        raise ValueError("BioHashes must be of the same length")
    
    # Hamming distance: proportion of positions at which the corresponding symbols are different
    distance = np.count_nonzero(hash1 != hash2) / len(hash1)
    return distance

def main():
    parser = argparse.ArgumentParser(description="Multimodal Zero Trust - BioHashing PoC")
    parser.add_argument("--img1", required=True, help="Path to first image")
    parser.add_argument("--img2", required=True, help="Path to second image")
    parser.add_argument("--seed1", type=int, default=42, help="Token/Seed for first image (default: 42)")
    parser.add_argument("--seed2", type=int, default=42, help="Token/Seed for second image (default: 42)")
    
    args = parser.parse_args()
    
    print("-" * 50)
    print(" >>> BioHashing Proof of Concept <<<")
    print("-" * 50)
    
    # Step 1: Extract Features
    print(f"[*] Extracting features from {args.img1}...")
    feat1 = extract_face_features(args.img1)
    
    print(f"[*] Extracting features from {args.img2}...")
    feat2 = extract_face_features(args.img2)
    
    if feat1 is None or feat2 is None:
        print("[-] Error: Could NOT extract features from one or both images.")
        sys.exit(1)
        
    print("[+] Features extracted successfully.")
    print(f"    Feature Vector Length: {len(feat1)}")
    
    # Step 2: Generate BioHashes
    print(f"[*] Generating BioHash for Img1 with Seed {args.seed1}...")
    hash1 = generate_biohash(feat1, args.seed1)
    
    print(f"[*] Generating BioHash for Img2 with Seed {args.seed2}...")
    hash2 = generate_biohash(feat2, args.seed2)
    
    # Step 3: Match
    dist = match_biohash(hash1, hash2)
    
    # Debug: Check original Euclidean distance
    euc_dist = np.linalg.norm(feat1 - feat2)
    
    print("-" * 50)
    print(f"Original Euclidean Distance: {euc_dist:.4f}")
    if euc_dist > 0.6:
        print("(Dlib considers this DIFFERENT people)")
    else:
        print("(Dlib considers this SAME person (threshold 0.6))")

    print("-" * 50)
    print(f"BioHash 1 (first 16 bits): {hash1[:16]}...")
    print(f"BioHash 2 (first 16 bits): {hash2[:16]}...")
    print("-" * 50)
    print(f"HAMMING DISTANCE: {dist:.4f}")
    print("-" * 50)
    
    # Decision Threshold (Typical is around 0.2 - 0.3 for BioHashing, depending on setup)
    # Adjusted to 0.15 based on dlib ResNet model behavior on this dataset
    THRESHOLD = 0.15
    if dist < THRESHOLD:
        print(">>> RESULT: MATCH ACCEPTED ✅")
    else:
        print(">>> RESULT: MATCH REJECTED ❌")
        
    # Analysis
    if args.img1 == args.img2 and args.seed1 == args.seed2:
        print("(Note: Same image + Same seed should be 0.0)")
    elif args.img1 == args.img2 and args.seed1 != args.seed2:
        print("(Note: Same image + Different seed simulates REVOCATION. Should be ~0.5)")
    elif args.img1 != args.img2 and args.seed1 == args.seed2:
        print("(Note: Different people + Same seed should be > 0.3)")

if __name__ == "__main__":
    main()
