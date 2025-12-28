
import cv2
import numpy as np
import json
import base64

class PalmService:
    def __init__(self):
        # Switch to AKAZE for stability (Segmentation fault fix)
        self.detector = cv2.AKAZE_create() 
        # Matcher: Hamming distance works for AKAZE descriptors (binary)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def preprocess(self, image_bytes):
        """
        Convert bytes to Grayscale and enhance contrast (CLAHE).
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        
        # Resize if too large (speed up AKAZE)
        h, w = img.shape[:2]
        if w > 800:
            scale = 800 / w
            img = cv2.resize(img, (int(w*scale), int(h*scale)))
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Enhances the palm lines significantly
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        return enhanced

    def create_template(self, image_bytes):
        """
        Extract descriptors and serialize to JSON compatible format.
        """
        # print("[PalmService] Preprocessing...")
        img = self.preprocess(image_bytes)
        if img is None:
            print("[PalmService] Preprocessing failed (img is None).")
            return None
            
        # print(f"[PalmService] Detecting Features (Shape: {img.shape})...")
        try:
            # Detect and Compute
            kp, des = self.detector.detectAndCompute(img, None)
            # print(f"[PalmService] Found {len(kp)} keypoints.")
        except Exception as e:
            print(f"[PalmService] Feature Detector Error: {e}")
            return None
        
        if des is None or len(des) < 10:
             print("[PalmService] Not enough descriptors.")
             return None # Not enough features
            
        # Convert descriptors (numpy uint8) to Base64 string for storage
        des_b64 = base64.b64encode(des.tobytes()).decode('utf-8')
        
        data = {
            "shape": des.shape,
            "dtype": str(des.dtype),
            "b64": des_b64
        }
        return json.dumps(data)

    def verify(self, image_bytes, stored_template_json):
        """
        Match live image against stored template using Ratio Test.
        """
        # 1. Parse Stored Template
        try:
            data = json.loads(stored_template_json)
            # Support legacy format check (if user had old implementation)
            if "b64" not in data: 
                return False, 0.0, "Invalid Template Format"
                
            dtype = np.dtype(data['dtype']) if 'dtype' in data else np.uint8
            
            des_stored = np.frombuffer(base64.b64decode(data['b64']), dtype=dtype)
            des_stored = des_stored.reshape(data['shape'])
        except Exception as e:
            print(f"[PalmService] Template Error: {e}")
            return False, 0.0, "Template Error"
            
        # 2. Extract Live Features
        img = self.preprocess(image_bytes)
        if img is None:
            return False, 0.0, "Image Error"
            
        kp_live, des_live = self.detector.detectAndCompute(img, None)
        
        if des_live is None or len(des_live) < 5:
            return False, 0.0, "No Features Found"
            
        # 3. Match
        # knnMatch with k=2 for Ratio Test
        matches = self.bf.knnMatch(des_live, des_stored, k=2)
        
        good_matches = []
        for m, n in matches:
            # Lowe's Ratio Test
            # If the closest match is significantly closer than the second closest, it's a "Good" match.
            # 0.75 is standard. Stricter = 0.7
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
                
        # 4. Scoring
        # How many good matches defined "Identity"?
        # For Palm, usually 20-50 matches is strong evidence.
        score = len(good_matches)
        
        # Threshold:
        # < 10: Noise
        # 10-20: Weak Match
        # > 25: Strong Match
        # BENCHMARK UPDATE: Imposters get up to 60. Genuines get > 260.
        # Safe Threshold: 100
        is_match = score >= 100
        
        return is_match, score, "Matched"

