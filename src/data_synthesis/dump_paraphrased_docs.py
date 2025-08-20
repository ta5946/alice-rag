import os
import json


DATASET_PATH = "./data/synthetic/paraphrased_doc_dataset.json"
DUMP_PATH = "./data/knowledge_base/synthetic/docs/"

def group_docs_by_link(docs_by_chunk):
    docs_by_link = {}
    for chunk_id, docs in docs_by_chunk.items():
        for doc in docs:
            link = doc.get("link")
            if link not in docs_by_link:
                docs_by_link[link] = [{
                    "start_chunk_id": chunk_id,
                    "link": link,
                }]
            docs_by_link[link].append({
                "paraphrased_text": doc.get("paraphrased_text"),
            })
    return docs_by_link


if __name__ == "__main__":
    with open(DATASET_PATH, "r") as rf:
        docs_by_chunk = json.load(rf)
        print(len(docs_by_chunk), "chunks found in the dataset.")
        docs_by_chunk = dict(sorted(docs_by_chunk.items())) # consistent order of chunks
        docs_by_link = group_docs_by_link(docs_by_chunk)

        # dump questions
        os.makedirs(DUMP_PATH, exist_ok=True)
        for link, docs in docs_by_link.items():
            # name files as start chunk id
            start_chunk_id = docs[0].get("start_chunk_id")
            file_path = os.path.join(DUMP_PATH, f"{start_chunk_id}.md")

            with open(file_path, "w") as wf:
                # write metadata
                wf.write("## Metadata\n\n")
                wf.write(f"**Document link:** {link}\n\n")
                wf.write(f"**Start chunk id:** {start_chunk_id}\n\n")

                # write content
                wf.write("## Content\n\n")
                content = []
                for doc in docs[1:]:
                    content.append(doc.get("paraphrased_text"))
                wf.write("\n\n---\n\n".join(content))

            print(f"Dumped {len(docs) - 1} paraphrased documents to {file_path}")
