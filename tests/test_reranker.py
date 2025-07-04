import os
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"


def test_reranker():
    reranker = HuggingFaceCrossEncoder(
        model_name=os.getenv("HF_RERANKER_REPO"),
        model_kwargs={"cache_folder": os.getenv("HF_CACHE_DIR"), "device": "cpu"} # cuda out of memory
    )
    query = "How do you play the game of basketball?"
    documents = [
        "Basketball is a team sport in which two teams, most commonly of five players each, opposing one another on a rectangular court, compete to shoot the ball through the opponent's hoop.",
        "The game of basketball is played with a round ball that is thrown through a hoop to score points.",
        "In baseball, two teams take turns batting and fielding. The batting team attempts to score runs by hitting a ball thrown by the pitcher and running around a series of bases."
    ]

    text_pairs = [(query, doc) for doc in documents]
    similarity_scores = reranker.score(text_pairs)
    print(similarity_scores)

    assert len(similarity_scores) == len(documents), "The number of similarity scores should match the number of documents."
    assert similarity_scores[0] > similarity_scores[2], "The first document should be more relevant than the third."
    assert similarity_scores[1] > similarity_scores[2], "The second document should also be more relevant than the third."


if __name__ == "__main__":
    test_reranker()
