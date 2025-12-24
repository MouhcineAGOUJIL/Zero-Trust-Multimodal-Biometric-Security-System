import random
import numpy as np
from scipy.interpolate import lagrange

class FuzzyVault:
    def __init__(self, polynomial_degree=4, vault_size=200):
        self.degree = polynomial_degree
        self.vault_size = vault_size

    def lock(self, secret_int, features):
        """
        Locks a secret (integer) using a set of features (x, y).
        1. Encodes secret into a Polynomial P(x).
        2. Projects legitimate features onto P(x) -> (x, P(x)).
        3. Adds Chaff points (random noise) -> (rx, ry).
        Returns the Vault (list of points).
        """
        # 1. Encode Secret: 
        # For simplicity, we make the secret the constant term (coefficient 0)
        # and random other coefficients.
        coefficients = [secret_int] + [random.randint(1, 100) for _ in range(self.degree)]
        poly = np.poly1d(coefficients[::-1]) # numpy expects highest degree first

        vault = []

        # 2. Project Real Points (Genuine Set)
        # We use the X coordinate of the feature as the input 'x'
        # We assume X coordinates are unique enough or we handle collisions
        track_x = set()
        for (x, y) in features:
            # We combine x and y to make a single robust 'x' for the polynomial
            # or just use x. Let's use x + y to utilize both dimensions.
            # CAUTION: 'x' for polynomial must be unique.
            poly_x = x + y  
            if poly_x in track_x:
                continue
            track_x.add(poly_x)
            
            poly_y = int(poly(poly_x)) # Cast to int for simplicity and compatibility
            vault.append((int(poly_x), poly_y))

        # 3. Add Chaff Points (Noise)
        while len(vault) < self.vault_size:
            rx = random.randint(0, 1000)
            ry = random.randint(0, 1000000)
            if rx not in track_x:
                vault.append((rx, ry))
                track_x.add(rx)

        # Shuffle to hide which points are real
        random.shuffle(vault)
        return vault

    def unlock(self, vault, candidate_features):
        """
        Unlocks existing vault using candidate features.
        1. Find points in vault that match candidate features (Projection).
        2. If enough points match ( > degree + delta), try to interpolate.
        3. Recover secret.
        """
        matches = []
        
        # Candidate projection
        candidate_x_set = set()
        for (x, y) in candidate_features:
            candidate_x_set.add(x + y)

        # Find intersections
        for (vx, vy) in vault:
            if vx in candidate_x_set:
                matches.append((vx, vy))

        print(f"[FuzzyVault] Vault Size: {len(vault)}")
        print(f"[FuzzyVault] Candidate X Set Size: {len(candidate_x_set)}")
        print(f"[FuzzyVault] Found {len(matches)} matching points (Need {self.degree + 1})")

        if len(matches) <= self.degree:
            print("[FuzzyVault] Not enough matches to interpolate.")
            return None, 0.0 # Failed

        # Try Polyfit (Least Squares) which is more stable than Lagrange for high offsets
        x_points = [m[0] for m in matches]
        y_points = [m[1] for m in matches]
        
        try:
            # Fit polynomial of 'degree'
            # We use all matches because we assume chaff collisions are rare
            # In production: RANSAC would be needed.
            z = np.polyfit(x_points, y_points, self.degree)
            poly = np.poly1d(z)
            
            # Secret is poly(0) aka the last coefficient
            # polyfit returns highest degree first.
            secret = int(round(poly(0)))
            
            # Simple Trust Score: What % of necessary points did we find?
            score = min(1.0, len(matches) / (self.degree * 2))
            
            return secret, score
        except Exception as e:
            print(f"Error interpolating: {e}")
            return None, 0.0
