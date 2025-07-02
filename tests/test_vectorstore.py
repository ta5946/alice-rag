import os
from chromadb import PersistentClient
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever
from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(
        model_name=os.getenv("HF_EMBEDDINGS_REPO"),
        cache_folder=os.getenv("HF_CACHE_DIR"),
        model_kwargs={"device": "cuda"}
    )
    chroma_client = PersistentClient(path=os.getenv("CHROMA_DIR"))
    chroma_vectorstore = Chroma(
        collection_name=os.getenv("CHROMA_COLLECTION_NAME"),
        embedding_function=embeddings,
        client=chroma_client,
        relevance_score_fn=lambda distance: 1 - distance
    ) # created in indexer folder
    query = "How to obtain a valid alien token to run the O2 simulation?"

    """
    result = chroma_vectorstore.similarity_search_with_relevance_scores(query, k=int(os.getenv("CHROMA_TOP_K")))
    print("Retrieved documents and relevance scores:")
    for doc in result:
        print(doc) # by default chroma stores cosine distance = 1 - cosine similarity and returns the relevance score

    """

    # Basic retrieval
    chroma_retriever = chroma_vectorstore.as_retriever(
        search_type="similarity_score_threshold", 
        search_kwargs={"k": int(os.getenv("CHROMA_TOP_K")), "score_threshold": float(os.getenv("CHROMA_THRESHOLD"))}
    ) # generalized retriever class
    result = chroma_retriever.invoke(query)
    print("Retrieved documents with relevance score above threshold:")
    for doc in result:
        print(doc) # top k documents with a relevance score above the threshold

    reranker = HuggingFaceCrossEncoder(
        model_name=os.getenv("HF_RERANKER_REPO"),
        model_kwargs={"cache_folder": os.getenv("HF_CACHE_DIR"),"device": "cpu"}
    )
    compressor = CrossEncoderReranker(
        model=reranker,
        top_n=int(os.getenv("CHROMA_TOP_N"))
    ) # compresses the context to only top n documents
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=chroma_retriever
    )

    # Retrieval with reranking
    result = compression_retriever.invoke(query)
    print("Retrieved documents with reranking:")
    for doc in result:
        print(doc) # top k documents reranked
