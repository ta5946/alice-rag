import json
from tqdm import tqdm
from src.chatbot.langchain_components import LLM, CHROMA_COLLECTION
from src.data_synthesis.generate_qa_pairs import check_or_create_file
import src.data_synthesis.generation_prompts as prompts

DATASET_PATH = "./data/synthetic/paraphrased_doc_dataset.json"


def paraphrase_document(document):
    print("Paraphrasing document...")
    system_message = prompts.paraphraser_system_message
    user_message = prompts.paraphraser_prompt_template.format(document=document)
    messages = [system_message, user_message]

    assistant_message = LLM.invoke(messages)
    paraphrased_text = assistant_message.content.strip()
    return paraphrased_text


if __name__ == "__main__":
    with open(check_or_create_file(DATASET_PATH), "r") as rf:
        json_data = json.load(rf)

        collection = CHROMA_COLLECTION.get() # 2900 text chunks
        for identifier, metadata, document in tqdm(
                zip(collection.get("ids"), collection.get("metadatas"), collection.get("documents")),
                total=len(collection.get("ids")),
                desc="Processing documents"
        ):
            if json_data.get(identifier):
                continue

            json_data[identifier] = []
            paraphrased_text = paraphrase_document(document)
            json_data[identifier].append({
                "model": LLM.model_name,
                "paraphrased_text": paraphrased_text,
                "link": metadata.get("link")
            })

            print("Saving the paraphrased text...")
            with open(DATASET_PATH, "w") as wf:
                json.dump(json_data, wf, indent=4, ensure_ascii=False)
