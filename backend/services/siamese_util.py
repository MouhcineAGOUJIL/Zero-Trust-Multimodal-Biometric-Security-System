import tensorflow as tf
from tensorflow.keras import layers, Model, applications
import numpy as np

def build_embedding_model(input_shape=(224, 224, 3)):
    """
    Base Feature Extractor (MobileNetV2).
    """
    base_model = applications.MobileNetV2(
        weights='imagenet', 
        include_top=False, 
        pooling='avg', 
        input_shape=input_shape
    )
    
    # Freeze early layers to avoid destroying ImageNet features on small data
    # Fine-tune only the top layers
    for layer in base_model.layers[:-20]:
        layer.trainable = False
        
    inputs = layers.Input(shape=input_shape)
    x = applications.mobilenet_v2.preprocess_input(inputs) # Important!
    x = base_model(x)
    
    # Add a Dense layer to compress to 128 dimensions (Common for Metric Learning)
    # L2 Normalization is crucial for Siamese Networks (Embeddings on hypersphere)
    # Using explicit output_shape to avoid load errors
    x = layers.Dense(128, activation=None)(x)
    outputs = layers.Lambda(lambda v: tf.math.l2_normalize(v, axis=1), output_shape=(128,))(x)
    
    return Model(inputs, outputs, name="EmbeddingModel")

class SiameseNetwork(Model):
    def __init__(self, embedding_model):
        super(SiameseNetwork, self).__init__()
        self.embedding_model = embedding_model

    def call(self, inputs):
        anchor, positive, negative = inputs
        emb_a = self.embedding_model(anchor)
        emb_p = self.embedding_model(positive)
        emb_n = self.embedding_model(negative)
        return emb_a, emb_p, emb_n

    def train_step(self, data):
        # Unpack the data
        anchor, positive, negative = data # (batch, 224, 224, 3)

        with tf.GradientTape() as tape:
            # Forward pass
            emb_a, emb_p, emb_n = self( [anchor, positive, negative], training=True)
            
            # Compute Triplet Loss
            # d(A, P) = ||A - P||^2
            # d(A, N) = ||A - N||^2
            # Loss = max(d(A, P) - d(A, N) + margin, 0)
            
            margin = 0.5
            dist_ap = tf.reduce_sum(tf.square(emb_a - emb_p), axis=1)
            dist_an = tf.reduce_sum(tf.square(emb_a - emb_n), axis=1)
            
            loss = tf.maximum(dist_ap - dist_an + margin, 0.0)
            loss = tf.reduce_mean(loss)

        # Compute gradients
        trainable_vars = self.embedding_model.trainable_variables
        gradients = tape.gradient(loss, trainable_vars)
        
        # Update weights
        self.optimizer.apply_gradients(zip(gradients, trainable_vars))
        
        return {"loss": loss}
