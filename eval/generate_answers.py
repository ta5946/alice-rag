import os
import json
import time
import asyncio
from tqdm import tqdm
from functools import partial
from src.chatbot.langchain_components import LLM, GEMINI
from src.chatbot.basic_rag_qa import rag_response


async def base_llm(question):
    # await asyncio.sleep(1) # to not overload the llama.cpp server (1 second?)
    assistant_message = await LLM.ainvoke(question) # hangs at "srv log_server_r: request: GET /health 127.0.0.1 20"
    return assistant_message.content

async def base_gemini(question):
    await asyncio.sleep(3) # wait for N seconds to avoid rate limit
    assistant_message = await GEMINI.ainvoke(question) # TODO empty content fix
    return assistant_message.content


# evaluation configuration
DATASET_PATH = "eval/datasets/expert_qa_dataset_gpt.json"
ANSWER_GENERATOR = partial(rag_response, include_links=False)
ANSWER_PATH = "eval/answers/synthetic/rag_qwen_medium_questions.json"
N_ANSWERS = 5

async def generate_answers():
    # load dataset
    with open(DATASET_PATH, "r") as dataset_file:
        qa_dataset = json.load(dataset_file)

    # drop questions without answers
    qa_dataset = [item for item in qa_dataset if item["correct_answer"]]
    print(f"Loaded {len(qa_dataset)} question-answer pairs from {DATASET_PATH}")

    # generate answers
    for item in tqdm(qa_dataset, desc=f"Generating samples of {N_ANSWERS} answers", unit="question"):
        item["generated_answers"] = []
        item["times"] = []
        for i in range(N_ANSWERS):
            start = time.time()
            generated_answer = await ANSWER_GENERATOR(item["question"])
            print(generated_answer)
            item["generated_answers"].append(generated_answer)
            end = time.time()
            item["times"].append(end - start)

    # save answers
    os.makedirs(os.path.dirname(ANSWER_PATH), exist_ok=True)
    print(f"Saving generated answers to {ANSWER_PATH}")
    with open(ANSWER_PATH, "w") as answer_file:
        json.dump(qa_dataset, answer_file, indent=4)


if __name__ == "__main__":
    asyncio.run(generate_answers())
