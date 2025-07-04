import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"


def test_llm():
    llm = ChatOpenAI(
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY")
    )  # v1 endpoint with no authentication for now
    prompt = "What is 9*9?"

    response = llm.invoke(prompt)
    print("Model response:")
    print(response)

    assert response is not None, "LLM response should not be None"
    assert "81" in response.content, "LLM response should contain the answer to 9*9"


if __name__ == "__main__":
    test_llm()
