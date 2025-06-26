from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from utils import LLM, RETRIEVER


PROMPT_CATEGORIES = {
    1: "General question",
    2: "Requires context"
    # TODO add more categories
}

def classify_prompt(prompt):
    system_message = SystemMessage(
        content="""You are a prompt classifier.
        Your task is to classify the following prompt into one of the categories:
        1. General question, that can be answered without any additional information,
        2. Question that requires context from the O2 simulation documentation.
        
        Respond only with the category number (1 or 2) and nothing else."""
    )
    user_text = PromptTemplate.from_template("""Question:
    {question}
    
    Category:""")
    user_message = HumanMessage(content=user_text.format(question=prompt))
    messages = [system_message, user_message]

    assistant_message = LLM.invoke(messages)
    if "1" in assistant_message.content:
        return 1
    elif "2" in assistant_message.content:
        return 2
    else:
        raise ValueError("Invalid prompt classification:", assistant_message.content)

def basic_response(prompt):
    system_message = SystemMessage(
        content="""You are a helpful assistant."""
    )
    user_message = HumanMessage(content=prompt)
    messages = [system_message, user_message]

    print("CHATBOT ANSWER:")
    assistant_text = ""
    for event in LLM.stream(messages):
        print(event.content, end="", flush=True)
        assistant_text += event.content
    print()
    return assistant_text

def rag_response(prompt):
    system_message = SystemMessage(
        content="""You are a chatbot designed to help with the 02 simulation documentation.
        Use the provided context to answer the following question.
        If the context does not contain enough (or any) relevant information just say so.
        Also cite your sources like [n] and do not make up new information."""
    ) # TODO add links to document metadata

    retrieved_docs = RETRIEVER.invoke(prompt)
    print("RETRIEVED DOCUMENTS:")
    print(retrieved_docs)
    user_text = PromptTemplate.from_template("""Question:
    {question}
    
    Context:
    {context}
    
    Answer:""")
    user_message = HumanMessage(
        content=user_text.format(question=prompt, context=retrieved_docs)
    )
    messages = [system_message, user_message]

    print("CHATBOT ANSWER:")
    assistant_text = ""
    for event in LLM.stream(messages):
        print(event.content, end="", flush=True)
        assistant_text += event.content
        print(event)
    print()
    return assistant_text


if __name__ == "__main__":
    while True:
        question = input("YOUR QUESTION: ")
        question_category = classify_prompt(question)
        print("QUESTION CLASSIFICATION:", PROMPT_CATEGORIES[question_category])
        if question_category == 1:
            answer = basic_response(question)
        elif question_category == 2:
            answer = rag_response(question)
