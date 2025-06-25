from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        cache_folder="./models/huggingface",
        model_kwargs = {"device": "cuda"}
    )
    chroma_vectorstore = Chroma(
        persist_directory="indexer/chroma_store",
        embedding_function=embeddings,
        collection_name="chroma_docs",
        relevance_score_fn=lambda distance: 1 - distance
    ) # created in indexer folder
    query = "How to obtain a valid alien token to run the O2 simulation?"

    result = chroma_vectorstore.similarity_search_with_relevance_scores(query, k=3)
    print("Retrieved documents:")
    for doc in result:
        print(doc) # by default chroma stores cosine distance = 1 - cosine similarity and returns the relevance score

    # chroma_retriever = chroma_vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"k": 3, "score_threshold": 0.6})
