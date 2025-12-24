import numpy as np
import dlib
import cv2
import os
import secrets

class BiometricService:
    def __init__(self, shape_path="shape_predictor_68_face_landmarks.dat", rec_path="dlib_face_recognition_resnet_model_v1.dat"):
        self.detector = None
        self.predictor = None
        self.face_rec = None
        self.models_loaded = False
        self._load_models(shape_path, rec_path)

    def _load_models(self, shape_path, rec_path):
        try:
            # Look for models in current dir or parent dir (flexible pathing)
            possible_paths = [
                shape_path,
                os.path.join("..", shape_path),
                os.path.join(os.getcwd(), shape_path)
            ]
            
            final_shape = next((p for p in possible_paths if os.path.exists(p)), None)
            
            # Similar logic for recognition model
            possible_rec_paths = [
                rec_path,
                os.path.join("..", rec_path),
                os.path.join(os.getcwd(), rec_path)
            ]
            final_rec = next((p for p in possible_rec_paths if os.path.exists(p)), None)

            if final_shape and final_rec:
                self.detector = dlib.get_frontal_face_detector()
                self.predictor = dlib.shape_predictor(final_shape)
                self.face_rec = dlib.face_recognition_model_v1(final_rec)
                self.models_loaded = True
                print("[+] Biometric Models Loaded Successfully")
            else:
                print("[-] Error: Biometric models not found.")
        except Exception as e:
            print(f"[-] Error loading models: {e}")

    def extract_features_from_buffer(self, image_bytes):
        """Extracts 128d features from image bytes (e.g., uploaded file)."""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded")

        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        dets = self.detector(rgb_img, 1)

        if len(dets) == 0:
            return None

        # Process first face
        shape = self.predictor(rgb_img, dets[0])
        face_descriptor = self.face_rec.compute_face_descriptor(rgb_img, shape)
        return np.array(face_descriptor)

    def generate_token(self):
        """Generates a secure random integer token."""
        return secrets.randbits(32)

    def generate_biohash(self, feature_vector, token_seed, hash_length=128):
        """Projects features onto random basis defined by token_seed."""
        np.random.seed(token_seed)
        feature_len = len(feature_vector)
        # Generate random projection matrix
        projection_matrix = np.random.randn(feature_len, hash_length)
        
        # Project
        projected = np.dot(feature_vector, projection_matrix)
        
        # Binarize (Threshold 0)
        biohash = (projected > 0).astype(int)
        
        # Return as string '10101...' for storage
        return "".join(map(str, biohash))

    def match_biohashes(self, hash_str1, hash_str2, threshold=0.15):
        """Calculates Hamming Distance between two hash strings."""
        if len(hash_str1) != len(hash_str2):
            return False, 1.0

        # Convert strings back to arrays
        h1 = np.array([int(c) for c in hash_str1])
        h2 = np.array([int(c) for c in hash_str2])
        
        distance = np.count_nonzero(h1 != h2) / len(h1)
        return distance < threshold, distance
