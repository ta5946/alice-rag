import os
from sklearn.metrics.pairwise import cosine_similarity # or alternative similarity function
from src.chatbot.langchain_components import EMBEDDINGS
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"


def test_embeddings():
    sentences = [
        "Roses are red.",
        "Violets are blue.",
        "A computer is a machine that can be programmed to carry out sequences of arithmetic or logical operations automatically.",
    ]

    embeddings = EMBEDDINGS.embed_documents(sentences)
    cosine_similarities = cosine_similarity(embeddings)
    cosine_distances = 1 - cosine_similarities
    print("Cosine similarities:")
    print(cosine_similarities)
    print("Cosine distances:")
    print(cosine_distances)

    assert len(embeddings) == len(sentences), "The number of embeddings should match the number of sentences."
    assert len(embeddings[0]) > 0, "Each embedding should have more than zero dimensions."
    assert cosine_similarities[0][0] > 0.99, "The similarity of the first sentence with itself should be close to 1."
    assert cosine_similarities[0][1] > cosine_similarities[0][2], "The first sentence should be more similar to the second than to the third."


if __name__ == "__main__":
    test_embeddings()
