import os
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
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
