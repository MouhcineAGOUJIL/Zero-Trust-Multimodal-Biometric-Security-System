
import os
import sys
import numpy as np
import random
import glob
from itertools import combinations
import statistics

# Add current directory to path
sys.path.append(os.getcwd())

from backend.services.biometric import BiometricService

def run_benchmark():
    print("[*] Initializing Biometric Service...")
    bs = BiometricService()
    
    dataset_path = "/home/red/Documents/S5/Biom Sec/Project/LUTBIO sample data"
    users = {}
    
    print(f"[*] Loading dataset from {dataset_path}...")
    
    # Load Data
    user_dirs = sorted([d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))])
    
    total_images = 0
    for uid in user_dirs:
        face_path = os.path.join(dataset_path, uid, "face")
        if not os.path.exists(face_path):
            continue
            
        images = glob.glob(os.path.join(face_path, "*.jpg"))
        if len(images) > 0:
            users[uid] = images
            total_images += len(images)
            
    print(f"[*] Found {len(users)} users with {total_images} face images.")
    
    # Generate Embeddings Cache
    print("[*] extracting features (this may take a while)...")
    embeddings = {} # path -> feature_vector
    
    for uid, img_paths in users.items():
        for path in img_paths:
            try:
                with open(path, "rb") as f:
                    img_bytes = f.read()
                    feats = bs.extract_features_from_buffer(img_bytes)
                    if feats is not None:
                        embeddings[path] = feats
            except Exception as e:
                print(f"Error processing {path}: {e}")

    print(f"[*] Successfully extracted features for {len(embeddings)} images.")

    # Comparisons
    genuine_scores_biohash = []
    genuine_scores_euclidean = []
    impostor_scores_biohash = []
    impostor_scores_euclidean = []
    
    user_ids = list(users.keys())
    
    # Helper for comparison
    seed_token = 123456 # Fixed seed for consistency
    
    print("[*] Running comparisons...")
    
    # 1. Genuine Pairs (Same User)
    for uid in user_ids:
        user_imgs = [p for p in users[uid] if p in embeddings]
        if len(user_imgs) < 2:
            continue
            
        for img1, img2 in combinations(user_imgs, 2):
            feat1 = embeddings[img1]
            feat2 = embeddings[img2]
            
            # BioHash
            h1 = bs.generate_biohash(feat1, seed_token, hash_length=256)
            h2 = bs.generate_biohash(feat2, seed_token, hash_length=256)
            _, dist_bh = bs.match_biohashes(h1, h2, threshold=1.0) # threshold=1 to just get score
            genuine_scores_biohash.append(dist_bh)
            
            # Euclidean
            dist_euc = np.linalg.norm(feat1 - feat2)
            genuine_scores_euclidean.append(dist_euc)

    # 2. Impostor Pairs (Different Users)
    # Randomly sample impostor pairs to avoid O(N^2) explosion
    num_impostor_pairs = 2000 
    
    for _ in range(num_impostor_pairs):
        u1, u2 = random.sample(user_ids, 2)
        
        imgs1 = [p for p in users[u1] if p in embeddings]
        imgs2 = [p for p in users[u2] if p in embeddings]
        
        if not imgs1 or not imgs2: 
            continue
            
        img1 = random.choice(imgs1)
        img2 = random.choice(imgs2)
        
        feat1 = embeddings[img1]
        feat2 = embeddings[img2]
        
        # BioHash
        h1 = bs.generate_biohash(feat1, seed_token, hash_length=256)
        h2 = bs.generate_biohash(feat2, seed_token, hash_length=256)
        _, dist_bh = bs.match_biohashes(h1, h2, threshold=1.0)
        impostor_scores_biohash.append(dist_bh)
        
        # Euclidean
        dist_euc = np.linalg.norm(feat1 - feat2)
        impostor_scores_euclidean.append(dist_euc)

    # Analysis
    def analyze(name, gen, imp, threshold=None):
        print(f"\n--- {name} Analysis ---")
        print(f"Genuine Pairs: {len(gen)}")
        print(f"Impostor Pairs: {len(imp)}")
        
        mean_gen = statistics.mean(gen) if gen else 0
        mean_imp = statistics.mean(imp) if imp else 0
        
        print(f"Mean Genuine Dist: {mean_gen:.4f} (Lower is better)")
        print(f"Mean Impostor Dist: {mean_imp:.4f} (Higher is better)")
        print(f"Separation: {mean_imp - mean_gen:.4f}")
        
        if threshold:
            frr = sum(1 for x in gen if x > threshold) / len(gen) if gen else 0
            far = sum(1 for x in imp if x <= threshold) / len(imp) if imp else 0
            print(f"\nAt Threshold {threshold}:")
            print(f"FAR (False Accept): {far*100:.2f}%")
            print(f"FRR (False Reject): {frr*100:.2f}%")

    print("\n--- BioHash Threshold Sweep ---")
    for t in [0.05, 0.08, 0.10, 0.11, 0.12, 0.13, 0.15]:
        frr = sum(1 for x in genuine_scores_biohash if x > t) / len(genuine_scores_biohash) if genuine_scores_biohash else 0
        far = sum(1 for x in impostor_scores_biohash if x <= t) / len(impostor_scores_biohash) if impostor_scores_biohash else 0
        print(f"Thresh {t:.2f} | FAR: {far*100:.2f}% | FRR: {frr*100:.2f}%")

    print("\n--- Euclidean Threshold Sweep ---")
    for t in [0.3, 0.35, 0.4, 0.45, 0.5, 0.6]:
        frr = sum(1 for x in genuine_scores_euclidean if x > t) / len(genuine_scores_euclidean) if genuine_scores_euclidean else 0
        far = sum(1 for x in impostor_scores_euclidean if x <= t) / len(impostor_scores_euclidean) if impostor_scores_euclidean else 0
        print(f"Thresh {t:.2f} | FAR: {far*100:.2f}% | FRR: {frr*100:.2f}%")

if __name__ == "__main__":
    run_benchmark()
