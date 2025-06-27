from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langsmith import trace
from utils import LLM, COMPRESSION_RETRIEVER, TRACING_CLIENT


PROMPT_CATEGORIES = {
    1: "General question",
    2: "Requires context"
    # TODO add more categories
}

# TODO system prompts as configurable parameters
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
        print(event.content, end="", flush=True) # replace with render in mattermost
        assistant_text += event.content
    print()
    return assistant_text

def rag_response(prompt):
    system_message = SystemMessage(
        content="""You are a chatbot designed to help with the 02 simulation documentation.
        Use the provided context to answer the following question.
        If the context does not contain enough (or any) relevant information say that you do not know the answer.
        Also cite your sources like [n] and do not make up new information."""
    ) # TODO add links to document metadata

    retrieved_docs = COMPRESSION_RETRIEVER.invoke(prompt)
    if len(retrieved_docs) == 0:
        retrieved_docs = "No relevant documents were retrieved."
    print("RETRIEVED DOCUMENTS:")
    print(retrieved_docs)

    # TODO replace question with conversation history
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
    print()
    return assistant_text

def qa_pipeline(question):
    with trace(name="basic_qa_rag", inputs={"question": question}) as qa_trace:
        question_category = classify_prompt(question)
        print("QUESTION CLASSIFICATION:", PROMPT_CATEGORIES[question_category])
        answer = ""
        if question_category == 1:
            answer = basic_response(question)
        elif question_category == 2:
            answer = rag_response(question)
        qa_trace.add_outputs({"answer": answer})
        create_feedback(qa_trace)
        return answer

def create_feedback(qa_trace):
    feedback = input("WAS THE ANSWER HELPFUL? (Y/N): ").lower()
    score = None
    if feedback == "y" or feedback == "yes":
        score = 1
    elif feedback == "n" or feedback == "no":
        score = 0

    TRACING_CLIENT.create_feedback(
        key="helpful",
        score=score,
        trace_id=qa_trace.id,
    ) # to create a database of correct answers
    return score


if __name__ == "__main__":
    while True:
        try:
            question = input("YOUR QUESTION: ")
            answer = qa_pipeline(question)
        except Exception as error:
            print(error)
        print()
