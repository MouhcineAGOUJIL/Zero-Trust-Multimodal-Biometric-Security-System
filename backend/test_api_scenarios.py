
import requests
import os
import glob

BASE_URL = "http://127.0.0.1:8000/auth"
DATASET_PATH = "/home/red/Documents/S5/Biom Sec/Project/LUTBIO sample data"

def get_file_path(uid, modality):
    # modality: face, finger, palm_touch
    path = os.path.join(DATASET_PATH, uid, modality)
    files = sorted(glob.glob(os.path.join(path, "*")))
    return files[0] if files else None

def test_face(username, file_path, expected_result):
    print(f"[-] Testing FACE for {username} using {os.path.basename(file_path)}...")
    url = f"{BASE_URL}/verify/face"
    files = {'file': open(file_path, 'rb')}
    data = {'username': username}
    
    try:
        r = requests.post(url, data=data, files=files)
        res = r.json()
        print(f"    Result: {res['message']}")
        success = res['authenticated'] == expected_result
        print(f"    PASS: {success} (Expected: {expected_result})")
    except Exception as e:
        print(f"    ERROR: {e}")

def test_palm(username, file_path, expected_result):
    print(f"[-] Testing PALM for {username} using {os.path.basename(file_path)}...")
    url = f"{BASE_URL}/verify/palm"
    files = {'file_palm': open(file_path, 'rb')}
    data = {'username': username}
    
    try:
        r = requests.post(url, data=data, files=files)
        res = r.json()
        print(f"    Result: {res['message']}")
        success = res['authenticated'] == expected_result
        print(f"    PASS: {success} (Expected: {expected_result})")
    except Exception as e:
        print(f"    ERROR: {e}")

def main():
    print("=== SCENARIO 1: Valid User 120 (Face) ===")
    f120 = get_file_path("120", "face")
    test_face("user120", f120, True)

    print("\n=== SCENARIO 2: Valid User 120 (Palm) ===")
    p120 = get_file_path("120", "palm_touch")
    test_palm("user120", p120, True)

    print("\n=== SCENARIO 3: Imposter Attack on User 120 (User 162's Face) ===")
    f162 = get_file_path("162", "face")
    test_face("user120", f162, False)

    print("\n=== SCENARIO 4: Imposter Attack on User 120 (User 162's Palm) ===")
    p162 = get_file_path("162", "palm_touch")
    test_palm("user120", p162, False)

    print("\n=== SCENARIO 5: Valid User 303 (Palm) ===")
    p303 = get_file_path("303", "palm_touch")
    test_palm("user303", p303, True)

    print("\n=== SCENARIO 6: Imposter Attack on User 303 (User 273's Palm) ===")
    p273 = get_file_path("273", "palm_touch")
    test_palm("user303", p273, False)

if __name__ == "__main__":
    main()
