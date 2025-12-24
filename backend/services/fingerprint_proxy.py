import cv2
import numpy as np

class FingerprintProxy:
    def __init__(self):
        # ORB is a good free alternative to SIFT/SURF
        self.orb = cv2.ORB_create(nfeatures=40) # Limit features to keep Vault size manageable

    def extract_features(self, image_bytes):
        """
        Extracts keypoints (x, y) from a fingerprint image buffer.
        Returns a list of integer tuples [(x1, y1), (x2, y2), ...].
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            return None

        # Detect keypoints
        kp = self.orb.detect(img, None)
        
        # Convert to list of (x, y) coordinates
        # We discretize/quantize them to integers for the Vault to work reliably
        points = []
        for k in kp:
            x, y = int(k.pt[0]), int(k.pt[1])
            # Filter duplicates implicitly or explicitly if needed
            points.append((x, y))
            
        # Sort for consistency (though Vault relies on set matching)
        return sorted(list(set(points)))
