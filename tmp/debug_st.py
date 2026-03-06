import sys
from sentence_transformers import SentenceTransformer
import os

model_id = "BAAI/bge-m3"
print(f"Attempting to load model: {model_id}")

try:
    model = SentenceTransformer(model_id, trust_remote_code=False)
    print("Model loaded successfully!")
    embedding = model.encode("Test sentence")
    print(f"Embedding shape: {embedding.shape}")
except Exception as e:
    print(f"Error loading model: {e}")
    import traceback

    traceback.print_exc()
