import os
import json
import time
import asyncio
from tqdm import tqdm
from src.chatbot.langchain_components import LLM, GEMINI
from src.chatbot.basic_rag_qa import rag_response


async def base_llm(question):
    assistant_message = await LLM.ainvoke(question)
    return assistant_message.content

async def base_gemini(question):
    await asyncio.sleep(3) # wait for N seconds to avoid rate limit
    assistant_message = await GEMINI.ainvoke(question)
    return assistant_message.content


# evaluation configuration
DATASET_PATH = "eval/datasets/qa_dataset_gpt.json"
ANSWER_GENERATOR = rag_response
ANSWER_PATH = "eval/answers/extended_rag_qwen_answers.json"

async def generate_answers():
    # load dataset
    with open(DATASET_PATH, "r") as dataset_file:
        qa_dataset = json.load(dataset_file)

    # drop questions without answers
    qa_dataset = [item for item in qa_dataset if item["correct_answer"]]
    print(f"Loaded {len(qa_dataset)} question-answer pairs from {DATASET_PATH}")

    # generate answers
    for item in tqdm(qa_dataset, desc="Generating answers", unit="question"):
        start = time.time()
        item["generated_answer"] = await ANSWER_GENERATOR(item["question"])
        end = time.time()
        item["time"] = end - start

    # save answers
    os.makedirs(os.path.dirname(ANSWER_PATH), exist_ok=True)
    print(f"Saving generated answers to {ANSWER_PATH}")
    with open(ANSWER_PATH, "w") as answer_file:
        json.dump(qa_dataset, answer_file, indent=4)


if __name__ == "__main__":
    asyncio.run(generate_answers())
