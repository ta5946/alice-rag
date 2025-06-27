import os
import chromadb
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()


LLM = ChatOpenAI(
    model=os.getenv("HF_LLM_REPO").split("/")[1].split("-GGUF")[0],
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY")
)

EMBEDDINGS = HuggingFaceEmbeddings(
    model_name=os.getenv("HF_EMBEDDINGS_REPO"),
    cache_folder=os.getenv("HF_CACHE_DIR"),
    model_kwargs = {"device": "cuda"}
)

CHROMA_CLIENT = chromadb.PersistentClient(path=os.getenv("CHROMA_DIR")) # can switch to chromadb.HttpClient()

VECTORSTORE = Chroma(
    collection_name="chroma_docs",
    embedding_function=EMBEDDINGS,
    client=CHROMA_CLIENT,
    relevance_score_fn=lambda distance: 1 - distance
)

VECTORSTORE_RETRIEVER = VECTORSTORE.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": int(os.getenv("CHROMA_TOP_K")), "score_threshold": float(os.getenv("CHROMA_THRESHOLD"))}
)

RERANKER = HuggingFaceCrossEncoder(
    model_name=os.getenv("HF_RERANKER_REPO"),
    model_kwargs = {"cache_folder": os.getenv("HF_CACHE_DIR"),"device": "cpu"}
)

COMPRESSOR = CrossEncoderReranker(
    model=RERANKER,
    top_n=int(os.getenv("CHROMA_TOP_N"))
)

COMPRESSION_RETRIEVER = ContextualCompressionRetriever(
    base_compressor=COMPRESSOR,
    base_retriever=VECTORSTORE_RETRIEVER
)

TRACING_CLIENT = Client()
