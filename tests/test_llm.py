from langchain_openai import ChatOpenAI


llm = ChatOpenAI(base_url="http://localhost:8080/v1", api_key="any") # no authentication for now
response = llm.invoke("What is 9*9?")
print(response)
