from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langsmith import trace
import simulation_chatbot_prompts as prompts
from utils import LLM, COMPRESSION_RETRIEVER, TRACING_CLIENT, messages_to_string


PROMPT_CATEGORY_MAP = {
    1: "General question",
    2: "Requires context"
    # TODO add more categories as chatbot states
}

def classify_prompt(prompt, message_history):
    system_message = prompts.classifier_system_message
    user_text = PromptTemplate.from_template("""(
    CONVERSATION HISTORY:
    {conversation_history}
    )
    
    QUESTION:
    {question}
    
    CATEGORY:""") # TODO maybe summarize the conversation history to make it shorter
    user_message = HumanMessage(content=user_text.format(conversation_history=messages_to_string(message_history), question=prompt))
    messages = [system_message, user_message]

    assistant_message = LLM.invoke(messages)
    if "1" in assistant_message.content:
        return 1
    elif "2" in assistant_message.content:
        return 2
    else:
        raise ValueError("Invalid prompt classification:", assistant_message.content)

def basic_response(prompt, message_history):
    system_message = prompts.basic_response_system_message
    user_text = PromptTemplate.from_template("""(
    CONVERSATION HISTORY:
    {conversation_history}
    )
    
    QUESTION:
    {question}
    
    ANSWER:""")
    user_message = HumanMessage(content=user_text.format(conversation_history=messages_to_string(message_history), question=prompt))
    messages = [system_message, user_message]

    print("CHATBOT ANSWER:")
    assistant_text = ""
    for event in LLM.stream(messages):
        print(event.content, end="", flush=True)
        assistant_text += event.content
    print()
    return assistant_text

def rag_response(prompt, message_history):
    system_message = prompts.querier_system_message
    user_text = PromptTemplate.from_template("""(
    CONVERSATION HISTORY:
    {conversation_history}
    )
    
    QUESTION:
    {question}
    
    SEARCH QUERY:""")
    user_message = HumanMessage(content=user_text.format(conversation_history=messages_to_string(message_history), question=prompt))
    messages = [system_message, user_message]

    print("SEARCH QUERY:")
    assistant_message = LLM.invoke(messages)
    search_query = assistant_message.content
    print(search_query)

    retrieved_docs = COMPRESSION_RETRIEVER.invoke(search_query)
    if isinstance(retrieved_docs, list):
        retrieved_docs = [Document(page_content=doc.page_content, metadata=doc.metadata) for doc in retrieved_docs]
    if len(retrieved_docs) == 0:
        retrieved_docs = "No relevant documents were retrieved."
    print("RETRIEVED DOCUMENTS:")
    print(retrieved_docs)

    system_message = prompts.rag_response_system_message
    user_text = PromptTemplate.from_template("""(
    CONVERSATION HISTORY:
    {conversation_history}
    )
    
    QUESTION:
    {question}
    
    CONTEXT:
    {context}
    
    ANSWER:""")
    user_message = HumanMessage(
        content=user_text.format(conversation_history=messages_to_string(message_history), question=prompt, context=retrieved_docs)
    )
    messages = [system_message, user_message]

    print("CHATBOT ANSWER:")
    assistant_text = ""
    for event in LLM.stream(messages):
        print(event.content, end="", flush=True)
        assistant_text += event.content
    print()
    return assistant_text

def qa_pipeline(question, message_history, feedback=True):
    with trace(name="basic_rag_qa", inputs={"question": question, "messages": message_history}) as qa_trace:
        question_category = classify_prompt(question, message_history)
        print("QUESTION CLASSIFICATION:", PROMPT_CATEGORY_MAP[question_category])
        answer = ""
        if question_category == 1:
            answer = basic_response(question, message_history)
        elif question_category == 2:
            answer = rag_response(question, message_history)
        qa_trace.add_outputs({"answer": answer})
        if feedback:
            create_feedback(qa_trace)
        return answer

def create_feedback(qa_trace):
    user_feedback = input("WAS THE ANSWER HELPFUL? (Y/N): ").lower()
    score = None
    if user_feedback == "y" or user_feedback == "yes":
        score = 1
        print(":)")
    elif user_feedback == "n" or user_feedback == "no":
        score = 0
        print(":(")

    TRACING_CLIENT.create_feedback(
        key="helpful",
        score=score,
        trace_id=qa_trace.id,
    ) # to create a database of correct answers
    return score


if __name__ == "__main__":
    conversation_history = []
    while True:
        try:
            question = input("YOUR QUESTION: ")
            if question.lower() in ["q", "quit"]:
                print("Bye!")
                break
            if len(conversation_history) == 0:
                answer = qa_pipeline(question, prompts.default_message_history)
            else:
                answer = qa_pipeline(question, conversation_history)
            conversation_history.extend([HumanMessage(content=question), AIMessage(content=answer)])
        except Exception as error:
            print(error)
        print()
