# Functions concering the embedding model; this is used to index into a vector database
import os
from typing import List
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import normalize_embeddings
import torch # for normalization

# Path to locally store the model
LOCAL_MODEL_DIR = "local_models/bge-base-en-v1.5"
REMOTE_MODEL_NAME = "BAAI/bge-base-en-v1.5"

# Ensure the model is available locally
def get_local_model(path: str = LOCAL_MODEL_DIR, model_name: str = REMOTE_MODEL_NAME) -> SentenceTransformer:
    if not os.path.exists(path):
        print(f"[embedder] Downloading model '{model_name}' to '{path}'...")
        model = SentenceTransformer(model_name)
        model.save(path)
    else:
        print(f"[embedder] Loading model from local path '{path}'")
        model = SentenceTransformer(path)
    return model

# Load on import
model = get_local_model()

def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    Generate normalized embeddings for a list of documents.
    Returns a list of 768-d float vectors.
    """
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_tensor=True)
    # embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    embeddings = normalize_embeddings(embeddings)
    return embeddings.tolist()

# Optional test
if __name__ == "__main__":
    sample = ["RAG systems retrieve knowledge.", "Language models generate text."]
    vecs = embed_documents(sample)
    print(f"Generated {len(vecs)} embeddings with dimension {len(vecs[0])}")
