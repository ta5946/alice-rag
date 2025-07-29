import os
from chromadb import PersistentClient
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from dotenv import load_dotenv

load_dotenv()


LLM = ChatOpenAI(
    model=os.getenv("HF_LLM_REPO").split("/")[1].split("-GGUF")[0],
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    max_tokens=int(os.getenv("LLM_MAX_TOKENS"))
) # v1 endpoint with no authentication for now

GEMINI = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL"),
    api_key=os.getenv("GEMINI_API_KEY"),
    max_tokens=int(os.getenv("LLM_MAX_TOKENS"))
) # free api key with a rate limit

EMBEDDINGS = HuggingFaceEmbeddings(
    model_name=os.getenv("HF_EMBEDDINGS_REPO"),
    cache_folder=os.getenv("HF_CACHE_DIR"),
    model_kwargs={"device": "cuda"}, # cpu or cuda
    encode_kwargs={"batch_size": 10}  # normalize_embeddings=False by default
) # normalization not needed if we use cosine similarity

CHROMA_CLIENT = PersistentClient(path=os.getenv("CHROMA_DIR")) # can switch to chromadb.HttpClient()

VECTORSTORE = Chroma(
    collection_name=os.getenv("CHROMA_COLLECTION_NAME"),
    embedding_function=EMBEDDINGS,
    client=CHROMA_CLIENT,
    relevance_score_fn=lambda distance: 1 - distance
) # created in indexer folder

VECTORSTORE_RETRIEVER = VECTORSTORE.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": int(os.getenv("CHROMA_TOP_K")), "score_threshold": float(os.getenv("CHROMA_THRESHOLD"))}
) # generalized retriever class

RERANKER = HuggingFaceCrossEncoder(
    model_name=os.getenv("HF_RERANKER_REPO"),
    model_kwargs={"cache_folder": os.getenv("HF_CACHE_DIR"),"device": "cpu"} # cuda out of memory
)

COMPRESSOR = CrossEncoderReranker(
    model=RERANKER,
    top_n=int(os.getenv("CHROMA_TOP_N"))
) # compresses the context to only top n documents

COMPRESSION_RETRIEVER = ContextualCompressionRetriever(
    base_compressor=COMPRESSOR,
    base_retriever=VECTORSTORE_RETRIEVER
)

TRACING_CLIENT = get_client()

TRACING_HANDLER = CallbackHandler()


def messages_to_string(messages):
    str = "[\n"
    for msg in messages:
        if isinstance(msg, SystemMessage):
            str += f"System: {msg.content}\n"
        elif isinstance(msg, HumanMessage):
            str += f"User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            str += f"Assistant: {msg.content}\n"
        else:
            raise ValueError(f"Invalid message type: {msg.type}")
    str += "]"
    return str
