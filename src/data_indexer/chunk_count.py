from src.chatbot.langchain_components import *


if __name__ == "__main__":
    # print the nuber of stored chunks
    print(f"Simulation vectorstore chunks: {SIMULATION_VECTORSTORE._collection.count()}")
    print(f"Analysis vectorstore chunks: {ANALYSIS_VECTORSTORE._collection.count()}")
    # as of 28. 8. 2025
    # 1909
    # 3531
