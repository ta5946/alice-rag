# TODO separate components and utils

import os
from chromadb import PersistentClient
from mattermostdriver import Driver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
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
    model_kwargs={"device": "cuda"}
)

CHROMA_CLIENT = PersistentClient(path=os.getenv("CHROMA_DIR")) # can switch to chromadb.HttpClient()

VECTORSTORE = Chroma(
    collection_name=os.getenv("CHROMA_COLLECTION_NAME"),
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
    model_kwargs={"cache_folder": os.getenv("HF_CACHE_DIR"),"device": "cpu"}
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


# patch https://github.com/Vaelor/python-mattermost-driver/issues/115
import ssl

create_default_context_orig = ssl.create_default_context
def cdc(*args, **kwargs):
    kwargs["purpose"] = ssl.Purpose.SERVER_AUTH
    return create_default_context_orig(*args, **kwargs)
ssl.create_default_context = cdc

MATTERMOST_DRIVER = Driver({
    "url": os.getenv("MATTERMOST_URL"),
    "token": os.getenv("MATTERMOST_TOKEN"),
    "scheme": 'https',
    "port": int(os.getenv("MATTERMOST_PORT")),
    "verify": True,
    "websocket": True
})


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
