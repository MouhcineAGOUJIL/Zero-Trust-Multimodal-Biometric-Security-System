import cv2
import sys
import os
import numpy as np

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.fingerprint_core import FingerprintCore

def test_matching():
    core = FingerprintCore()
    
    # Path to DB
    db_path = "/home/red/Documents/S5/Biom Sec/Project/data/person1/fingerprints"
    
    # Files are named fingerprint_1.png, fingerprint_2.png...
    f1_path = os.path.join(db_path, "fingerprint_1.png")
    
    if not os.path.exists(f1_path):
         print(f"Error: File not found at {f1_path}")
         return
         
    # Find second file
    base, ext = os.path.splitext(f1_path)
    # base is .../fingerprint_1
    # We want .../fingerprint_2.png
    f2_path = os.path.join(db_path, "fingerprint_2.png")
    
    print(f"Testing Matching: {f1_path} vs {f2_path}")
    
    # 1. Extract Minutiae 1
    min1, skel1 = core.extract_minutiae(f1_path)
    print(f"  Image 1: {len(min1)} minutiae")
    
    # 2. Extract Minutiae 2
    min2, skel2 = core.extract_minutiae(f2_path)
    print(f"  Image 2: {len(min2)} minutiae")
    
    # Debug: Save Skeletons
    cv2.imwrite("debug_skel_1.png", skel1 * 255)
    cv2.imwrite("debug_skel_2.png", skel2 * 255)
    print("  Saved debug skeletons.")
    
    # 3. Match
    score, transform = core.match_fingerprints(min1, min2)
    print(f"  Match Score: {score:.4f}")
    
    if transform:
        rot, c1, c2 = transform
        print(f"  Best Transform: Rot={rot} deg, C1={c1}, C2={c2}")
    else:
        print("  No alignment found.")
        
    if score > 0.15:
         print("  ✅ MATCH SUCCESS (Threshold > 0.15)")
    else:
         print("  ❌ MATCH FAIL")

if __name__ == "__main__":
    test_matching()
