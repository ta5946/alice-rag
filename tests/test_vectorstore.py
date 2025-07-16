import os
from src.chatbot.langchain_components import VECTORSTORE, VECTORSTORE_RETRIEVER, COMPRESSION_RETRIEVER
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"


def test_vectorstore():
    search_query = "How to obtain a valid alien token to run the O2 simulation?"

    # Relevance scores
    result_with_scores = VECTORSTORE.similarity_search_with_relevance_scores(
        k=int(os.getenv("CHROMA_TOP_K")),
        query=search_query,
        score_threshold=float(os.getenv("CHROMA_THRESHOLD"))
    )
    for doc, score in result_with_scores:
        print(score)

    # Basic retrieval
    basic_result = VECTORSTORE_RETRIEVER.invoke(search_query)
    print("Retrieved documents with relevance score above threshold:")
    for doc in basic_result:
        print(doc) # top k documents with a relevance score above the threshold

    # Retrieval with reranking
    reranked_result = COMPRESSION_RETRIEVER.invoke(search_query)
    print("Retrieved documents with reranking:")
    for doc in reranked_result:
        print(doc) # top n documents reranked

    assert len(result_with_scores) <= int(os.getenv("CHROMA_TOP_K")), "Number of retrieved documents should not be above top-k."
    assert all(score >= float(os.getenv("CHROMA_THRESHOLD")) for doc, score in result_with_scores), "Document cosine similarity scores should be above retrieval threshold."
    assert len(basic_result) > 0, "Basic retrieval should return at least one document."
    assert len(reranked_result) > 0, "Reranked retrieval should also return at least one document."
    assert all(doc in basic_result for doc in reranked_result), "Reranked documents should be a subset of basic retrieval results."


if __name__ == "__main__":
    test_vectorstore()
