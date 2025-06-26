import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
    llm = ChatOpenAI(
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY")
    ) # v1 endpoint with no authentication for now
    prompt = "What is 9*9?"

    response = llm.invoke(prompt)
    print("Model response:")
    print(response)
