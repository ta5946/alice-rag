import asyncio
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
import simulation_chatbot_prompts as prompts
from mattermost_utils import update_post
from langchain_components import LLM, COMPRESSION_RETRIEVER, TRACING_CLIENT, TRACING_HANDLER, messages_to_string


PROMPT_CATEGORY_MAP = {
    1: "General question",
    2: "Requires context"
    # TODO add more categories as chatbot states
}


async def classify_prompt(prompt, message_history, mattermost_context):
    if mattermost_context:
        await update_post(mattermost_context, "🔍 _Analyzing question..._")

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

    assistant_message = await LLM.ainvoke(messages, config={"callbacks": [TRACING_HANDLER]})
    if "1" in assistant_message.content:
        return 1
    elif "2" in assistant_message.content:
        return 2
    else:
        raise ValueError("Invalid prompt classification:", assistant_message.content)

async def basic_response(prompt, message_history, mattermost_context):
    if mattermost_context:
        await update_post(mattermost_context, "🤖 _Generating response..._")

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
    async for event in LLM.astream(messages, config={"callbacks": [TRACING_HANDLER]}):
        print(event.content, end="", flush=True)
        assistant_text += event.content
        # TODO increase API rate limit
        # TODO freeze fix
        await update_post(mattermost_context, assistant_text) if mattermost_context else None
    print()
    return assistant_text

async def rag_response(prompt, message_history, mattermost_context):
    if mattermost_context:
        await update_post(mattermost_context, "📄 _Searching for documents..._")

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
    assistant_message = await LLM.ainvoke(messages, config={"callbacks": [TRACING_HANDLER]})
    search_query = assistant_message.content
    print(search_query)

    retrieved_docs = await COMPRESSION_RETRIEVER.ainvoke(search_query, config={"callbacks": [TRACING_HANDLER]})
    if isinstance(retrieved_docs, list):
        retrieved_docs = [Document(page_content=doc.page_content, metadata=doc.metadata) for doc in retrieved_docs]
    if len(retrieved_docs) == 0:
        retrieved_docs = "No relevant documents were retrieved."
    print("RETRIEVED DOCUMENTS:")
    print(retrieved_docs)

    if mattermost_context:
        await update_post(mattermost_context, "🤖 _Generating response..._")

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
    async for event in LLM.astream(messages, config={"callbacks": [TRACING_HANDLER]}):
        print(event.content, end="", flush=True)
        assistant_text += event.content
        await update_post(mattermost_context, assistant_text) if mattermost_context else None
    print()
    return assistant_text

async def qa_pipeline(question, message_history, feedback=True, mattermost_context=None):
    with TRACING_CLIENT.start_as_current_span(name="basic_rag_qa", input={"question": question, "messages": message_history}) as qa_trace:
        question_category = await classify_prompt(question, message_history, mattermost_context)
        print("QUESTION CLASSIFICATION:", PROMPT_CATEGORY_MAP[question_category])
        answer = ""
        if question_category == 1:
            answer = await basic_response(question, message_history, mattermost_context)
        elif question_category == 2:
            answer = await rag_response(question, message_history, mattermost_context)
        qa_trace.update_trace(output={"answer": answer})
        if feedback:
            await create_feedback(qa_trace.trace_id)
        return answer

async def create_feedback(trace_id):
    user_feedback = input("WAS THE ANSWER HELPFUL? (Y/N): ").lower()
    score = 0 # neutral feedback
    if user_feedback == "y" or user_feedback == "yes":
        score = 1
        print(":)")
    elif user_feedback == "n" or user_feedback == "no":
        score = -1
        print(":(")

    TRACING_CLIENT.create_score(trace_id=trace_id, name="helpfulness", value=score)
    return score

async def main():
    conversation_history = []
    while True:
        try:
            question = input("YOUR QUESTION: ")
            if question.lower() in ["q", "quit"]:
                print("Bye!")
                break
            if len(conversation_history) == 0:
                answer = await qa_pipeline(question, prompts.default_message_history)
            else:
                answer = await qa_pipeline(question, conversation_history)
            conversation_history.extend([HumanMessage(content=question), AIMessage(content=answer)])
        except Exception as error:
            print(error)
        print()


if __name__ == "__main__":
    asyncio.run(main())
