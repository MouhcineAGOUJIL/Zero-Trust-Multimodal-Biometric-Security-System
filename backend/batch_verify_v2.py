import os
import sys
import glob

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.services.fuzzy_vault import FuzzyVault
from backend.services.fingerprint_proxy import FingerprintProxy

def batch_verify():
    proxy = FingerprintProxy()
    # Initialize vault with degree 6 for better robustness
    vault_service = FuzzyVault(polynomial_degree=6) 
    
    # Path
    base_path = "/home/red/Documents/S5/Biom Sec/Project/data/person1/fingerprints"
    
    files = sorted(glob.glob(os.path.join(base_path, "fingerprint_*.png")))
    if not files: 
        print("No files found.")
        return
        
    # Enroll File 1
    enroll_img = files[0]
    print(f"Enrolling with {os.path.basename(enroll_img)}")
    
    with open(enroll_img, 'rb') as f:
        img_bytes = f.read()
    
    features = proxy.extract_features(img_bytes)
    print(f"  Extracted {len(features)} minutiae")
    
    if len(features) < 10:
        print("  Not enough features to lock.")
        return

    secret = 12345
    vault_data = vault_service.lock(secret, features)
    print("  Vault Locked.")
    
    # Verify others
    success = 0
    total = 0
    
    # Test file 2 to end
    for fpath in files[1:]:
        total += 1
        with open(fpath, 'rb') as f:
             q_bytes = f.read()
        
        q_features = proxy.extract_features(q_bytes)
        print(f"Verifying {os.path.basename(fpath)} ({len(q_features)} minutiae)...")
        
        rec_secret, score = vault_service.unlock(vault_data, q_features)
        
        if rec_secret == secret:
            print("  ✅ SUCCESS")
            success += 1
        else:
            print("  ❌ FAIL")
            
    print("-" * 30)
    print(f"GAR: {success}/{total} ({(success/total)*100 if total > 0 else 0:.1f}%)")

if __name__ == "__main__":
    batch_verify()
