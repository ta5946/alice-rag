import os
import json
from tqdm import tqdm
from src.chatbot.langchain_components import LLM, CHROMA_COLLECTION
import src.data_synthesis.generation_prompts as prompts


DATASET_PATH = "./data/synthetic/document_qa_dataset.json"
# takes 10 hours for 3000 text chunks in the vector database

def generate_question(document, difficulty="Medium"):
    print("Generating question...")
    system_message = prompts.question_generator_system_message
    user_message = prompts.question_generator_prompt_template.format(document=document, difficulty=difficulty)
    messages = [system_message, user_message]

    assistant_message = LLM.invoke(messages)
    question = assistant_message.content.strip()
    return question

def generate_answer(document, question):
    print("Generating answer...")
    system_message = prompts.answer_generator_system_message
    user_message = prompts.answer_generator_prompt_template.format(document=document, question=question)
    messages = [system_message, user_message]

    assistant_message = LLM.invoke(messages)
    answer = assistant_message.content.strip()
    return answer

def check_or_create_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as wf:
            json.dump({}, wf, indent=4, ensure_ascii=False)
    return path


if __name__ == "__main__":
    with open(check_or_create_file(DATASET_PATH), "r") as rf:
        json_data = json.load(rf)

        collection = CHROMA_COLLECTION.get() # 2900 text chunks
        for identifier, metadata, document in tqdm(
                zip(collection.get("ids"), collection.get("metadatas"), collection.get("documents")),
                total=len(collection.get("ids")),
                desc="Processing documents"
        ): # could improve with a sliding window
            if json_data.get(identifier):
                continue

            json_data[identifier] = []
            for difficulty in ["Easy", "Medium", "Hard"]:
                question = generate_question(document, difficulty=difficulty)
                answer = generate_answer(document, question)
                json_data[identifier].append({
                    "model": LLM.model_name,
                    "difficulty": difficulty,
                    "question": question,
                    "answer": answer,
                    "link": metadata.get("link")
                })

            print("Saving the generated question-answer pair...")
            with open(DATASET_PATH, "w") as wf:
                json.dump(json_data, wf, indent=4, ensure_ascii=False)
