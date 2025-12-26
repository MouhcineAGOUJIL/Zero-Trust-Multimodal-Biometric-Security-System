import numpy as np
import cv2
from scipy import signal
from scipy import ndimage

class FingerprintCore:
    def __init__(self):
        # Parameters
        self.block_size = 16
        self.threshold_std = 0.1  # For segmentation
        
    def _zhang_suen_thinning(self, img):
        """
        Implements Zhang-Suen thinning algorithm for skeletonization.
        img: binary image (0/1)
        """
        # Ensure image is 0/1
        img = img.copy()
        img[img > 0] = 1
        
        # Kernels for neighborhood analysis
        # P9 P2 P3
        # P8 P1 P4
        # P7 P6 P5
        
        # In a list: P2, P3, P4, P5, P6, P7, P8, P9
        
        curr = img
        while True:
            # Iteration 1
            # A: Count 0->1 transitions in P2->...->P9->P2
            # B: Number of non-zero neighbors
            
            # We can use fitler2D to get neighbors count?
            # Or simplified iteration since Python loops are slow?
            # For 300x300, loops might be slow (seconds).
            # Vectorized approach:
            
            prev = curr.copy()
            
            # Shifted images
            p2 = np.roll(curr, -1, axis=0) # Up
            p3 = np.roll(np.roll(curr, -1, axis=0), 1, axis=1) # Up-Right
            p4 = np.roll(curr, 1, axis=1) # Right
            p5 = np.roll(np.roll(curr, 1, axis=0), 1, axis=1) # Down-Right
            p6 = np.roll(curr, 1, axis=0) # Down
            p7 = np.roll(np.roll(curr, 1, axis=0), -1, axis=1) # Down-Left
            p8 = np.roll(curr, -1, axis=1) # Left
            p9 = np.roll(np.roll(curr, -1, axis=0), -1, axis=1) # Up-Left
            
            # B: Number of non-zero neighbors
            B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            
            # A: Number of 0->1 transitions
            # (p2==0 && p3==1) + (p3==0 && p4==1) ...
            A = ((p2 == 0) & (p3 == 1)) + \
                ((p3 == 0) & (p4 == 1)) + \
                ((p4 == 0) & (p5 == 1)) + \
                ((p5 == 0) & (p6 == 1)) + \
                ((p6 == 0) & (p7 == 1)) + \
                ((p7 == 0) & (p8 == 1)) + \
                ((p8 == 0) & (p9 == 1)) + \
                ((p9 == 0) & (p2 == 1))
            
            # Cond 1: 2 <= B <= 6
            c1 = (B >= 2) & (B <= 6)
            
            # Cond 2: A == 1
            c2 = (A == 1)
            
            # Iter 1: P2*P4*P6 == 0 AND P4*P6*P8 == 0
            c3a = ((p2 * p4 * p6) == 0)
            c4a = ((p4 * p6 * p8) == 0)
            
            # Delete pixels
            m1 = c1 & c2 & c3a & c4a & (curr == 1)
            curr[m1] = 0
            
            # Recompute shifted for Iter 2? Or just update affected?
            # Standard algo updates sequentially. Vectorized updates parallel.
            # But Zhang Suen has 2 sub-iterations.
            
            # Iteration 2
            # Use UPDATED curr
            p2 = np.roll(curr, -1, axis=0)
            p3 = np.roll(np.roll(curr, -1, axis=0), 1, axis=1)
            p4 = np.roll(curr, 1, axis=1)
            p5 = np.roll(np.roll(curr, 1, axis=0), 1, axis=1)
            p6 = np.roll(curr, 1, axis=0)
            p7 = np.roll(np.roll(curr, 1, axis=0), -1, axis=1)
            p8 = np.roll(curr, -1, axis=1)
            p9 = np.roll(np.roll(curr, -1, axis=0), -1, axis=1)
            
            B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            A = ((p2 == 0) & (p3 == 1)) + \
                ((p3 == 0) & (p4 == 1)) + \
                ((p4 == 0) & (p5 == 1)) + \
                ((p5 == 0) & (p6 == 1)) + \
                ((p6 == 0) & (p7 == 1)) + \
                ((p7 == 0) & (p8 == 1)) + \
                ((p8 == 0) & (p9 == 1)) + \
                ((p9 == 0) & (p2 == 1))
            
            c1 = (B >= 2) & (B <= 6)
            c2 = (A == 1)
            
            # Iter 2: P2*P4*P8 == 0 AND P2*P6*P8 == 0
            c3b = ((p2 * p4 * p8) == 0)
            c4b = ((p2 * p6 * p8) == 0)
            
            m2 = c1 & c2 & c3b & c4b & (curr == 1)
            curr[m2] = 0
            
            # Stop if no change
            if np.sum(m1) == 0 and np.sum(m2) == 0:
                break
                
        return curr

        
    def normalize(self, img):
        """Standardize image mean 0, var 1"""
        if img is None: return None
        norm_img = (img - np.mean(img)) / (np.std(img) + 1e-10)
        return norm_img

    def segment(self, img, w=16):
        """Separate fingerprint from background using variance"""
        rows, cols = img.shape
        mask = np.zeros((rows, cols), dtype=np.uint8)
        
        for r in range(0, rows, w):
            for c in range(0, cols, w):
                chunk = img[r:min(r+w, rows), c:min(c+w, cols)]
                if np.std(chunk) > self.threshold_std:
                    mask[r:min(r+w, rows), c:min(c+w, cols)] = 1
                    
        # Morphological closing to fill holes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w, w))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    def calculate_orientation(self, img, w=16):
        """Estimate orientation field using gradients"""
        # Sobel Gradients
        gx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
        
        rows, cols = img.shape
        orientations = np.zeros((rows, cols), dtype=np.float32)
        
        # Smoothed gradients
        # Gxx = gx**2, Gyy = gy**2, Gxy = gx*gy
        # Block averaging
        
        # Gaussian blur gradients first (more robust)
        gx = cv2.GaussianBlur(gx, (5,5), 0)
        gy = cv2.GaussianBlur(gy, (5,5), 0)
        
        Gxx = gx**2
        Gyy = gy**2
        Gxy = gx*gy
        
        # Average per block
        for r in range(0, rows, w):
            for c in range(0, cols, w):
                pixel_area = slice(r, min(r+w, rows)), slice(c, min(c+w, cols))
                
                sum_Gxx = np.sum(Gxx[pixel_area])
                sum_Gyy = np.sum(Gyy[pixel_area])
                sum_Gxy = np.sum(Gxy[pixel_area])
                
                # Theta = 0.5 * atan2(2Gxy, Gxx - Gyy)
                theta = 0.5 * np.arctan2(2*sum_Gxy, sum_Gxx - sum_Gyy)
                orientations[pixel_area] = theta
                
        return orientations

    def gabor_filter(self, img, orientations, w=16):
        """Apply oriented Gabor filters to enhance ridges"""
        rows, cols = img.shape
        enhanced = np.zeros((rows, cols), dtype=np.float32)
        
        # Precompute kernels for discrete angles (0, 10, ... 170)
        freq = 1.0/8.0 # Average ridge frequency (~8-10 pixels)
        filters = {}
        
        for angle_deg in range(0, 180, 5):
            theta = np.deg2rad(angle_deg)
            kern = cv2.getGaborKernel((w-1, w-1), 4.0, theta, freq, 0.5, 0, ktype=cv2.CV_32F)
            filters[angle_deg] = kern
            
        for r in range(0, rows, w):
            for c in range(0, cols, w):
                # Get local orientation
                local_theta = orientations[r+w//2, c+w//2]
                local_deg = int(np.rad2deg(local_theta))
                if local_deg < 0: local_deg += 180
                local_deg = round(local_deg / 5) * 5
                if local_deg >= 180: local_deg -= 180
                
                kernel = filters.get(local_deg, filters[0])
                
                chunk = img[r:min(r+w, rows), c:min(c+w, cols)]
                h, w_curr = chunk.shape
                
                # Pad chunk for filtering
                # Simply replicate borders
                # But easiest is to filter full image? No, orientation varies.
                # Just filter the chunk. 
                # (For speed/simplicity: Use pre-filtered global images and mask)
                # But let's do chunk-wise approximation.
                
                # Wait, chunk-wise filtering creates artifacts at boundaries.
                # Better: Filter entire image 36 times (one per angle) and combine.
                pass
                
        # Better Gabor Approach: Bank of Filters
        # Create 16 filtered images
        bank_images = {}
        for angle_deg in range(0, 180, 10): # 18 filters
            theta = np.deg2rad(angle_deg)
            kern = cv2.getGaborKernel((21, 21), 4.0, theta, 1/9.0, 0.5, 0, ktype=cv2.CV_32F)
            filtered = cv2.filter2D(img, cv2.CV_32F, kern)
            bank_images[angle_deg] = filtered
            
        # Compose
        for r in range(rows):
            for c in range(cols):
                theta = orientations[r, c]
                deg = int(np.rad2deg(theta))
                if deg < 0: deg += 180
                deg = round(deg / 10) * 10
                if deg >= 180: deg -= 180
                
                enhanced[r, c] = bank_images[deg][r, c]
                
        return enhanced

    def extract_minutiae(self, img_path):
        """Full pipeline"""
        # Load
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None: return [], None
        
        img = img.astype(np.float32) / 255.0
        
        # 1. Normalize
        norm = self.normalize(img)
        
        # 2. Segment
        mask = self.segment(norm)
        
        # 3. Orientation
        orient_map = self.calculate_orientation(norm)
        
        # 4. Enhance (Gabor)
        enhanced = self.gabor_filter(norm, orient_map)
        
        # 5. Binarize
        # Where enhanced ridges > 0 (Gabor response)
        # Apply mask
        enhanced = np.where(mask > 0, enhanced, -1.0)
        binary = (enhanced > 0).astype(np.uint8)
        
        # 6. Skeletonize
        skeleton = self._zhang_suen_thinning(binary)
        skeleton = skeleton.astype(np.uint8)
        
        # 7. Find Minutiae
        # Crossing Number method
        minutiae = []
        
        # Kernel 3x3 for neighborhood sum
        rows, cols = skeleton.shape
        
        # Avoid borders
        margin = 16
        for r in range(margin, rows-margin):
            for c in range(margin, cols-margin):
                if skeleton[r, c] == 0: continue
                
                # Check neighbors (8-connectivity)
                # P9 P2 P3
                # P8 P1 P4
                # P7 P6 P5
                # CN = 0.5 * sum(|Pi - Pi+1|)
                
                blk = skeleton[r-1:r+2, c-1:c+2]
                
                # Flatten neighbors in cyclic order
                # P2, P3, P4, P5, P6, P7, P8, P9
                # (0,1), (0,2), (1,2), (2,2), (2,1), (2,0), (1,0), (0,0) index map for 3x3
                # Indices in flatten 3x3 (0..8)
                # 0 1 2
                # 3 4 5
                # 6 7 8
                # Cycle: 1, 2, 5, 8, 7, 6, 3, 0
                
                p = [blk[0,1], blk[0,2], blk[1,2], blk[2,2], blk[2,1], blk[2,0], blk[1,0], blk[0,0]]
                
                val = 0
                for i in range(8):
                    val += abs(int(p[i]) - int(p[(i+1)%8]))
                
                cn = val * 0.5
                
                if cn == 1:
                    # Ending
                    angle = orient_map[r, c]
                    minutiae.append({'x': int(c), 'y': int(r), 'type': 'ending', 'angle': float(angle)})
                elif cn == 3:
                    # Bifurcation
                    angle = orient_map[r, c]
                    minutiae.append({'x': int(c), 'y': int(r), 'type': 'bifurcation', 'angle': float(angle)})
                    
        return minutiae, skeleton

    def match_fingerprints(self, min1, min2):
        """
        Match two sets of minutiae using geometric hashing / RANSAC.
        Returns: Score (0.0 to 1.0), Transformation (Best tx, ty, rot)
        """
        if len(min1) < 5 or len(min2) < 5:
            return 0.0, None

        best_score = 0
        best_transform = None
        
        # Convert to numpy for speed
        m1_arr = np.array([[m['x'], m['y'], m['angle']] for m in min1])
        m2_arr = np.array([[m['x'], m['y'], m['angle']] for m in min2])
        
        # Center points
        c1 = np.mean(m1_arr[:, :2], axis=0)
        c2 = np.mean(m2_arr[:, :2], axis=0)
        
        m1_centered = m1_arr[:, :2] - c1
        m2_centered = m2_arr[:, :2] - c2
        
        # Try rotations
        # Brute force rotation search (Coarse alignment)
        # -45 to +45 degrees in 2 deg steps (Finer search)
        for rot_deg in range(-45, 50, 2):
            rot_rad = np.deg2rad(rot_deg)
            cos_t, sin_t = np.cos(rot_rad), np.sin(rot_rad)
            
            # Rotate M2 to match M1
            # x' = x cos - y sin
            # y' = x sin + y cos
            
            m2_rot_x = m2_centered[:, 0] * cos_t - m2_centered[:, 1] * sin_t
            m2_rot_y = m2_centered[:, 0] * sin_t + m2_centered[:, 1] * cos_t
            
            # Simple match count
            # For each p1, is there a p2 close enough?
            # Optimization: KDTree or Grid? 
            # Brute force N*M is fine for < 100 points
            
            inliers = 0
            for i in range(len(m1_centered)):
                x1, y1 = m1_centered[i]
                
                # Find closest in m2_rot
                dists = (m2_rot_x - x1)**2 + (m2_rot_y - y1)**2
                min_dist_sq = np.min(dists)
                
                if min_dist_sq < 225: # 15 pixels radius (Relaxed)
                    inliers += 1
            
            score = inliers / max(len(min1), len(min2), 1)
            
            if score > best_score:
                best_score = score
                best_transform = (rot_deg, c1, c2)
                
        return best_score, best_transform

# Test Singleton
fp_core = FingerprintCore()
