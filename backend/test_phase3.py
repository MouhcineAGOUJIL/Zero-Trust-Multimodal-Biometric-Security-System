import requests
import time

BASE_URL = "http://127.0.0.1:8000"
USER = "alice_context"
IMG = "/home/red/.gemini/antigravity/brain/2a5148a9-5964-47a2-a626-ed56d9184a9b/person_a_face_1766512670673.png"

def test_context_flow():
    # 1. Enroll (Trusted IP = 127.0.0.1)
    print(f"[*] Enrolling {USER} from Trusted IP...")
    with open(IMG, "rb") as f:
        r = requests.post(f"{BASE_URL}/auth/enroll", data={"username": USER}, files={"file": f})
    print(r.json())
    
    # 2. Verify from SAME IP (Should Pass)
    print(f"\n[*] Verifying from SAME IP (127.0.0.1)...")
    with open(IMG, "rb") as f:
        r = requests.post(f"{BASE_URL}/auth/verify", data={"username": USER}, files={"file": f})
    res = r.json()
    print(res)
    
    if res['authenticated'] and "Trust: 1.0" in res['message']:
        print("✅ High Trust Access Granted")
    else:
        print("❌ Unexpected Rejection")

    # Note: We cannot easily simulate a different IP locally without mocking the Request object
    # or using a proxy. For this PoC script, we are verifying that the Logic *exists* and defaults to 1.0 locally.
    # To truly test "Untrusted IP", we would need to manually modify the DB or use a proxy.

if __name__ == "__main__":
    try:
        test_context_flow()
    except Exception as e:
        print(f"Error: {e}")
