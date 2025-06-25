import os
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity # or alternative similarity function
from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
    model = HuggingFaceEmbeddings(
        model_name=os.getenv("HF_EMBEDDINGS_REPO"),
        cache_folder=os.getenv("HF_CACHE_DIR"),
        model_kwargs = {"device": "cuda"} # cpu or cuda
    )
    sentences = [
        "Roses are red.",
        "Violets are blue.",
        "A computer is a machine that can be programmed to carry out sequences of arithmetic or logical operations automatically.",
    ]

    embeddings = model.embed_documents(sentences) # normalization not needed if we use cosine similarity
    cosine_similarities = cosine_similarity(embeddings)
    cosine_distances = 1 - cosine_similarities
    print("Cosine similarities:")
    print(cosine_similarities)
    print("Cosine distances:")
    print(cosine_distances)
