import os
from src.chatbot.langchain_components import LLM
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "false"


def test_llm():
    prompt = "What is 9*9?"

    response = LLM.invoke(prompt)
    print("Model response:")
    print(response)

    assert response is not None, "LLM response should not be None."
    assert "81" in response.content, "LLM response should contain the answer to 9*9."


if __name__ == "__main__":
    test_llm()
