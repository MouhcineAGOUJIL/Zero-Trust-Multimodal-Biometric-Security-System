import os
import numpy as np
import cv2
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Suppress TF logs
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

class CNNService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CNNService, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def reload_model(self, force_imagenet=False):
        print(f"[CNN] Reloading Model (Force ImageNet: {force_imagenet})...")
        self._load_model(force_imagenet=force_imagenet)

    def _load_model(self, force_imagenet=False):
        # 1. Try Loading Optimized Siamese Model
        model_path = os.path.join(os.getcwd(), 'fingerprint_siamese.keras')
        if not force_imagenet and os.path.exists(model_path):
            print(f"[CNN] Loading Fine-Tuned Siamese Model from {model_path}...")
            try:
                # Workaround for Lambda Serialization: Rebuild and Load Weights
                from backend.services.siamese_util import build_embedding_model
                self._model = build_embedding_model()
                # Load the saved model (which contains weights) into this fresh instance
                # Actually, loading weights from .keras file requires matching topology.
                # Since .keras acts as a zip, let's try calling load_weights directly
                self._model.load_weights(model_path)
                print("[CNN] Siamese Model Loaded (Weights Only). Output Dim: 128")
                return
            except Exception as e:
                print(f"[CNN] Error loading Siamese weights: {e}. Fallback to ImageNet.")

        # 2. Fallback: Pre-trained ImageNet
        print("[CNN] Loading MobileNetV2 (ImageNet weights)...")
        # Re-enable pooling='avg' for compact 1280-dim embedding
        self._model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg', input_shape=(224, 224, 3))
        print("[CNN] Model Loaded Successfully.")

    def extract_features(self, image_input, enhance_ridges=True):
        """
        Extracts a deep feature vector (1280-dim) from an image.
        image_input: filename (str) or bytes or numpy array
        enhance_ridges: bool, set to False for Palm images (prevents texture destruction)
        """
        img = None
        
        # 1. Load Image
        if isinstance(image_input, str):
            img = cv2.imread(image_input)
        elif isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif isinstance(image_input, np.ndarray):
            img = image_input
            if len(img.shape) == 2: # Grayscale
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                
        if img is None:
            print("[CNN] Error loading image")
            return None

        # 2. Preprocess: RIDGE ENHANCEMENT (Binary Skeletal Look)
        # Only Apply if requested (Fingerprints). Skip for Palms.
        
        final_input = img 
        
        if enhance_ridges:
            # Convert to Grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Adaptive Threshold to get ridges (Black ridges on white background)
            ridges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 5)
            # Convert back to BGR (3 channels) for MobileNet
            final_input = cv2.cvtColor(ridges, cv2.COLOR_GRAY2BGR)

        # Resize to 224x224
        img_resized = cv2.resize(final_input, (224, 224))
        
        # Convert to batch
        img_batch = np.expand_dims(img_resized, axis=0)
        
        # Preprocess input (Scale -1 to 1)
        img_preprocessed = preprocess_input(img_batch)
        
        # 3. Predict
        features = self._model.predict(img_preprocessed, verbose=0)
        
        # features shape is (1, 1280)
        return features.flatten()
