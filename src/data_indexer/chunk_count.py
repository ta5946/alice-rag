from src.chatbot.langchain_components import *


if __name__ == "__main__":
    # print the nuber of stored chunks
    print(f"Simulation and analysis vectorstore chunks: {DB.base_retriever.vectorstore._collection.count()}")
    # as of 28. 8. 2025
    # 1909 for simulation
    # 3531 for both
