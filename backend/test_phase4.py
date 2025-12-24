import requests
import json

BASE_URL = "http://127.0.0.1:8000"
USER = "alice_multimodal"
IMG_FACE = "/home/red/.gemini/antigravity/brain/2a5148a9-5964-47a2-a626-ed56d9184a9b/person_a_face_1766512670673.png"
IMG_FINGER_A = "finger_a.png"
IMG_FINGER_B = "finger_b.png" # Wrong finger

def run_test():
    # 1. Enroll Multimodal
    print("[*] Enrolling Fac + Finger A...")
    files = {
        "file": open(IMG_FACE, "rb"),
        "file_finger": open(IMG_FINGER_A, "rb")
    }
    r = requests.post(f"{BASE_URL}/auth/enroll", data={"username": USER}, files=files)
    try:
        print(r.json())
    except:
        print(f"FAILED TO DECODE JSON. Status: {r.status_code}")
        print(f"Raw Body: {r.text}")

    # 2. Verify Correct (Face + Finger A)
    print("\n[*] Verify Valid (Should be High Score)...")
    files = {
        "file": open(IMG_FACE, "rb"),
        "file_finger": open(IMG_FINGER_A, "rb")
    }
    r = requests.post(f"{BASE_URL}/auth/verify", data={"username": USER}, files=files)
    print(r.json())

    # 3. Verify Partial Impostor (Face + Finger B)
    print("\n[*] Verify Partial Impostor (Wrong Finger)...")
    files = {
        "file": open(IMG_FACE, "rb"),
        "file_finger": open(IMG_FINGER_B, "rb")
    }
    r = requests.post(f"{BASE_URL}/auth/verify", data={"username": USER}, files=files)
    # Expect lower score but Access might still be granted if Face Weight (0.6) + Trust (1.0) is high enough
    # But Finger score should be 0.
    print(r.json())

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(e)
