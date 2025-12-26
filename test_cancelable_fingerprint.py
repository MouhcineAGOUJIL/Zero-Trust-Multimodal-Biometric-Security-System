import os
import glob
import itertools
from collections import defaultdict
import numpy as np
from backend.services.cnn_service import CNNService
from backend.services.biometric import BiometricService

# Configuration
DB_PATH = "/home/red/Documents/S5/Biom Sec/DB2_B"

def load_dataset(path):
    print(f"Loading dataset from {path}...")
    files = sorted(glob.glob(os.path.join(path, "*.tif")))
    user_data = defaultdict(list)
    for f in files:
        basename = os.path.basename(f)
        try:
            parts = basename.split('_')
            user_id = parts[0]
            user_data[user_id].append(f)
        except:
            pass
    print(f"Found {len(user_data)} users.")
    return user_data

def run_cancelable_test():
    try:
        cnn = CNNService() # 1280-dim
        bio = BiometricService() # For BioHashing
    except Exception as e:
        print(f"Failed to load services: {e}")
        return

    dataset = load_dataset(DB_PATH)
    users = sorted(list(dataset.keys()))
    
    # 1. Extract Features
    print("Extracting CNN Features...")
    # Structure: cache[uid][sample_idx] = feature_vector
    cache = defaultdict(list)
    
    # Count total samples
    total_imgs = sum(len(v) for v in dataset.values())
    print(f"Total images to process: {total_imgs}")

    for uid in users:
        files = dataset[uid]
        for f in files:
            feats = cnn.extract_features(f)
            if feats is not None:
                cache[uid].append(feats)
                
    print(f"Extracted features for {len(cache)} users.")

    if not cache:
        print("No features extracted. Exiting.")
        return

    # 2. Performance Test (Standard Authentication)
    # Token is FIXED per user (Simulating enrolled state)
    print("\n--- PERFORMANCE TEST (Fixed Token) ---")
    gen_scores = []
    imp_scores = []
    
    user_tokens = {uid: hash(uid) % 100000 for uid in users}
    
    # Genuine (Same User, Same Token, Diff Sample)
    print("Running Genuine Matches...")
    for uid in users:
        samples = cache[uid]
        token = user_tokens[uid]
        # Generate Hashes
        hashes = [bio.generate_biohash(f, token) for f in samples]
        
        for h1, h2 in itertools.combinations(hashes, 2):
            match, dist = bio.match_biohashes(h1, h2)
            gen_scores.append(dist) # Store Distance (lower is better for Hamming)

    # Imposter (Diff User, Target's Token)
    # Scenario: Stolen Token Attack. Attacker uses their own biometric + Target's Token.
    print("Running Imposter Matches (Stolen Token Scenario)...") 
    for i, target_uid in enumerate(users):
        target_token = user_tokens[target_uid]
        target_samples = cache[target_uid]
        if not target_samples: continue
        
        # Target Template (Hash of Sample 0)
        target_hash = bio.generate_biohash(target_samples[0], target_token)
        
        for attacker_uid in users:
            if attacker_uid == target_uid: continue
            attacker_samples = cache[attacker_uid]
            if not attacker_samples: continue
            
            # Attacker uses their finger + Target's Token
            attacker_feat = attacker_samples[0]
            attacker_hash = bio.generate_biohash(attacker_feat, target_token)
            
            match, dist = bio.match_biohashes(target_hash, attacker_hash)
            imp_scores.append(dist)

    # Stats
    # BioHash is a binary string. 128 bits.
    # Hamming Distance varies from 0.0 to 1.0.
    # 0.5 means Uncorrelated.
    # < 0.2 means Match (usually).
    
    thresholds = [0.10, 0.15, 0.20, 0.25, 0.30]
    
    print("\nResults:")
    if gen_scores:
        print(f"Genuine Mean Hamming Dist: {np.mean(gen_scores):.3f} (Lower is Better)")
    if imp_scores:
        print(f"Imposter Mean Hamming Dist: {np.mean(imp_scores):.3f} (Ideally ~0.5)")

    if gen_scores and imp_scores:
        print("-" * 40)
        print(f"{'Threshold':<10} | {'FAR (%)':<10} | {'FRR (%)':<10} | {'ACC (%)':<10}")
        print("-" * 40)
        for t in thresholds:
            far = sum(1 for s in imp_scores if s <= t) / len(imp_scores)
            frr = sum(1 for s in gen_scores if s > t) / len(gen_scores)
            acc = ((1-far) + (1-frr)) / 2
            print(f"{t:<10.2f} | {far*100:<10.2f} | {frr*100:<10.2f} | {acc*100:<10.2f}")
        print("-" * 40)

    # 3. Cancelability Test (Revocability)
    # Compare: Same Finger + Token A  vs  Same Finger + Token B
    # Should be Uncorrelated (Distance ~0.5)
    print("\n--- CANCELABILITY TEST (Revocability) ---")
    revocability_scores = []
    
    for uid in users:
        samples = cache[uid]
        if not samples: continue
        feat = samples[0] # Use first sample
        
        token_a = 12345
        token_b = 67890
        
        h1 = bio.generate_biohash(feat, token_a)
        h2 = bio.generate_biohash(feat, token_b)
        
        match, dist = bio.match_biohashes(h1, h2)
        revocability_scores.append(dist)
        
    if revocability_scores:
        rev_mean = np.mean(revocability_scores)
        print(f"Revocability Mean Dist: {rev_mean:.3f}")
        print("(Target: ~0.5. If close to 0.5, tokens provide perfect separation.)")
        
        if 0.45 <= rev_mean <= 0.55:
            print("[SUCCESS] New keys effectively cancel old keys.")
        else:
            print("[WARNING] Keys are correlated!")

if __name__ == "__main__":
    run_cancelable_test()
