import os
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()


# Path to locally store the model
# Load on import
EMBEDDER = HuggingFaceEmbeddings(
    model_name=os.getenv("HF_EMBEDDINGS_REPO"),
    cache_folder=os.getenv("HF_CACHE_DIR"),
    model_kwargs={"device": "cuda"},
    encode_kwargs={"batch_size": 10} # normalize_embeddings=False by default
)


# Optional test
if __name__ == "__main__":
    sample = ["RAG systems retrieve knowledge.", "Language models generate text."]
    vectors = EMBEDDER.embed_documents(sample)
    print(f"Generated {len(vectors)} embeddings with dimension {len(vectors[0])}")
