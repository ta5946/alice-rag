# A script to index documents/resources (mentioned in knowledge_base.yml)
# into a vector database (Chroma) using an embedding model.
# Remembers previous work through hashing.
# Started May 2025, sandro.wenzel@cern.ch
# Updated July 2025

import os
import subprocess
import yaml
import hashlib
from pathlib import Path
from src.chatbot.langchain_components import EMBEDDINGS
from src.data_indexer.utils import LOADER_MAPPING, CHROMA_COLLECTION, CHARACTER_SPLITTER, SEMANTIC_SPLITTER, load_previous_hashes, save_hashes
from dotenv import load_dotenv

load_dotenv()


RESOURCE_FILE = os.getenv("INDEXER_RESOURCE_FILE")
HASHES_FILE = os.getenv("INDEXER_HASHES_FILE")
DATA_PATH = Path(os.getenv("INDEXER_DATA_DIR"))
BATCH_SIZE = int(os.getenv("INDEXER_BATCH_SIZE"))
TEXT_SPLITTER = CHARACTER_SPLITTER

def compute_hash(text: str, source: str = "", chunk_index: int = 0, embedder_name: str = "") -> str:
    combined = f"{source}|{chunk_index}|{embedder_name}|{text}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

def index_resource(resource):
    repo_name = resource["url"].split("/")[-1].replace(".git", "")
    repo_path = DATA_PATH / repo_name

    if not repo_path.exists():
        subprocess.run(["git", "clone", "--depth", "1", "-b", resource["branch"], resource["url"], str(repo_path)])
    else:
        subprocess.run(["git", "-C", str(repo_path), "pull"])

    matched_files = []
    for pattern in resource["include"]:
        matched_files.extend(repo_path.rglob(pattern))
    
    for pattern in resource.get("exclude", []):
        excluded = set(repo_path.rglob(pattern))
        matched_files = [f for f in matched_files if f not in excluded]

    return matched_files

def load_file_content(file_path):
    ext = file_path.suffix.lower()
    loader_cls = LOADER_MAPPING.get(ext)
    if not loader_cls:
        return None

    try:
        loader = loader_cls(str(file_path))
        docs = loader.load()
        return docs
    except Exception as e:
        print(f"Failed to load {file_path}: {e}")
        return None

def batched(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]

def main():
    with open(RESOURCE_FILE) as f:
        config = yaml.safe_load(f)

    old_hashes = load_previous_hashes(HASHES_FILE)
    new_hashes = {}

    for resource in config["resources"]:
        files = index_resource(resource)
        base_url = resource["url"]
        branch = resource["branch"]
        repo_name = base_url.rstrip('/').split('/')[-1]
        repo_path = DATA_PATH / repo_name

        for path in files:
            rel_path = path.relative_to(repo_path).as_posix()
            link = f"{base_url}/blob/{branch}/{rel_path}"
            print(f"Treating {path} from {link}")
            docs = load_file_content(path)
            if not docs:
                continue

            all_text = "\n".join(doc.page_content for doc in docs)
            doc_hash = compute_hash(all_text, path, 0, embedder_name=EMBEDDINGS.model_name)
            new_hashes[str(path)] = doc_hash

            if old_hashes.get(str(path)) == doc_hash:
                print(f"Skipping {path} ... already treated")
                continue # Skip unchanged

            split_docs = TEXT_SPLITTER.split_documents(docs)
            texts = [doc.page_content for doc in split_docs]
            metadatas = [{"source": str(path), "link": link} for t in texts]
            embeddings = EMBEDDINGS.embed_documents(texts)
            ids = [compute_hash(t, path, i, "local") for i, t in enumerate(texts)]

            # We add in smaller batches because the add function has a mem limitation or size-limitation per call
            for doc_batch, id_batch, meta_batch, embedd_batch in zip(
                    batched(texts, BATCH_SIZE),
                    batched(ids, BATCH_SIZE),
                    batched(metadatas, BATCH_SIZE),
                    batched(embeddings, BATCH_SIZE)
            ):
                CHROMA_COLLECTION.add(
                    documents=doc_batch,
                    embeddings=embedd_batch,
                    metadatas=meta_batch,
                    ids=id_batch
                )

    save_hashes(HASHES_FILE, new_hashes)

if __name__ == "__main__":
    main()
