from langchain_openai import ChatOpenAI


if __name__ == "__main__":
    llm = ChatOpenAI(base_url="http://localhost:8080/v1", api_key="any") # v1 endpoint with no authentication for now
    prompt = "What is 9*9?"

    response = llm.invoke(prompt)
    print("Model response:")
    print(response)
