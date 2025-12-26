import os
import glob
import numpy as np
import cv2
import itertools
from collections import defaultdict
from backend.services.cnn_service import CNNService
from backend.services.biometric import BiometricService

# Configuration
DATASET_ROOT = "/home/red/Documents/S5/Biom Sec/Project/LUTBIO sample data"

def load_lutbio_data(root_path, max_users=20):
    print(f"Scanning {root_path}...")
    user_dirs = sorted([d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))])
    
    if max_users:
        user_dirs = user_dirs[:max_users]
        
    dataset = {}
    
    for uid in user_dirs:
        u_path = os.path.join(root_path, uid)
        dataset[uid] = {
            'face': sorted(glob.glob(os.path.join(u_path, "face", "*.*"))),
            'finger': sorted(glob.glob(os.path.join(u_path, "finger", "*.*"))),
            'palm': sorted(glob.glob(os.path.join(u_path, "palm_touch", "*.*")))
        }
        
    print(f"Found {len(dataset)} users.")
    return dataset

def test_modality(modality_name, dataset, extractor_func):
    print(f"\n--- Testing Modality: {modality_name} ---")
    
    # Extract Features
    encodings = defaultdict(list)
    users = sorted(dataset.keys())
    
    print("Extracting features...")
    count = 0
    for uid in users:
        files = dataset[uid].get(modality_name, [])
        for f in files:
            feat = extractor_func(f)
            if feat is not None:
                encodings[uid].append(feat)
                count += 1
    print(f"Extracted {count} templates.")
    
    if count < 2:
        print("Not enough data.")
        return

    # Metrics
    gen_scores = []
    imp_scores = []
    
    # Genuine
    for uid in users:
        samples = encodings[uid]
        if len(samples) < 2: continue
        for s1, s2 in itertools.combinations(samples, 2):
            score = np.linalg.norm(s1 - s2)
            gen_scores.append(score)
            
    # Imposter
    users_with_data = [u for u in users if encodings[u]]
    for i, target in enumerate(users_with_data):
        target_feat = encodings[target][0]
        for j, attacker in enumerate(users_with_data):
            if i >= j: continue 
            attacker_feat = encodings[attacker][0]
            
            score = np.linalg.norm(target_feat - attacker_feat)
            imp_scores.append(score)
            
    if not gen_scores:
        print("No genuine pairs found.")
        return

    gen_mean = np.mean(gen_scores)
    imp_mean = np.mean(imp_scores)
    
    print(f"Genuine Mean Dist: {gen_mean:.3f}")
    print(f"Imposter Mean Dist: {imp_mean:.3f}")
    
    # EER / Best Acc
    best_acc = 0
    best_thresh = 0
    # Search range appropriate for Euclidean distances
    thresholds = np.linspace(0, 2.0, 100)
    
    for t in thresholds:
        frr = sum(1 for s in gen_scores if s > t) / len(gen_scores)
        far = sum(1 for s in imp_scores if s <= t) / len(imp_scores)
        acc = ((1-far) + (1-frr)) / 2
        
        if acc > best_acc:
            best_acc = acc
            best_thresh = t
            
    print(f"Best Accuracy: {best_acc*100:.2f}% at Threshold {best_thresh:.3f}")

def run_multimodal_test():
    print("Loading Services...")
    try:
        bio = BiometricService() # Face
        cnn = CNNService() # Finger, Palm
    except Exception as e:
        print(f"Error loading services: {e}")
        return

    data = load_lutbio_data(DATASET_ROOT)
    
    # 1. Test Face
    def face_extractor(path):
        with open(path, 'rb') as f:
            b = f.read()
        return bio.extract_features_from_buffer(b)
        
    test_modality('face', data, face_extractor)
    
    # 2. Test Finger (Siamese CNN)
    test_modality('finger', data, cnn.extract_features)
    
    # 3. Test Palm (Siamese CNN - Transfer Learning Check)
    test_modality('palm', data, cnn.extract_features)

if __name__ == "__main__":
    run_multimodal_test()
