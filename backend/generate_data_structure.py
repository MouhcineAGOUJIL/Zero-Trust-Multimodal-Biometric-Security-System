import cv2
import numpy as np
import random
import os

def generate_fingerprint(filename, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    img = np.zeros((300, 300), dtype=np.uint8)
    center = (150, 150)
    axes = (100, 120)
    angle = random.randint(0, 360)
    
    # Increase density of ellipses
    for i in range(10, 140, 4):
        a = axes[0] + random.randint(-5, 5)
        b = axes[1] + random.randint(-5, 5)
        # Random Thickness
        thick = random.choice([1, 2])
        cv2.ellipse(img, center, (i, int(i*1.2)), angle, 0, 360, 255, thick)
        
        # Add random "minutiae" (dots/bifurcations) significantly
        for _ in range(5):
             x = random.randint(40, 260)
             y = random.randint(40, 260)
             cv2.circle(img, (x, y), 2, 255, -1)
    
    cv2.imwrite(filename, img)
    print(f"Generated {filename}")

if __name__ == "__main__":
    # Person 1
    generate_fingerprint("data/person1/fingerprints/fingerprint_1.png", seed=101)
    generate_fingerprint("data/person1/fingerprints/fingerprint_2.png", seed=101) # Same seed for simplicity in this logic
    
    # Person 2
    generate_fingerprint("data/person2/fingerprints/fingerprint_1.png", seed=202)
    
    # Person 3
    generate_fingerprint("data/person3/fingerprints/fingerprint_1.png", seed=303)
    
    # Impostor
    generate_fingerprint("data/impostor/fingerprints/fingerprint_1.png", seed=666)
    
    # Also generate placeholder faces if existing ones copied failed or for impostor
    # We rely on the 'cp' command for real faces, but let's make a dummy one for impostor
    dummy_face = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.putText(dummy_face, "IMPOSTOR", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.imwrite("data/impostor/faces/face_1.png", dummy_face)
