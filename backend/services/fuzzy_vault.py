import random
import numpy as np
import warnings
import struct
import binascii

class FuzzyVault:
    def __init__(self, polynomial_degree=8, vault_size=250):
        # TIFS07 uses Degree 8-10. 
        self.degree = polynomial_degree
        self.vault_size = vault_size
        self.QUANTIZATION = 1000  # Scaling factor for float coords -> int
        self.MIN_DIST_CHAFF = 15  # Minimum distance between any two points (Real or Chaff)

    def _compute_crc(self, data):
        """Standard CRC-16 (Modbus) implementation."""
        # polynomial 0x8005 (x^16 + x^15 + x^2 + 1)
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if (crc & 0x0001):
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        return crc

    def _encode_secret(self, secret_int):
        """
        Encodes secret + CRC into coefficients.
        Secret is split into lower-order coefficients.
        """
        # 1. Convert secret to bytes
        try:
            # Assume secret is small int, pack to 4 bytes
            data = struct.pack('<I', secret_int)
        except:
            data = struct.pack('<I', secret_int % 0xFFFFFFFF)
            
        # 2. Compute CRC
        crc = self._compute_crc(data)
        
        # 3. Create coefficients
        # P(x) = c0 + c1*x + ... + c8*x^8
        # We embed (Secret, CRC) into these coefficients.
        # Simple method: c0=Secret, c1=CRC, Rest=Random
        coeffs = [secret_int, crc] + [random.randint(1, 1000) for _ in range(self.degree - 1)]
        
        return np.poly1d(coeffs[::-1]), crc

    def lock(self, secret_int, features):
        """
        Locks secret using robust 2D placement.
        """
        # 1. Construct Polynomial with CRC
        poly, stored_crc = self._encode_secret(secret_int)
        
        vault = []
        occupied_u = set()
        
        # 2. Project Real Points (Genuine)
        for (x, y) in features:
            # Secure 2D Projection: u = x || y
            # u = x * 1000 + y
            u = int(x) * 1000 + int(y)
            
            # Check for exact collision
            if u in occupied_u: continue
            
            # Evaluate Poly
            v = int(poly(u))
            
            vault.append((u, v))
            occupied_u.add(u)

        # 3. Add Chaff Points (Robust Generation)
        attempts = 0
        
        # Estimate bounds (generic image size 600x600)
        max_x = 600
        max_y = 600
        
        # Determine V range
        ys = [p[1] for p in vault]
        min_v, max_v = (min(ys), max(ys)) if ys else (0, 100000)
        v_range = max_v - min_v
        
        # Decode genuine X,Y for distance checking
        genuine_xy = []
        for u in occupied_u:
            genuine_xy.append((u // 1000, u % 1000))

        while len(vault) < self.vault_size and attempts < self.vault_size * 50:
            attempts += 1
            
            # Generate random 2D point (x, y)
            rx = random.randint(0, max_x)
            ry = random.randint(0, max_y)
            
            # Distance check in 2D
            is_close = False
            for (gx, gy) in genuine_xy:
                if abs(rx - gx) < 15 and abs(ry - gy) < 15:
                    is_close = True; break
            
            if not is_close:
                ru = rx * 1000 + ry
                # Random V (Chaff)
                rv = random.randint(min_v - int(v_range*0.2), max_v + int(v_range*0.2))
                
                vault.append((ru, rv))
                # Add to local exclusion list
                genuine_xy.append((rx, ry))
        
        random.shuffle(vault)
        return vault

    def unlock(self, vault, candidate_features):
        """
        Unlocks using 2D Spatial Matching.
        """
        # 1. Parse Candidate Points
        candidates_xy = [(int(x), int(y)) for (x, y) in candidate_features]
             
        # 2. Find Matches (Spatial Tolerance)
        matches = []
        TOLERANCE = 10 
        TOLERANCE_SQ = TOLERANCE ** 2
        
        for (vu, vv) in vault:
            # Unpack Vault Point
            vx = vu // 1000
            vy = vu % 1000
            
            # Find closest candidate
            best_dist_sq = float('inf')
            
            for (cx, cy) in candidates_xy:
                if abs(vx - cx) > TOLERANCE: continue 
                if abs(vy - cy) > TOLERANCE: continue
                
                dist_sq = (vx - cx)**2 + (vy - cy)**2
                if dist_sq < best_dist_sq:
                    best_dist_sq = dist_sq
            
            if best_dist_sq <= TOLERANCE_SQ:
                matches.append((vu, vv))
        
        # Deduplicate
        matches = list(set(matches))
        
        # print(f"[FuzzyVault] Matches: {len(matches)} (Required: {self.degree+2})")

        # Check Sufficiency
        if len(matches) < self.degree + 2:
            return None, 0.0
            
        # 3. RANSAC with CRC Check
        iterations = 2000
        best_secret = None
        
        for _ in range(iterations):
            try:
                # Sample
                sample = random.sample(matches, self.degree + 1)
                
                # Check for duplicate Inputs in sample
                sus = [p[0] for p in sample]
                if len(set(sus)) < len(sus): 
                     continue 
                
                sv = [p[1] for p in sample]
                
                # Interpolate P(u)
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', np.RankWarning)
                    z = np.polyfit(sus, sv, self.degree)
                    rec_poly = np.poly1d(z)
                
                # Check Inliers
                inliers_count = 0
                for (mu, mv) in matches:
                    if abs(rec_poly(mu) - mv) < 500: 
                        inliers_count += 1
                
                # Pruning
                if inliers_count < self.degree + 3:
                     continue
                
                # DECODE and CRC
                rec_secret = int(round(rec_poly.coeffs[-1]))
                rec_crc = int(round(rec_poly.coeffs[-2]))
                
                # Verify CRC
                try:
                     if rec_secret < 0: rec_secret = abs(rec_secret)
                     data = struct.pack('<I', rec_secret)
                except:
                     continue
                    
                calc_crc = self._compute_crc(data)
                
                if calc_crc == rec_crc:
                    print(f"[FuzzyVault] CRC MATCH! Secret: {rec_secret} Inliers: {inliers_count}")
                    return rec_secret, 1.0 
                    
            except Exception:
                pass
             
        return None, 0.0
