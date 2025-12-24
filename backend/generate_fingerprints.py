import cv2
import numpy as np
import random

def generate_fingerprint(filename, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    
    # Create black canvas
    img = np.zeros((300, 300), dtype=np.uint8)
    
    # Draw random concentric ellipses/curves to simulate ridges
    center = (150, 150)
    axes = (100, 120)
    angle = random.randint(0, 360)
    
    for i in range(10, 100, 5):
        # Perturb axes slightly for uniqueness
        a = axes[0] + random.randint(-5, 5)
        b = axes[1] + random.randint(-5, 5)
        cv2.ellipse(img, center, (i, int(i*1.2)), angle, 0, 360, 255, 2)
        
        # Add random "minutiae" (dots/lines)
        if random.random() > 0.5:
             x = random.randint(50, 250)
             y = random.randint(50, 250)
             cv2.circle(img, (x, y), 2, 255, -1)

    cv2.imwrite(filename, img)
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_fingerprint("finger_a.png", seed=101) # Person A Finger
    generate_fingerprint("finger_b.png", seed=202) # Person B Finger
    # Finger A (Noisy) - Same seed but slightly blurred/rotated would be better test
    # but for simple matching we re-use A. Ideal test needs robust image aug.
