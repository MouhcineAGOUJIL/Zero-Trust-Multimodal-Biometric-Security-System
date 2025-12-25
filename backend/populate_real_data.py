import os
import glob
import shutil
import cv2
import numpy as np

# Configuration
FACE_SRC_ROOT = "/home/red/Documents/S5/Biom Sec/images"
FINGER_SRC_ROOT = "/home/red/Documents/S5/Biom Sec/DB1_B"
DATA_DST_ROOT = "data"

MAPPING = {
    "person1": {"face_dir": "Al_Gore", "finger_prefix": "101", "face_count": 6},
    "person2": {"face_dir": "Albert_Costa", "finger_prefix": "102", "face_count": 6},
    "person3": {"face_dir": "Ahmed_Chalabi", "finger_prefix": "103", "face_count": 5},
    "impostor": {"face_dir": "Ai_Sugiyama", "finger_prefix": "104", "face_count": 2}
}

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def convert_and_save(src_path, dst_path):
    # Read image
    img = cv2.imread(src_path)
    if img is None:
        print(f"Error reading {src_path}")
        return
    # Write as PNG (default compression)
    cv2.imwrite(dst_path, img)
    print(f"Saved {dst_path}")

def main():
    print("Starting Data Population...")
    
    for user_role, config in MAPPING.items():
        print(f"\nProcessing {user_role}...")
        
        # 1. Setup Directories
        face_dst_dir = os.path.join(DATA_DST_ROOT, user_role, "faces")
        finger_dst_dir = os.path.join(DATA_DST_ROOT, user_role, "fingerprints")
        
        # Clean existing (optional, but good for idempotency)
        if os.path.exists(face_dst_dir): shutil.rmtree(face_dst_dir)
        if os.path.exists(finger_dst_dir): shutil.rmtree(finger_dst_dir)
        
        ensure_dir(face_dst_dir)
        ensure_dir(finger_dst_dir)
        
        # 2. Process Faces
        src_face_dir = os.path.join(FACE_SRC_ROOT, config["face_dir"])
        # Get all images (jpg/png)
        face_files = sorted(glob.glob(os.path.join(src_face_dir, "*")))
        
        count = 0
        for i, fpath in enumerate(face_files):
            if count >= config["face_count"]:
                break
            
            fname = os.path.basename(fpath)
            dst_name = f"face_{count+1}.png" # Standardize name
            dst_path = os.path.join(face_dst_dir, dst_name)
            
            convert_and_save(fpath, dst_path)
            count += 1
            
        print(f"  -> Copied {count} faces from {config['face_dir']}")

        # 3. Process Fingerprints
        # Pattern: prefix_*.tif
        finger_pattern = os.path.join(FINGER_SRC_ROOT, f"{config['finger_prefix']}_*.tif")
        finger_files = sorted(glob.glob(finger_pattern))
        
        count = 0
        for i, fpath in enumerate(finger_files):
            fname = os.path.basename(fpath)
            # 101_1.tif -> fingerprint_1.png
            dst_name = f"fingerprint_{count+1}.png"
            dst_path = os.path.join(finger_dst_dir, dst_name)
            
            convert_and_save(fpath, dst_path)
            count += 1
            
        print(f"  -> Copied {count} fingerprints for prefix {config['finger_prefix']}")

    print("\nData Population Complete.")

if __name__ == "__main__":
    main()
