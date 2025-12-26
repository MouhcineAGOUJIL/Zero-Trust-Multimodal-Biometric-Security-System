import os
import glob
import itertools
from collections import defaultdict
import numpy as np
from backend.services.iom_service import IoMService
from backend.fingerprint_core import FingerprintCore
from backend.services.fingerprint_proxy import FingerprintProxy
import os
import glob
import itertools

# Configuration
DB_PATH = "/home/red/Documents/S5/Biom Sec/DB2_B"
LIMIT_users = 10 # Limit number of users for speed if needed (set None for all)
LIMIT_samples = 8 # Ensure we process up to 8 per user as specified

def load_dataset(path):
    print(f"Loading dataset from {path}...")
    files = sorted(glob.glob(os.path.join(path, "*.tif")))
    
    # Group by User ID
    # Filename format expected: 101_1.tif, 101_2.tif, ...
    user_data = defaultdict(list)
    
    for f in files:
        basename = os.path.basename(f)
        try:
            parts = basename.split('_')
            user_id = parts[0]
            # sample_id = parts[1].split('.')[0]
            user_data[user_id].append(f)
        except:
            print(f"Skipping file with unknown format: {basename}")
            
    print(f"Found {len(user_data)} users.")
    return user_data

def align_minutiae(source_pts, target_pts, core):
    """
    Align source_pts TO target_pts using FingerprintCore's geometric matching.
    Returns: Aligned source_pts (list of dicts)
    """
    # 1. Get Matching Transform
    # core.match_fingerprints(target, source) -> checks how well Source fits Target
    # Note: match_fingerprints aligns param2 (min2) to param1 (min1)
    # So we call match_fingerprints(target, source)
    score, transform = core.match_fingerprints(target_pts, source_pts)
    
    if not transform:
        return source_pts # Failed to align, return original
        
    rot_deg, c_target, c_source = transform
    
    # 2. Apply Rotation
    # IoM handles translation (centering), so we only care about rotating Source 
    # around its own centroid to match Target's orientation.
    # The transform gave us 'rot_deg' which is the rotation of Source to match Target.
    
    rot_rad = np.deg2rad(rot_deg)
    cos_t, sin_t = np.cos(rot_rad), np.sin(rot_rad)
    
    aligned_pts = []
    
    # Calculate source centroid manually to rotate around it
    # (or use c_source provided by transform if accurate)
    cx = c_source[0]
    cy = c_source[1]
    
    for p in source_pts:
        # Center
        x = p['x'] - cx
        y = p['y'] - cy
        
        # Rotate
        rx = x * cos_t - y * sin_t
        ry = x * sin_t + y * cos_t
        
        # De-center (Back to original coordinate space? Or keep centered?)
        # IoM re-centers anyway. Let's shift back to absolute just in case IoM logic changes.
        final_x = rx + cx
        final_y = ry + cy
        
        aligned_pts.append({
            'x': final_x,
            'y': final_y,
            'angle': p['angle'] + rot_deg # Update local angle too
        })
        
    return aligned_pts

from backend.services.cnn_service import CNNService

# ... imports ...

