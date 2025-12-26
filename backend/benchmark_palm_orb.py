
import os
import sys
import glob
import cv2
import numpy as np
import random
import statistics

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.palm_service import PalmService

def benchmark_orb():
    print("[-] Initializing PalmService (AKAZE)...")
    service = PalmService()
    
    dataset_path = "/home/red/Documents/S5/Biom Sec/Project/LUTBIO sample data"
    
    # 1. Collect Data
    users = {}
    user_dirs = sorted([d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))])
    
    count = 0
    path_list = []
    
    # Load all palm images
    for uid in user_dirs:
        p_paths = []
        touch = os.path.join(dataset_path, uid, "palm_touch")
        
        if os.path.exists(touch):
            p_paths.extend(glob.glob(os.path.join(touch, "*")))
        
        if len(p_paths) > 0:
            users[uid] = p_paths
            count += len(p_paths)
            path_list.extend(p_paths)
            
    print(f"[-] Found {len(users)} users with {count} palm images.")
    
    # 2. Pre-Calculate Templates
    print("[-] Creating Templates...")
    templates = {} # path -> json_string
    
    for p in path_list:
        with open(p, "rb") as f:
            b = f.read()
        tpl = service.create_template(b)
        if tpl:
            templates[p] = {"tpl": tpl, "uid": None}
            # Find uid owner
            for uid, paths in users.items():
                if p in paths:
                    templates[p]["uid"] = uid
                    break
    
    print(f"[-] Created {len(templates)} valid templates.")

    # 3. Matching
    genuine_scores = []
    impostor_scores = []
    
    # Genuine (Same UID)
    from itertools import combinations
    gen_pairs = 0
    imp_pairs = 0
    
    print("[-] Matching Genuine Pairs...")
    for uid in users:
        user_paths = [p for p in users[uid] if p in templates]
        # Match every pair
        for p1, p2 in combinations(user_paths, 2):
            # Verify p1 against p2's template
            with open(p1, "rb") as f:
                b1 = f.read()
            
            is_match, score, msg = service.verify(b1, templates[p2]["tpl"])
            genuine_scores.append(score)
            gen_pairs += 1
            
    print(f"    Tested {gen_pairs} genuine pairs.")

    print("[-] Matching Imposter Pairs (Random Sample)...")
    # Imposter
    for _ in range(500):
        p1 = random.choice(path_list)
        p2 = random.choice(path_list)
        
        if p1 not in templates or p2 not in templates: continue
        
        if templates[p1]["uid"] == templates[p2]["uid"]:
            continue
            
        with open(p1, "rb") as f:
            b1 = f.read()
            
        is_match, score, msg = service.verify(b1, templates[p2]["tpl"])
        impostor_scores.append(score)
        imp_pairs += 1
        
    print(f"    Tested {imp_pairs} imposter pairs.")
    
    # 4. Analysis
    if not genuine_scores or not impostor_scores:
        print("Not enough data.")
        return

    g_mean = statistics.mean(genuine_scores)
    i_mean = statistics.mean(impostor_scores)
    i_max = max(impostor_scores)
    g_min = min(genuine_scores)
    
    print("\n--- RESULTS (Keypoint Matches) ---")
    print(f"Genuine Mean:  {g_mean:.2f} (Min: {g_min})")
    print(f"Imposter Mean: {i_mean:.2f} (Max: {i_max})")
    
    # Determine Optimal Threshold
    # We want Threshold > i_max
    suggested = int(i_max * 1.5) + 5
    if suggested > g_mean:
        suggested = int((g_mean + i_max) / 2) # Middle ground
        
    print(f"Current Threshold: 15")
    print(f"Imposter Max is {i_max}. If 15 < {i_max}, then FAR > 0.")
    print(f"Suggested Threshold: {suggested}")

if __name__ == "__main__":
    benchmark_orb()
