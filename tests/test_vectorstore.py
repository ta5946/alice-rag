import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(
        model_name=os.getenv("HF_EMBEDDINGS_REPO"),
        cache_folder=os.getenv("HF_CACHE_DIR"),
        model_kwargs = {"device": "cuda"}
    )
    chroma_vectorstore = Chroma(
        persist_directory=os.getenv("CHROMA_DIR"),
        embedding_function=embeddings,
        collection_name="chroma_docs",
        relevance_score_fn=lambda distance: 1 - distance
    ) # created in indexer folder
    query = "How to obtain a valid alien token to run the O2 simulation?"

    result = chroma_vectorstore.similarity_search_with_relevance_scores(query, k=int(os.getenv("CHROMA_TOP_K")))
    print("Retrieved documents:")
    for doc in result:
        print(doc) # by default chroma stores cosine distance = 1 - cosine similarity and returns the relevance score

    """
    chroma_retriever = chroma_vectorstore.as_retriever(
        search_type="similarity_score_threshold", 
        search_kwargs={"k": int(os.getenv("CHROMA_TOP_K")), "score_threshold": 0.6}
    ) # generalized retriever class
    result = chroma_retriever.invoke(query)
    print("Retrieved documents with score threshold:")
    for doc in result:
        print(doc) # top k documents with a relevance score above the threshold
    """
