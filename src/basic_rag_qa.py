from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langsmith import trace
import simulation_chatbot_prompts as prompts
from utils import LLM, COMPRESSION_RETRIEVER, TRACING_CLIENT, messages_to_string


PROMPT_CATEGORIES = {
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
        print(event.content, end="", flush=True) # TODO replace with render in mattermost
        assistant_text += event.content
    print()
    return assistant_text

def rag_response(prompt, message_history):
    system_message = prompts.rag_response_system_message # TODO add links to document metadata

    retrieved_docs = COMPRESSION_RETRIEVER.invoke(prompt) # TODO generate a rich search query
    if len(retrieved_docs) == 0:
        retrieved_docs = "No relevant documents were retrieved."
    print("RETRIEVED DOCUMENTS:")
    print(retrieved_docs)

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

def qa_pipeline(question, message_history):
    with trace(name="basic_rag_qa", inputs={"question": question, "messages": message_history}) as qa_trace:
        question_category = classify_prompt(question, message_history)
        print("QUESTION CLASSIFICATION:", PROMPT_CATEGORIES[question_category])
        answer = ""
        if question_category == 1:
            answer = basic_response(question, message_history)
        elif question_category == 2:
            answer = rag_response(question, message_history)
        qa_trace.add_outputs({"answer": answer})
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
            if len(conversation_history) == 0:
                answer = qa_pipeline(question, prompts.default_message_history)
            else:
                answer = qa_pipeline(question, conversation_history)
            conversation_history.extend([HumanMessage(content=question), AIMessage(content=answer)])
        except Exception as error:
            print(error)
        print()
