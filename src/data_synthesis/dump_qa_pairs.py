import os
import json


DATASET_PATH = "./data/synthetic/document_qa_dataset.json"
DUMP_PATH = "./data/knowledge_base/synthetic/qa/"

def group_qa_pairs_by_link(qa_pairs_by_chunk, include_difficulty="Medium"):
    qa_pairs_by_link = {}
    for chunk_id, qa_pairs in qa_pairs_by_chunk.items():
        for qa_pair in qa_pairs:
            if qa_pair.get("difficulty") != include_difficulty: # only include medium difficulty questions to reduce size
                continue
            link = qa_pair.get("link")
            if link not in qa_pairs_by_link:
                qa_pairs_by_link[link] = [{
                    "start_chunk_id": chunk_id,
                    "link": link,
                }]
            qa_pairs_by_link[link].append({
                "question": qa_pair.get("question"),
                "answer": qa_pair.get("answer"),
            })
    return qa_pairs_by_link


if __name__ == "__main__":
    with open(DATASET_PATH, "r") as rf:
        qa_pairs_by_chunk = json.load(rf)
        qa_pairs_by_chunk = dict(sorted(qa_pairs_by_chunk.items())) # consistent order of chunks
        qa_pairs_by_link = group_qa_pairs_by_link(qa_pairs_by_chunk)

        # dump questions
        os.makedirs(DUMP_PATH, exist_ok=True)
        for link, qa_pairs in qa_pairs_by_link.items():
            # name files as start chunk id
            start_chunk_id = qa_pairs[0].get("start_chunk_id")
            file_path = os.path.join(DUMP_PATH, f"{start_chunk_id}.md")

            with open(file_path, "w") as wf:
                # write metadata
                wf.write("## Metadata\n\n")
                wf.write(f"**Document link:** {link}\n\n")
                wf.write(f"**Start chunk id:** {start_chunk_id}\n\n")

                # write content
                wf.write("## Content\n\n")
                content = []
                for qa_pair in qa_pairs[1:]:
                    content.append(f"**Question:** {qa_pair.get('question')}\n\n**Answer:** {qa_pair.get('answer')}")
                wf.write("\n\n---\n\n".join(content))

            print(f"Dumped {len(qa_pairs) - 1} question-answer pairs to {file_path}")
