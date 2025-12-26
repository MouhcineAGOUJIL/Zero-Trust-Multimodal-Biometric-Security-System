import os
import glob
import numpy as np
import cv2
import tensorflow as tf
from collections import defaultdict
from backend.services.siamese_util import build_embedding_model, SiameseNetwork
import random

# Configuration
DB_PATH = "/home/red/Documents/S5/Biom Sec/DB2_B"
EPOCHS = 3
BATCH_SIZE = 16
IMG_SIZE = (224, 224)

def load_data(path):
    print(f"Loading data from {path}...")
    files = sorted(glob.glob(os.path.join(path, "*.tif")))
    user_images = defaultdict(list)
    
    cnt = 0
    for f in files:
        basename = os.path.basename(f)
        try:
            parts = basename.split('_')
            uid = parts[0]
            
            # Load and Preprocess Here (to save memory during training loop? No, 80 imgs fit in RAM)
            img = cv2.imread(f)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, IMG_SIZE)
            
            user_images[uid].append(img)
            cnt += 1
        except:
            pass
            
    print(f"Loaded {cnt} images from {len(user_images)} users.")
    return user_images

def generate_triplets(user_images, num_triplets=1000):
    users = list(user_images.keys())
    anchors = []
    positives = []
    negatives = []
    
    print(f"Generating {num_triplets} triplets...")
    
    for _ in range(num_triplets):
        # 1. Pick Anchor User
        uid = random.choice(users)
        samples = user_images[uid]
        if len(samples) < 2: continue # Need at least 2 for A and P
        
        # 2. Pick Anchor and Positive
        a_idx, p_idx = random.sample(range(len(samples)), 2)
        anchors.append(samples[a_idx])
        positives.append(samples[p_idx])
        
        # 3. Pick Negative User
        neg_uid = random.choice(users)
        while neg_uid == uid:
            neg_uid = random.choice(users)
            
        # 4. Pick Negative Sample
        neg_samples = user_images[neg_uid]
        if not neg_samples: continue
        n_idx = random.choice(range(len(neg_samples)))
        negatives.append(neg_samples[n_idx])
        
    return np.array(anchors), np.array(positives), np.array(negatives)

def train():
    # 1. Load Data
    data = load_data(DB_PATH)
    if len(data) < 2:
        print("Not enough users to train.")
        return

    # 2. Build Model
    embedding_model = build_embedding_model()
    siamese_model = SiameseNetwork(embedding_model)
    siamese_model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001))
    
    # 3. Generate Training Data
    # Since dataset is tiny (10 users), we generate a lot of random pairs
    anchors, positives, negatives = generate_triplets(data, num_triplets=2000)
    
    # Bundle into Dataset
    dataset = tf.data.Dataset.from_tensor_slices((anchors, positives, negatives))
    dataset = dataset.shuffle(buffer_size=1024).batch(BATCH_SIZE)
    
    print("Starting Training...")
    history = siamese_model.fit(
        dataset,
        epochs=EPOCHS
    )
    
    # 4. Save Model
    save_path = "fingerprint_siamese.keras"
    embedding_model.save(save_path)
    print(f"Model saved to {save_path}")

if __name__ == "__main__":
    train()
