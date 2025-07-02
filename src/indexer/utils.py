import os
import json
from pathlib import Path
from typing import Dict, Optional
from chromadb import PersistentClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, PythonLoader, PDFMinerLoader, UnstructuredHTMLLoader
from dotenv import load_dotenv

load_dotenv()


LOADER_MAPPING = {
    ".md": TextLoader,
    ".txt": TextLoader,
    ".py": PythonLoader,
    ".sh": TextLoader,
    ".html": UnstructuredHTMLLoader,
    ".htm": UnstructuredHTMLLoader,
    ".pdf": PDFMinerLoader,
}

chroma_client = PersistentClient(path=os.getenv("CHROMA_DIR"))
CHROMA_COLLECTION = chroma_client.get_or_create_collection(name=os.getenv("CHROMA_COLLECTION_NAME"))

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=int(os.getenv("CHROMA_CHUNK_SIZE")),
    chunk_overlap=int(os.getenv("CHROMA_CHUNK_SIZE")) // 10
) # TODO try semantic text splitter

def load_previous_hashes(path: str) -> Dict[str, str]:
    """
    Load previously saved file hashes from disk.
    Returns an empty dict if file doesn't exist.
    """
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_hashes(path: str, hashes: Dict[str, str]) -> None:
    """
    Save file hashes to disk for future comparison.
    """
    print ("Hashes ", path)
    print ("hashes ", hashes)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(hashes, f, indent=2)

def extract_text_from_file(file_path: Path) -> Optional[str]:
    """
    Simple fallback loader for .txt, .md, .py, .sh files.
    Used only if not using LangChain for some reason.
    """
    try:
        if file_path.suffix.lower() in {".md", ".txt", ".py", ".sh"}:
            return file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[utils] Failed to read {file_path}: {e}")
    return None
