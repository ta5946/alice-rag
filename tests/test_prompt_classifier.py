import json
import pytest
import asyncio
from src.chatbot.basic_rag_qa import PROMPT_CATEGORY_MAP, classify_prompt
from dotenv import load_dotenv

load_dotenv()

DATASET_PATH = "eval/datasets/prompt_classifications.json"


@pytest.mark.asyncio
async def test_prompt_classifier():
    with open(DATASET_PATH, "r") as file:
        dataset = json.load(file)
        for item in dataset:
            prediction = await classify_prompt(item.get("prompt"), [], None)
            assert PROMPT_CATEGORY_MAP[prediction] == item.get("label"), \
                f"Expected {item.get('label')} but got {PROMPT_CATEGORY_MAP[prediction]} for prompt: {item.get('prompt')}"


if __name__ == "__main__":
    asyncio.run(test_prompt_classifier())
