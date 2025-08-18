from src.chatbot.langchain_components import CHROMA_COLLECTION

if __name__ == "__main__":
    # print the nuber of stored chunks
    print(CHROMA_COLLECTION.count())
    # 2900 chunks for chunk size 1000 (best)
    # 5200 chunks for chunk size 1000 + synthetic medium qa pairs
    # 9000 chunks for chunk size 1000 + synthetic easy, medium and hard qa pairs
    # 1450 chunks for chunk size 2000 - checks out
    # 3700 chunks for similarity threshold 0.9
