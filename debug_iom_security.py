import numpy as np
import random
from backend.services.iom_service import IoMService

def generate_random_minutiae(count=50):                 # More realistic count
    minutiae = []
    for _ in range(count):
        minutiae.append({
            'x': random.randint(50, 250),              # Centered distribution
            'y': random.randint(50, 300),
            'angle': random.random() * 360
        })
    return minutiae

def test_iom_collisions():
    service = IoMService(key_len=256, grid_size=64)
    
    # 1. Generate two DIFFERENT sets of minutiae
    f1 = generate_random_minutiae(40)
    f2 = generate_random_minutiae(40) # Different random seed implicitly
    
    seed = 123456789 # Same secret key (simulating same user, different fingerprint? No, different user w/ different fingers)
    # Actually, verification compares:
    # Template: (Feature A, Key A)
    # Query:    (Feature B, Key A)
    # So we use MATCHING keys but DIFFERENT features (Imposter scenario with stolen/leaked key? No, normal verify).
    
    # Wait, in Verify, we use the User's stored template key.
    # Scenario: Imposter claims to be User A.
    # System loads User A's Key.
    # System extracts Imposter's Features.
    # System Hashes(ImposterFeat, UserAKey).
    # System Compares H(Imposter) vs H(UserA).
    
    print("--- Test 1: Imposter Scenario (Different Finger, Same Key) ---")
    h1 = service.generate_iom_hash(f1, seed)
    h2 = service.generate_iom_hash(f2, seed)
    
    match, score = service.match_iom(h1, h2)
    print(f"Finger 1 Hash: {h1[:20]}...")
    print(f"Finger 2 Hash: {h2[:20]}...")
    print(f"Score: {score:.4f} (Should be low, around 0.5)")
    print(f"Match: {match}")
    
    print("\n--- Test 2: Genuine Scenario (Same Finger, Same Key) ---")
    # Perturb F1 slightly to simulate intra-class variation
    f1_prime = []
    for m in f1:
        f1_prime.append({
            'x': m['x'] + random.randint(-5, 5),
            'y': m['y'] + random.randint(-5, 5),
            'angle': m['angle']
        })
        
    h1_prime = service.generate_iom_hash(f1_prime, seed)
    match_gen, score_gen = service.match_iom(h1, h1_prime)
    print(f"Finger 1' Hash: {h1_prime[:20]}...")
    print(f"Score: {score_gen:.4f} (Should be high, > 0.7)")
    print(f"Match: {match_gen}")

if __name__ == "__main__":
    test_iom_collisions()
