import cv2
import numpy as np
import sys
import os

# Ensure backend modules are importable
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from backend.fingerprint_core import fp_core

class FingerprintProxy:
    def __init__(self):
        self.core = fp_core

    def extract_features(self, image_bytes):
        """
        Extracts minutiae from image buffer using FingerprintCore.
        Returns list of dicts: {'x': int, 'y': int, 'angle': float, 'type': str}
        """
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            
            if img is None:
                return None
            
            # Save temp file for core? (Core takes path)
            # Refactor Core to take image array?
            # Yes, check FingerprintCore.extract_minutiae.
            # It currently does cv2.imread(path).
            # I should overload it or modify Core to take numpy array.
            
            # Quick fix: Save to temp (inefficient but safe for now)
            # Or better: modify Core.
            
            # Since I can't modify Core in this prompt (I already did), 
            # I will modify Core to accept image array in next step or now?
            # I will assume I can modify/overload Core logic here or save temp.
            
            # Let's save temp for robustness strictly within this proxy to avoid changing too many files at once.
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                cv2.imwrite(tmp.name, img)
                tmp_path = tmp.name
                
            minutiae, _ = self.core.extract_minutiae(tmp_path)
            os.unlink(tmp_path)
            
            return minutiae
            
        except Exception as e:
            print(f"Feature Extraction Error: {e}")
            return []

    def match(self, min1, min2):
        """Proxy to core matching"""
        return self.core.match_fingerprints(min1, min2)