def run_performance_test():
    try:
        cnn = CNNService() # Singleton
    except Exception as e:
        print(f"Failed to load CNN: {e}")
        return
        
    iom_service = IoMService(key_len=256)
    
    dataset = load_dataset(DB_PATH)
    users = sorted(list(dataset.keys()))
    
    # Cache Features (CNN Embeddings)
    cache = defaultdict(dict)
    
    print("Extracting CNN Features...")
    valid_samples_count = 0
    user_tokens = {uid: hash(uid) % 100000 for uid in users}
    
    for uid in users:
        samples = dataset[uid]
        for f_path in samples:
            # CNN Service handles loading from path
            feats = cnn.extract_features(f_path)
            
            if feats is not None:
                # Store Embedding
                cache[uid][f_path] = {'features': feats}
                valid_samples_count += 1
    
    print(f"Processed {valid_samples_count} valid samples.")
    
    genuine_scores = []
    imposter_scores = []
    
    # GENUINE MATCHES
    print("Running Genuine Matches (CNN Embeddings)...")
    for uid in users:
        samples = list(cache[uid].values())
        token = user_tokens[uid]
        
        # Pairwise
        for s1, s2 in itertools.combinations(samples, 2):
            f1 = s1['features']
            f2 = s2['features']
            
            # Hash
            h1 = iom_service.generate_iom_hash(f1, token)
            h2 = iom_service.generate_iom_hash(f2, token)
            
            match, score = iom_service.match_iom(h1, h2)
            genuine_scores.append(score)

    # IMPOSTER MATCHES
    print("Running Imposter Matches (CNN Embeddings)...")
    users_list = list(cache.keys())
    for i, target_uid in enumerate(users_list):
        if not cache[target_uid]: continue
        target_sample = list(cache[target_uid].values())[0]
        t_feats = target_sample['features']
        token = user_tokens[target_uid]
        
        # Hash Template
        h_template = iom_service.generate_iom_hash(t_feats, token)
        
        for attacker_uid in users_list:
            if attacker_uid == target_uid: continue
            if not cache[attacker_uid]: continue
            
            # Take one attacker sample
            attacker_sample = list(cache[attacker_uid].values())[0]
            a_feats = attacker_sample['features']
            
            # Hash Attacker with Target Token
            h_attacker = iom_service.generate_iom_hash(a_feats, token)
            
            match, score = iom_service.match_iom(h_template, h_attacker)
            imposter_scores.append(score)
            
    # Results
    if not genuine_scores or not imposter_scores:
        print("Not enough data for stats.")
        return

    gen_mean = np.mean(genuine_scores)
    imp_mean = np.mean(imposter_scores)
    
    threshold = 0.65
    frr = sum(1 for s in genuine_scores if s <= threshold) / len(genuine_scores)
    far = sum(1 for s in imposter_scores if s > threshold) / len(imposter_scores)
    
    print("\n" + "="*30)
    print("IoM Performance Report (CNN-Based)")
    print("="*30)
    print(f"Total Users: {len(users)}")
    print(f"Genuine Comparisons: {len(genuine_scores)}")
    print(f"Imposter Comparisons: {len(imposter_scores)}")
    print(f"Threshold: {threshold}")
    print("-" * 20)
    print(f"Genuine Scores: Mean={gen_mean:.3f}, Min={min(genuine_scores):.3f}, Max={max(genuine_scores):.3f}")
    print(f"Imposter Scores: Mean={imp_mean:.3f}, Min={min(imposter_scores):.3f}, Max={max(imposter_scores):.3f}")
    print("-" * 20)
    print(f"FRR (False Rejection Rate):  {frr*100:.2f}%")
    print(f"ACC (Accuracy):              {((1-far)+(1-frr))/2 * 100:.2f}%")
    
    # ---------------------------------------------------------
    # RAW EMBEDDING MATCHING (Euclidean Distance Validation)
    # ---------------------------------------------------------
    # Since we fine-tuned with Triplet Loss (Euclidean), checking raw distance
    # confirms if the model learned anything, regardless of IoM.
    
    raw_gen_dists = []
    raw_imp_dists = []
    
    # Genuine
    for uid in users:
        samples = list(cache[uid].values())
        for s1, s2 in itertools.combinations(samples, 2):
            d = np.linalg.norm(s1['features'] - s2['features'])
            raw_gen_dists.append(d)
            
    # Imposter
    users_list = list(cache.keys())
    for i, target_uid in enumerate(users_list):
        if not cache[target_uid]: continue
        t_feats = list(cache[target_uid].values())[0]['features']
        for attacker_uid in users_list:
            if attacker_uid == target_uid: continue
            if not cache[attacker_uid]: continue
            a_feats = list(cache[attacker_uid].values())[0]['features']
            d = np.linalg.norm(t_feats - a_feats)
            raw_imp_dists.append(d)
            
    if raw_gen_dists and raw_imp_dists:
        print("\n" + "="*30)
        print("Siamese Raw Euclidean Performance (No IoM)")
        print("="*30)
        raw_gen_mean = np.mean(raw_gen_dists)
        raw_imp_mean = np.mean(raw_imp_dists)
        print(f"Genuine Mean Dist: {raw_gen_mean:.3f}")
        print(f"Imposter Mean Dist: {raw_imp_mean:.3f}")
        
        # Determine optimal threshold
        # Simple EER approximation
        best_acc = 0
        best_thresh = 0
        for thresh in np.linspace(0, 2.0, 50):
            r_frr = sum(1 for d in raw_gen_dists if d > thresh) / len(raw_gen_dists)
            r_far = sum(1 for d in raw_imp_dists if d <= thresh) / len(raw_imp_dists)
            acc = ((1-r_far) + (1-r_frr))/2
            if acc > best_acc:
                best_acc = acc
                best_thresh = thresh
                
        print(f"Best Threshold: {best_thresh:.3f}")
        print(f"Max Accuracy:   {best_acc*100:.2f}%")
        print("="*30)

    print("="*30)

if __name__ == "__main__":
    run_performance_test()
