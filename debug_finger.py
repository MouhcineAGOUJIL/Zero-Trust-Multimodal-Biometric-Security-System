from backend.services.fingerprint_proxy import FingerprintProxy
import cv2
import os

def test_proxy():
    print("Initializing Proxy...")
    proxy = FingerprintProxy()
    
    path = "finger_a.png"
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return

    print(f"Reading {path}...")
    with open(path, "rb") as f:
        data = f.read()
    
    print(f"Extracting features from {len(data)} bytes...")
    points = proxy.extract_features(data)
    
    if points:
        print(f"Success! Found {len(points)} keypoints.")
        print(f"First 5: {points[:5]}")
    else:
        print("Failed to find keypoints (or Error).")

if __name__ == "__main__":
    try:
        test_proxy()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
