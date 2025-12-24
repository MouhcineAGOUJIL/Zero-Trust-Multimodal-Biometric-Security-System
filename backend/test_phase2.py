import requests
import os

BASE_URL = "http://127.0.0.1:8000"

# User Data
USER_A = "alice_secure"
IMG_A = "/home/red/.gemini/antigravity/brain/2a5148a9-5964-47a2-a626-ed56d9184a9b/person_a_face_1766512670673.png"

USER_C = "charlie_impostor" # Not enrolled, but tries to spoof Alice
IMG_C = "/home/red/.gemini/antigravity/brain/2a5148a9-5964-47a2-a626-ed56d9184a9b/person_c_face_1766601084823.png"

def test_enrollment():
    print(f"\n[*] Testing Enrollment for {USER_A}...")
    with open(IMG_A, "rb") as f:
        files = {"file": f}
        data = {"username": USER_A}
        response = requests.post(f"{BASE_URL}/auth/enroll", files=files, data=data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        print("✅ Enrollment Successful")
    else:
        print("❌ Enrollment Failed")

def test_verify_valid():
    print(f"\n[*] Testing Valid Verification for {USER_A}...")
    with open(IMG_A, "rb") as f:
        files = {"file": f}
        data = {"username": USER_A}
        response = requests.post(f"{BASE_URL}/auth/verify", files=files, data=data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200 and response.json().get("authenticated") is True:
        print("✅ Validation Successful")
    else:
        print("❌ Validation Failed")

def test_verify_impostor():
    print(f"\n[*] Testing Impostor Attack (Charlie pretending to be Alice)...")
    with open(IMG_C, "rb") as f:
        files = {"file": f}
        data = {"username": USER_A} # Charlie CLAIMS to be Alice
        response = requests.post(f"{BASE_URL}/auth/verify", files=files, data=data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # We expect authenticated: False
    if response.json().get("authenticated") is False:
        print("✅ Impostor Properly Rejected")
    else:
        print("❌ Impostor Incorrectly Accepted!")

if __name__ == "__main__":
    try:
        # Check if server is up
        r = requests.get(BASE_URL)
        print(f"Server Status: {r.json()}")
        
        test_enrollment()
        test_verify_valid()
        test_verify_impostor()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Is the server running?")
