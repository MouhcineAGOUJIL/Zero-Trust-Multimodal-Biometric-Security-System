
import cv2
import numpy as np
import json
import base64

class IrisCancelableService:
    def __init__(self):
        # Parameters for Gabor Filter
        # Tuned for normalized iris
        self.ksize = (31, 31)
        self.sigma = 4.0
        self.lambd = 10.0
        self.gamma = 0.5
        self.psi = 0
        
        self.gabor_kernel = cv2.getGaborKernel(
            self.ksize, self.sigma, 0, self.lambd, self.gamma, self.psi, ktype=cv2.CV_32F
        )

    def preprocess(self, image_bytes):
        """
        Robust Preprocessing:
        1. Resize
        2. Find Pupil (Darkest Cluster)
        3. Define Iris relative to Pupil
        4. Unwrap
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if img is None: return None

        # Resize to fixed width (speed + consistency)
        h, w = img.shape
        target_w = 400
        scale = target_w / w
        img_small = cv2.resize(img, (int(w*scale), int(h*scale)))
        
        # --- ROI Extraction ---
        blurred = cv2.medianBlur(img_small, 9)
        
        hist = cv2.calcHist([blurred], [0], None, [256], [0, 256])
        cdf = hist.cumsum()
        total_pixels = img_small.shape[0] * img_small.shape[1]
        threshold_val = 30
        for i, count in enumerate(cdf):
             if count > total_pixels * 0.05:
                 threshold_val = i
                 break
        threshold_val = min(threshold_val, 60)
        
        _, thresh = cv2.threshold(blurred, threshold_val, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_circle = (w//2, h//2, w//6)
        best_score = 0
        center_x, center_y = img_small.shape[1]//2, img_small.shape[0]//2
        
        for c in contours:
            area = cv2.contourArea(c)
            if area < 50: continue
            if area > (total_pixels * 0.15): continue
            
            perimeter = cv2.arcLength(c, True)
            if perimeter == 0: continue
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            
            M = cv2.moments(c)
            if M['m00'] == 0: continue
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            
            dist_from_center = np.sqrt((cx - center_x)**2 + (cy - center_y)**2)
            score = circularity * (1 - dist_from_center/w) * 2
            
            if score > best_score:
                best_score = score
                (x,y), radius = cv2.minEnclosingCircle(c)
                best_circle = (int(x), int(y), int(radius))

        px, py, pr = best_circle
        
        # --- Safe Radii Calculation ---
        dist_to_edge_x = min(px, img_small.shape[1] - px)
        dist_to_edge_y = min(py, img_small.shape[0] - py)
        max_possible_radius = min(dist_to_edge_x, dist_to_edge_y) - 5
        
        ir = min(int(pr * 3.0), max_possible_radius)
        ir = max(ir, int(pr * 1.5))
        
        r_inner = int(pr + 2) 
        r_outer = int(ir - 2)
        
        normalized = self.unwrap_iris(img_small, px, py, r_inner, r_outer)
        
        # --- Aggressive Cropping ---
        # Keep only the middle 50%
        final_h = normalized.shape[0]
        crop_start = int(final_h * 0.25)
        crop_end = int(final_h * 0.75)
        
        cropped = normalized[crop_start:crop_end, :]
        
        # Enhance
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
        enhanced = clahe.apply(cropped)
        
        return enhanced

    def unwrap_iris(self, img, cx, cy, r_inner, r_outer, width=360, height=64):
        thetas = np.linspace(0, 2 * np.pi, width, endpoint=False)
        radii = np.linspace(r_inner, r_outer, height, endpoint=False)
        
        theta_grid, radius_grid = np.meshgrid(thetas, radii)
        
        map_x = cx + radius_grid * np.cos(theta_grid)
        map_y = cy + radius_grid * np.sin(theta_grid)
        
        map_x = map_x.astype(np.float32)
        map_y = map_y.astype(np.float32)
        
        unwrapped = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        return unwrapped
        
    def extract_raw_code(self, image_or_bytes):
        """
        Extract Features using Gabor.
        Accepts either bytes (initial) or np.array (loop optimization).
        """
        if isinstance(image_or_bytes, bytes):
            img_norm = self.preprocess(image_or_bytes)
        else:
            img_norm = image_or_bytes
            
        if img_norm is None: return None
        
        filtered = cv2.filter2D(img_norm, cv2.CV_32F, self.gabor_kernel)
        med = np.median(filtered)
        iris_code = (filtered > med).astype(np.uint8).flatten()
        return iris_code

    def create_template(self, image_bytes, seed_token):
        ra_code = self.extract_raw_code(image_bytes)
        if ra_code is None: return None
        
        # Transform
        transformed_code = self.cancelable_transform(ra_code, seed_token)
        
        # Serialize
        packed = np.packbits(transformed_code)
        b64_str = base64.b64encode(packed.tobytes()).decode('utf-8')
        
        data = {
            "shape": transformed_code.shape,
            "b64": b64_str,
            "algo": "BlockScramble_Gabor_ImgShift"
        }
        return json.dumps(data)
    
    def cancelable_transform(self, iris_code, seed):
        np.random.seed(seed)
        n = len(iris_code)
        perm = np.random.permutation(n)
        scrambled = iris_code[perm]
        mask = np.random.randint(0, 2, size=n, dtype=np.uint8)
        secure_code = np.bitwise_xor(scrambled, mask)
        return secure_code

    def verify(self, image_bytes, stored_template_json, seed_token):
        """
        Verify using Gabor with Image-Level Rotation Search.
        """
        # 1. Preprocess IMAGE once
        img_norm = self.preprocess(image_bytes)
        if img_norm is None: return False, 0.0, "Preprocessing Failed"
        
        # 2. Load Stored
        try:
            data = json.loads(stored_template_json)
            packed = np.frombuffer(base64.b64decode(data['b64']), dtype=np.uint8)
            stored_secure_code = np.unpackbits(packed)
            length = data['shape'][0]
            stored_secure_code = stored_secure_code[:length]
        except Exception as e:
            return False, 0.0, f"Template Error: {e}"

        best_score = 0.0
        
        # 3. Shift Search (Image Level)
        # Shift normalized image by +/- N pixels
        shifts = range(-16, 17, 4) # +/- 16 pixels
        
        for s in shifts:
            # Roll image
            shifted_img = np.roll(img_norm, s, axis=1)
            
            # Extract Gabor Code
            raw_code = self.extract_raw_code(shifted_img)
            
            # Transform
            live_secure_code = self.cancelable_transform(raw_code, seed_token)
            
            # Match
            dist = np.mean(live_secure_code != stored_secure_code)
            score = (1.0 - dist) * 100
            
            if score > best_score:
                best_score = score
        
        # Threshold update: Gabor usually has 0.35-0.4 dist threshold.
        # Score > 60 is a reasonable starting point.
        is_match = best_score > 60
        
        return is_match, best_score, "Matched"
