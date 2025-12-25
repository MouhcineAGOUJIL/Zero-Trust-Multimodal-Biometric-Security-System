import cv2
import numpy as np

class FingerprintProxy:
    def __init__(self):
        # ORB Configuration: More sensitive for synthetic/simple images
        self.orb = cv2.ORB_create(
            nfeatures=100, 
            edgeThreshold=5, 
            patchSize=31, 
            fastThreshold=0
        ) 

    def extract_features(self, image_bytes):
        """
        Extracts keypoints (x, y) from a fingerprint image buffer.
        Returns a list of integer tuples [(x1, y1), (x2, y2), ...].
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            return None

        # Pre-processing: Enhance Constrast (CLAHE)
        # This helps detection on low-contrast synthetic images
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        img = clahe.apply(img)

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
