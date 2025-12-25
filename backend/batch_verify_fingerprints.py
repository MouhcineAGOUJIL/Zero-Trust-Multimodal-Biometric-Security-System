import os
import glob
import json
import cv2
import numpy as np
from backend.services.fingerprint_proxy import FingerprintProxy
from backend.services.fuzzy_vault import FuzzyVault

import os
import glob
import json
import cv2
import numpy as np
from backend.services.fingerprint_proxy import FingerprintProxy
from backend.services.fuzzy_vault import FuzzyVault

# Configuration
DB_PATH = "/home/red/Documents/S5/Biom Sec/DB2_B"
START_ID = 101
END_ID = 110
SAMPLES_PER_ID = 8

def get_features_and_descriptors(image_path):
    """
    Returns (keypoints_list, descriptors, raw_keypoints_obj)
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None: return None, None, None
    
    # Preprocessing
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    img = clahe.apply(img)

    # Use a generous feature detector for alignment
    orb = cv2.ORB_create(nfeatures=500) 
    kp, des = orb.detectAndCompute(img, None)
    
    if kp is None or des is None: return [], None, None
    
    # Format for Vault: List of (x, y) tuples
    points = [(int(k.pt[0]), int(k.pt[1])) for k in kp]
    return points, des, kp

def align_points(target_kp, target_des, source_kp, source_des):
    """
    Aligns 'source' fingerprint to 'target' coordinate system.
    Returns: aligned_source_points (list of tuples)
    """
    if target_des is None or source_des is None or len(target_kp) < 2 or len(source_kp) < 2:
        return []

    # Match features using KNN (k=2) for Ratio Test
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = matcher.knnMatch(source_des, target_des, k=2)
    
    # Apply Lowe's Ratio Test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.9 * n.distance: # Relaxed from 0.75
            good_matches.append(m)
            
    # Fallback: If ratio test yields too few matches, use raw best matches
    if len(good_matches) < 10:
        # Sort all matches by distance
        all_matches_m = [m for m, n in matches]
        all_matches_m = sorted(all_matches_m, key=lambda x: x.distance)
        good_matches = all_matches_m[:50] # Take top 50 regardless of ratio
            
    if len(good_matches) < 4: 
        print(f"   [Align] Not enough good matches ({len(good_matches)}) for alignment.")
        return []

    # Extract location of good matches
    src_pts = np.float32([source_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([target_kp[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # 3. Estimate Affine Transform (RANSAC)
    try:
        M, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=10.0)
        
        if M is None:
            print("   [Align] Transformation Estimation Failed.")
            return []

        # Calculate alignment error on inliers
        inlier_count = np.sum(inliers)
        print(f"   [Align] Inliers: {inlier_count}/{len(src_pts)}")
        
        # Transform ALL query keypoints
        q_pts = np.float32([kp.pt for kp in source_kp]).reshape(-1, 1, 2)
        transformed_q_pts = cv2.transform(q_pts, M)
        
        aligned_features = []
        for i in range(len(transformed_q_pts)):
            pt = transformed_q_pts[i][0]
            if 0 <= pt[0] <= 400 and 0 <= pt[1] <= 600: 
                aligned_features.append((int(pt[0]), int(pt[1])))
                
        # DEBUG: Check overlap with template
        template_set = set()
        for kp in target_kp:
            template_set.add((int(kp.pt[0]), int(kp.pt[1])))
            
        close_count = 0
        for ax, ay in aligned_features:
            hit = False
            for dx in range(-8, 9):
                for dy in range(-8, 9):
                     if (ax+dx, ay+dy) in template_set:
                         hit = True
                         break
                if hit: break
            if hit: close_count += 1
            
        print(f"   [Align] Pseudo-Match Loop: {close_count} overlapping (Radius 8)")

        return aligned_features

    except Exception as e:
        print(f"   [Align] Error during warp: {e}")
        return []

def main():
    print("🚀 Starting HIGH-PERFORMANCE Fingerprint Testing (With Alignment)...")
    print(f"Dataset Path: {DB_PATH}")
    print("-" * 60)

    vault_service = FuzzyVault()
    
    # Store alignment data for impostor tests
    # {id: {'des': descriptors, 'kp_obj': raw_cv_keypoints, 'vault': vault_data, 'secret': secret}}
    enrolled_data = {} 
    
    total_genuine_attempts = 0
    total_genuine_success = 0
    
    total_impostor_attempts = 0
    total_impostor_success = 0

    # 1. Genuine Authorization Tests
    for user_id in range(START_ID, END_ID + 1):
        print(f"\n[User {user_id}] Processing...")
        
        # Enrollment: Image _1
        enroll_path = os.path.join(DB_PATH, f"{user_id}_1.tif")
        e_points, e_des, e_kp_obj = get_features_and_descriptors(enroll_path)
        
        if not e_points or len(e_points) < 10:
            print(f"  ❌ Enrollment Failed: Poor quality {os.path.basename(enroll_path)}")
            continue
            
        # Lock Vault (Use top 40 points to keep partials small) -> actually, use all for robustness
        # Note: Vault capacity is limited. We'll stick to logical vault usage.
        secret = 12345 + user_id
        # We only lock using the discrete points derived from features
        # The vault doesn't know about alignment, it just takes points.
        vault_data = vault_service.lock(secret, e_points[:60]) # Lock max 60 minutiae
        
        enrolled_data[user_id] = {
            'des': e_des,
            'kp_obj': e_kp_obj,
            'vault': vault_data,
            'secret': secret
        }
        
        print(f"  ✅ Enrolled (Vault Size: {len(vault_data)})")

        # Verification: Images _2 to _8
        user_success = 0
        user_attempts = 0
        
        for sample_id in range(2, SAMPLES_PER_ID + 1):
            verify_path = os.path.join(DB_PATH, f"{user_id}_{sample_id}.tif")
            if not os.path.exists(verify_path): continue
                
            v_points, v_des, v_kp_obj = get_features_and_descriptors(verify_path)
            
            user_attempts += 1
            
            # --- ALIGNMENT STEP ---
            # Align Verify(v) to Enroll(e)
            aligned_v_points = align_points(enrolled_data[user_id]['kp_obj'], enrolled_data[user_id]['des'], v_kp_obj, v_des)
            
            is_match = False
            match_method = "Raw"
            
            if aligned_v_points:
                # Try unlocking with ALIGNED points
                rec_secret, quality = vault_service.unlock(vault_data, aligned_v_points)
                if rec_secret == secret:
                    is_match = True
                    match_method = "Aligned"
            
            # Fallback: Try Raw points (if alignment failed or produced garbage)
            if not is_match and v_points:
                rec_secret, quality = vault_service.unlock(vault_data, v_points)
                if rec_secret == secret:
                    is_match = True
                    match_method = "Raw"

            status = "PASS" if is_match else "FAIL"
            color = "\033[92m" if is_match else "\033[91m"
            reset = "\033[0m"
            
            print(f"    - Sample {sample_id}: {color}{status}{reset} [{match_method}] (Pts: {len(aligned_v_points) if aligned_v_points else 0})")
            
            if is_match:
                user_success += 1

        total_genuine_attempts += user_attempts
        total_genuine_success += user_success
        
        rate = (user_success / user_attempts * 100) if user_attempts > 0 else 0
        print(f"  >> Match Rate: {user_success}/{user_attempts} ({rate:.1f}%)")

    # 2. Impostor Tests
    print("\n[Impostor Tests] Running Cross-Matching (With Alignment)...")
    for user_id in range(START_ID, END_ID):
        victim_id = user_id
        attacker_id = user_id + 1
        
        if victim_id not in enrolled_data or attacker_id not in enrolled_data: continue
        
        # Attacker uses their Image _1, tries to align to Victim's Image _1
        # This simulates an attacker trying to optimally align their print to the target
        attacker_path = os.path.join(DB_PATH, f"{attacker_id}_1.tif")
        a_points, a_des, a_kp_obj = get_features_and_descriptors(attacker_path)
        
        total_impostor_attempts += 1
        
        # Try Aligning Attacker -> Victim
        aligned_a_points = align_points(enrolled_data[victim_id]['kp_obj'], enrolled_data[victim_id]['des'], a_kp_obj, a_des)
        
        points_to_try = aligned_a_points if aligned_a_points else a_points
        
        rec_secret, _ = vault_service.unlock(enrolled_data[victim_id]['vault'], points_to_try)
        
        if rec_secret == enrolled_data[victim_id]['secret']:
            print(f"  ⚠️ ALERT: User {attacker_id} unlocked User {victim_id}'s vault!")
            total_impostor_success += 1
        else:
            # print(f"  Shielded.")
            pass

    print("-" * 60)
    print("📊 FINAL RESULTS (With Alignment)")
    print("-" * 60)
    if total_genuine_attempts > 0:
        gen_rate = (total_genuine_success / total_genuine_attempts) * 100
        print(f"Genuine Acceptance Rate (GAR): {gen_rate:.2f}% ({total_genuine_success}/{total_genuine_attempts})")
    else:
        print("Genuine Acceptance Rate (GAR): N/A")
        
    if total_impostor_attempts > 0:
        far_rate = (total_impostor_success / total_impostor_attempts) * 100
        print(f"False Acceptance Rate (FAR):   {far_rate:.2f}% ({total_impostor_success}/{total_impostor_attempts})")
    else:
        print("False Acceptance Rate (FAR):   N/A")
    print("-" * 60)

if __name__ == "__main__":
    main()
