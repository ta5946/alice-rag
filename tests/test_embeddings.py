from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity # or alternative similarity function


model = SentenceTransformer("BAAI/bge-base-en-v1.5", cache_folder="./models/huggingface", device="cuda") # cpu or cuda
sentences = [
    "Roses are red.",
    "Violets are blue.",
    "A computer is a machine that can be programmed to carry out sequences of arithmetic or logical operations automatically.",
]

embeddings = model.encode(sentences) # normalization not needed if we use cosine similarity
similarities = model.similarity(embeddings, embeddings)
print(similarities)
