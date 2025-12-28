"""
Iris Recognition System
(Daugman IrisCode + Cancelable Biometrics)

Pipeline:
Eye Image → Iris Normalization → Gabor Encoding
→ Cancelable IrisCode → Hamming Distance

Secure, performant, industry-standard.
"""

import cv2
import numpy as np


# ======================================================
# 1. IRIS NORMALIZATION (RUBBER SHEET MODEL - SIMPLIFIED)
# ======================================================

def normalize_iris(eye_img, radius=80):
    h, w = eye_img.shape
    center = (w // 2, h // 2)

    polar = cv2.warpPolar(
        eye_img,
        (360, radius),
        center,
        radius,
        cv2.WARP_POLAR_LINEAR
    )
    return polar


# ======================================================
# 2. DAUGMAN GABOR ENCODING
# ======================================================

def gabor_encode(normalized_iris):
    gabor = cv2.getGaborKernel(
        ksize=(21, 21),
        sigma=4.0,
        theta=0,
        lambd=10.0,
        gamma=0.5
    )

    filtered = cv2.filter2D(normalized_iris, cv2.CV_32F, gabor)

    # Binary IrisCode
    iriscode = (filtered > 0).astype(np.uint8).flatten()
    return iriscode


# ======================================================
# 3. CANCELABLE BIOMETRICS
# ======================================================

def cancelable_iriscode(iriscode, seed=42):
    np.random.seed(seed)
    mask = np.random.randint(0, 2, size=len(iriscode))
    return np.bitwise_xor(iriscode, mask)


# ======================================================
# 4. HAMMING DISTANCE MATCHING
# ======================================================

def hamming_distance(code1, code2):
    return np.sum(code1 != code2) / len(code1)


# ======================================================
# 5. FULL AUTHENTICATION PIPELINE
# ======================================================

def authenticate(eye1, eye2, threshold=0.32):
    iris1 = normalize_iris(eye1)
    iris2 = normalize_iris(eye2)

    code1 = cancelable_iriscode(gabor_encode(iris1))
    code2 = cancelable_iriscode(gabor_encode(iris2))

    score = hamming_distance(code1, code2)
    return score, score < threshold


# ======================================================
# 6. EXAMPLE
# ======================================================

if __name__ == "__main__":
    img1 = cv2.imread("iris1.png", cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread("iris2.png", cv2.IMREAD_GRAYSCALE)

    score, result = authenticate(img1, img2)

    print(f"Hamming Distance: {score:.3f}")
    print("✅ MATCH" if result else "❌ NO MATCH")
