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
        Locks secret using robust 2D placement with Alignment Helper Data.
        Features: List of dicts {'x':, 'y':, 'angle':...} or tuples.
        """
        # Handle dict input
        if features and isinstance(features[0], dict):
            minutiae_xy = [(m['x'], m['y']) for m in features]
            helper_data = features[:] # Store full minutiae for alignment
        else:
            minutiae_xy = features
            helper_data = [] # No alignment possible if features are raw
            
        # 1. Construct Polynomial with CRC
        poly, stored_crc = self._encode_secret(secret_int)
        
        vault = []
        occupied_u = set()
        
        # 2. Project Real Points (Genuine)
        for (x, y) in minutiae_xy:
            u = int(x) * 1000 + int(y)
            if u in occupied_u: continue
            
            v = int(poly(u / 1000000.0))
            vault.append((u, v))
            occupied_u.add(u)

        # 3. Add Chaff Points
        attempts = 0
        max_x, max_y = 600, 600
        ys = [p[1] for p in vault]
        min_v, max_v = (min(ys), max(ys)) if ys else (0, 100000)
        v_range = max_v - min_v
        
        genuine_xy = [(u // 1000, u % 1000) for u in occupied_u]

        while len(vault) < self.vault_size and attempts < self.vault_size * 50:
            attempts += 1
            rx = random.randint(0, max_x)
            ry = random.randint(0, max_y)
            
            is_close = False
            for (gx, gy) in genuine_xy:
                if abs(rx - gx) < 15 and abs(ry - gy) < 15:
                    is_close = True; break
            
            if not is_close:
                ru = rx * 1000 + ry
                rv = random.randint(min_v - int(v_range*0.2), max_v + int(v_range*0.2))
                vault.append((ru, rv))
                genuine_xy.append((rx, ry))
        
        random.shuffle(vault)
        return {
            'vault': vault, 
            'helper_data': helper_data,
            'degree': self.degree
        }

    def unlock(self, vault_package, candidate_features):
        """
        Unlocks using Alignment Helper Data + 2D Match.
        """
        # Unpack
        vault = vault_package['vault'] if 'vault' in vault_package else vault_package
        helper_data = vault_package.get('helper_data', [])
        
        # 0. Alignment Step
        # If we have helper data and candidates are dicts (minutiae), align!
        # Need FingerprintCore for match
        from backend.fingerprint_core import fp_core
        
        candidates_xy = []
        
        if helper_data and candidate_features and isinstance(candidate_features[0], dict):
            # Align Candidate -> Helper
            score, transform = fp_core.match_fingerprints(helper_data, candidate_features)
            print(f"[FuzzyVault] Alignment Score: {score:.3f}")
            
            if score > 0.1 and transform:
                rot_deg, c1, c2 = transform
                # Apply transform to candidates
                # m_aligned = R * (m - c2) + c1 
                # (Rotate Query(c2) to match Template(c1))
                # Note on match_fingerprints: it searched rotation of M2 (Query) to match M1 (Template)
                # So we apply best_transform to M2.
                
                rot_rad = np.deg2rad(rot_deg)
                cos_t, sin_t = np.cos(rot_rad), np.sin(rot_rad)
                
                for m in candidate_features:
                    # Centered
                    tx = m['x'] - c2[0]
                    ty = m['y'] - c2[1]
                    
                    # Rotated
                    rx = tx * cos_t - ty * sin_t
                    ry = tx * sin_t + ty * cos_t
                    
                    # Shifted to M1
                    fx = rx + c1[0]
                    fy = ry + c1[1]
                    
                    candidates_xy.append((int(fx), int(fy)))
            else:
                 print("[FuzzyVault] Alignment Failed or Score too low.")
                 candidates_xy = [(int(m['x']), int(m['y'])) for m in candidate_features]
        else:
             # Fallback
             candidates_xy = [(int(x), int(y)) for (x, y) in candidate_features] if not isinstance(candidate_features[0], dict) else [(m['x'], m['y']) for m in candidate_features]

        # 2. Vault Unlock (Standard Logic)
        matches = []
        TOLERANCE = 15 
        TOLERANCE_SQ = TOLERANCE ** 2
        
        for (vu, vv) in vault:
            vx = vu // 1000
            vy = vu % 1000
            
            best_dist_sq = float('inf')
            
            for (cx, cy) in candidates_xy:
                if abs(vx - cx) > TOLERANCE: continue 
                if abs(vy - cy) > TOLERANCE: continue
                
                dist_sq = (vx - cx)**2 + (vy - cy)**2
                if dist_sq < best_dist_sq:
                    best_dist_sq = dist_sq
            
            if best_dist_sq <= TOLERANCE_SQ:
                matches.append((vu, vv))
        
        matches = list(set(matches))
        print(f"[FuzzyVault] Unlocking... Vault Size: {len(vault)}, Candidates: {len(candidates_xy)}")
        if vault:
            vx, vy = vault[0][0] // 1000, vault[0][0] % 1000
            print(f"[Debug] Vault[0] (Genuine): ({vx}, {vy})")
        if candidates_xy:
             print(f"[Debug] Candidate[0] (Aligned): {candidates_xy[0]}")
             
        print(f"[FuzzyVault] Matches Found: {len(matches)} (Required: {self.degree + 2})")
        
        if len(matches) < self.degree + 2:
            return None, 0.0
            
        # 3. RANSAC
        iterations = 1000 # Reduced for speed
        for _ in range(iterations):
            try:
                sample = random.sample(matches, self.degree + 1)
                sus = [p[0] / 1000000.0 for p in sample]
                if len(set(sus)) < len(sus): continue
                sv = [p[1] for p in sample]
                
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', np.RankWarning)
                    z = np.polyfit(sus, sv, self.degree)
                    rec_poly = np.poly1d(z)
                
                inliers_count = 0
                for (mu, mv) in matches:
                    if abs(rec_poly(mu / 1000000.0) - mv) < 2000: 
                        inliers_count += 1
                
                if inliers_count < self.degree + 3: 
                    # print(f"  [RANSAC] Low Inliers: {inliers_count}")
                    continue
                
                rec_secret = int(round(rec_poly.coeffs[-1]))
                rec_crc = int(round(rec_poly.coeffs[-2]))
                
                try:
                     if rec_secret < 0: rec_secret = abs(rec_secret)
                     data = struct.pack('<I', rec_secret)
                except: 
                     continue
                    
                calc_crc = self._compute_crc(data) 
                
                if calc_crc == rec_crc:
                    print(f"[FuzzyVault] SUCCESS! Secret: {rec_secret} (Inliers: {inliers_count})")
                    return rec_secret, 1.0 
                else:
                    if _ % 100 == 0:
                        print(f"  [RANSAC] CRC Mismatch. Rec: {rec_secret}, CRC: {rec_crc} vs {calc_crc}. (Inliers: {inliers_count})")
                        
            except Exception as e: 
                # print(f"RANSAC Error: {e}")
                pass
        
        print("[FuzzyVault] RANSAC Failed to find valid secret.")
        return None, 0.0
