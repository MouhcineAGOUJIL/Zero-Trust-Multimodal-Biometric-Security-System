import numpy as np
import random
import os
from scipy.ndimage import gaussian_filter

class IoMService:
    def __init__(self, key_len=256, grid_size=64):
        """
        IoM Service for Minutiae Sets.
        Uses Random Projections on a Minutiae Density Grid.
        """
        self.key_len = key_len
        self.grid_size = grid_size
        
    def _minutiae_to_grid(self, minutiae, size=256):
        """
        Convert list of minutiae dicts to a 3-channel feature grid (Density, Cos, Sin).
        Returns: Flattened vector of size (3 * grid_size^2)
        """
        grid_den = np.zeros((self.grid_size, self.grid_size), dtype=np.float32)
        grid_cos = np.zeros((self.grid_size, self.grid_size), dtype=np.float32)
        grid_sin = np.zeros((self.grid_size, self.grid_size), dtype=np.float32)
        
        if not minutiae: 
            return np.concatenate([grid_den.flatten(), grid_cos.flatten(), grid_sin.flatten()])
        
        xs = [m['x'] for m in minutiae]
        ys = [m['y'] for m in minutiae]
        
        # Center the minutiae (Translation Invariance)
        center_x = sum(xs) / len(xs)
        center_y = sum(ys) / len(ys)
        
        # Fixed Scaling (Preserve Relative Distances)
        # Using 64/300 scale
        scale = self.grid_size / 300.0  
        
        for m in minutiae:
            # Map to grid coords (Centered)
            gx = int((m['x'] - center_x) * scale + self.grid_size/2)
            gy = int((m['y'] - center_y) * scale + self.grid_size/2)
            
            # Add with Splatting
            if 0 <= gx < self.grid_size and 0 <= gy < self.grid_size:
                grid_den[gy, gx] += 1.0
                
                # Angle encoding
                angle = np.deg2rad(m['angle'])
                grid_cos[gy, gx] += np.cos(angle)
                grid_sin[gy, gx] += np.sin(angle)
        
        # Smooth all channels
        sigma = 1.0 # Slightly less smoothing than before since we have more data
        grid_den = gaussian_filter(grid_den, sigma=sigma)
        grid_cos = gaussian_filter(grid_cos, sigma=sigma)
        grid_sin = gaussian_filter(grid_sin, sigma=sigma)
                            
        return np.concatenate([grid_den.flatten(), grid_cos.flatten(), grid_sin.flatten()])

    def generate_iom_hash(self, features, seed_token):
        """
        Generate IoM Hash from features (Minutiae Set OR Dense Vector).
        seed_token: Integer seed for reproducibility (Key).
        """
        # 1. Feature Extraction / Normalization
        if isinstance(features, list):
            # It's a Minutiae List -> Convert to Grid
            feature_vector = self._minutiae_to_grid(features)
        elif isinstance(features, np.ndarray):
            # It's a Dense Vector (CNN Embedding) -> Use as is
            feature_vector = features.flatten()
        else:
            return None
        
        # 2. Random Projection
        np.random.seed(seed_token % (2**32))
        
        # Determine Input Dimension dynamically from vector
        input_dim = len(feature_vector)
        
        # Random Measurement Matrix (key_len x input_dim)
        # Optimization: Don't generate huge matrix. Use loop or sparse logic if needed.
        # For prototype, generating (256, 1280) is fine.
        projection_matrix = np.random.randn(self.key_len, input_dim)
        
        # Project
        projected = np.dot(projection_matrix, feature_vector)
        
        # Binarize
        hash_bits = (projected > 0).astype(int)
        
        # Convert to single integer
        hash_int = 0
        for b in hash_bits:
            hash_int = (hash_int << 1) | int(b)
            
        return str(hash_int)

    def match_iom(self, hash1_str, hash2_str, threshold=0.65):
        """
        Hamming Distance matching.
        """
        try:
            h1 = int(hash1_str)
            h2 = int(hash2_str)
        except:
            return False, 0.0
            
        # XOR to find differing bits
        diff = h1 ^ h2
        
        # Count set bits (Hamming Distance)
        dist = bin(diff).count('1')
        
        # Normalized score
        score = 1.0 - (dist / self.key_len)
        
        # Threshold Check
        return (score > threshold), score
