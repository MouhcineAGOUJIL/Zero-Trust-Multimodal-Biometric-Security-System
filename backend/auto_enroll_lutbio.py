
import os
import sys
import glob
import json
import shutil
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.getcwd())

from backend import models, database
from backend.services.biometric import BiometricService
from backend.services.cnn_service import CNNService
from backend.services.iom_service import IoMService
from backend.services.palm_service import PalmService

# Configuration
DATASET_PATH = "/home/red/Documents/S5/Biom Sec/Project/LUTBIO sample data"
DB_PATH = "biosec.db"
EXCLUDED_IDS = ["001", "063"]

def reset_database():
    print(f"[-] Deleting existing database: {DB_PATH}")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    print(f"[-] Creating new database tables...")
    models.Base.metadata.create_all(bind=database.engine)

def get_file_bytes(path):
    if not path: return None
    with open(path, "rb") as f:
        return f.read()

def main():
    print("=== Auto-Enrollment Script for LUTBIO ===")
    
    # 1. Reset DB
    reset_database()
    
    session = database.SessionLocal()
    
    # 2. Initialize Services
    print("[-] Initializing Biometric Services...")
    bio_service = BiometricService()
    cnn_service = CNNService()
    iom_service = IoMService(key_len=256)
    palm_service = PalmService()
    
    # 3. Iterate Users
    if not os.path.exists(DATASET_PATH):
        print(f"[!] Dataset path not found: {DATASET_PATH}")
        return

    subdirs = sorted([d for d in os.listdir(DATASET_PATH) if os.path.isdir(os.path.join(DATASET_PATH, d))])
    
    for uid in subdirs:
        if uid in EXCLUDED_IDS:
            print(f"[Skipping] User {uid} (Excluded)")
            continue
            
        user_path = os.path.join(DATASET_PATH, uid)
        username = f"user{uid}"
        print(f"\n[Processing] {username}...")
        
        # 4. Find Sample Images (Take the first valid one)
        # Face
        face_dir = os.path.join(user_path, "face")
        faces = sorted(glob.glob(os.path.join(face_dir, "*")))
        face_file = faces[0] if faces else None
        
        # Finger
        finger_dir = os.path.join(user_path, "finger")
        fingers = sorted(glob.glob(os.path.join(finger_dir, "*")))
        finger_file = fingers[0] if fingers else None
        
        # Palm
        palm_dir = os.path.join(user_path, "palm_touch")
        palms = sorted(glob.glob(os.path.join(palm_dir, "*")))
        palm_file = palms[0] if palms else None
        
        if not face_file:
            print(f"  [!] No face found for {uid}. Skipping.")
            continue
            
        # 5. Enroll Logic (Replicating auth.py)
        
        # --- Face ---
        face_bytes = get_file_bytes(face_file)
        f_feats = bio_service.extract_features_from_buffer(face_bytes)
        
        if f_feats is None:
            print(f"  [!] Face extraction failed for {face_file}")
            continue
            
        secret_token = bio_service.generate_token()
        biohash_str = bio_service.generate_biohash(f_feats, secret_token)
        print(f"  [+] Face Enrolled.")
        
        # --- Finger ---
        finger_vault = None
        if finger_file:
            print(f"  [.] Processing Finger: {os.path.basename(finger_file)}")
            # Ridge enhancement ON for fingers
            f_bytes = get_file_bytes(finger_file)
            f_feats = cnn_service.extract_features(f_bytes, enhance_ridges=True)
            
            if f_feats is not None:
                iom_hash = iom_service.generate_iom_hash(f_feats, secret_token)
                vault_storage = {
                    "helper_data": f_feats.tolist(),
                    "iom_hash": iom_hash
                }
                finger_vault = json.dumps(vault_storage)
                print(f"  [+] Finger Enrolled.")
            else:
                print(f"  [!] Finger extraction failed.")
        
        # --- Palm (ORB) ---
        palm_vault = None
        if palm_file:
            print(f"  [.] Processing Palm: {os.path.basename(palm_file)}")
            p_bytes = get_file_bytes(palm_file)
            # PalmService handles template creation
            palm_template = palm_service.create_template(p_bytes)
            
            if palm_template:
                palm_vault = palm_template
                print(f"  [+] Palm Enrolled (ORB).")
            else:
                print(f"  [!] Palm extraction failed.")
                
        # 6. Save to DB
        # Create User
        try:
            new_user = models.User(username=username, trusted_ip="127.0.0.1")
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            # Create Template
            new_template = models.BiometricTemplate(
                user_id=new_user.id,
                seed_token=secret_token,
                biohash_data=biohash_str,
                fingerprint_vault=finger_vault,
                palm_vault=palm_vault
            )
            session.add(new_template)
            session.commit()
            print(f"  [SUCCESS] {username} enrolled successfully.")
            
        except Exception as e:
            print(f"  [ERROR] Database save failed: {e}")
            session.rollback()

    print("\n=== Enrollment Complete ===")
    session.close()

if __name__ == "__main__":
    main()
