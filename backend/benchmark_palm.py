
import os
import sys
import glob
import cv2
import numpy as np
import random
import statistics
import matplotlib.pyplot as plt

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.cnn_service import CNNService
from backend.services.iom_service import IoMService

def benchmark_palm():
    print("[-] Initializing Services...")
    # CNN Service (will print if it loads generic ImageNet or Siamese)
    cnn = CNNService() 
    cnn.reload_model(force_imagenet=True) # TEST: Force ImageNet for Palm
    iom = IoMService(key_len=256)
    
    dataset_path = "/home/red/Documents/S5/Biom Sec/Project/LUTBIO sample data"
    
    # 1. Collect Data
    users = {}
    user_dirs = sorted([d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))])
    
    count = 0
    for uid in user_dirs:
        # Check both touch and touchless
        p_paths = []
        touch = os.path.join(dataset_path, uid, "palm_touch")
        touchless = os.path.join(dataset_path, uid, "plam_touchless") # Note typo in dir name 'plam'
        
        if os.path.exists(touch):
            p_paths.extend(glob.glob(os.path.join(touch, "*")))
        
        # Taking only touch for now to be consistent? Or mixing?
        # Let's verify 'palm_touch' primarily as described in logic
        
        if len(p_paths) > 0:
            users[uid] = p_paths
            count += len(p_paths)
            
    print(f"[-] Found {len(users)} users with {count} palm images.")
    
    # 2. Visualization of Preprocessing
    # Let's grab one image and run the INTERNAL preprocessing of CNNService to see what it does
    if len(users) > 0:
        first_uid = list(users.keys())[0]
        test_img_path = users[first_uid][0]
        
        img = cv2.imread(test_img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Replicate CNNService logic
        ridges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 5)
        
        # Save for review
        cv2.imwrite("debug_palm_preprocessed.png", ridges)
        print("[-] Saved 'debug_palm_preprocessed.png' to check if features are destroyed.")

    # 3. Computing Features
    print("[-] Extracting Features & Hashes...")
    templates = {} # path -> hash
    
    # Dummy seed
    seed = 12345
    
    path_list = []
    
    for uid, paths in users.items():
        for p in paths:
            # Read bytes
            with open(p, "rb") as f:
                b = f.read()
            
            # Extract Palm features WITHOUT ridge enhancement
            feat = cnn.extract_features(b, enhance_ridges=False)
            if feat is not None:
                h = iom.generate_iom_hash(feat, seed)
                templates[p] = {"hash": h, "uid": uid}
                path_list.append(p)
                
    print(f"[-] Extracted {len(templates)} templates.")
    
    # 4. Matching logic
    genuine_scores = []
    impostor_scores = []
    
    # Genuine (Same UID)
    from itertools import combinations
    
    for uid in users:
        user_paths = [p for p in users[uid] if p in templates]
        for p1, p2 in combinations(user_paths, 2):
            h1 = templates[p1]["hash"]
            h2 = templates[p2]["hash"]
            is_match, score = iom.match_iom(h1, h2)
            genuine_scores.append(score)
            
    # Imposter (Different UID)
    # Random sample 1000 pairs
    for _ in range(1000):
        p1 = random.choice(path_list)
        p2 = random.choice(path_list)
        
        if templates[p1]["uid"] == templates[p2]["uid"]:
            continue
            
        h1 = templates[p1]["hash"]
        h2 = templates[p2]["hash"]
        is_match, score = iom.match_iom(h1, h2)
        impostor_scores.append(score)
        
    print("\n--- RESULTS ---")
    if genuine_scores:
        print(f"Genuine Mean: {statistics.mean(genuine_scores):.4f}")
    if impostor_scores:
        print(f"Imposter Mean: {statistics.mean(impostor_scores):.4f}")
        
    # Check "Everything Granted" hypothesis
    # If Imposter Mean is > 0.65, then system accepts everyone
    print(f"Current Threshold: 0.65")
    
    far_count = sum(1 for s in impostor_scores if s > 0.65)
    print(f"False Accepts (FAR): {far_count}/{len(impostor_scores)} ({far_count/len(impostor_scores)*100:.2f}%)")

if __name__ == "__main__":
    benchmark_palm()
