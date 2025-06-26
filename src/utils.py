import os
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()


LLM = ChatOpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY")
)

EMBEDDINGS = HuggingFaceEmbeddings(
    model_name=os.getenv("HF_EMBEDDINGS_REPO"),
    cache_folder=os.getenv("HF_CACHE_DIR"),
    model_kwargs = {"device": "cuda"}
)

VECTORSTORE = Chroma(
    persist_directory=os.getenv("CHROMA_DIR"),
    embedding_function=EMBEDDINGS,
    collection_name="chroma_docs",
    relevance_score_fn=lambda distance: 1 - distance
)

RETRIEVER = VECTORSTORE.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": int(os.getenv("CHROMA_TOP_K")), "score_threshold": float(os.getenv("CHROMA_THRESHOLD"))}
)
