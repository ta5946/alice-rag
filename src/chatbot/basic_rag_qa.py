# TODO Replace prints with logging

import asyncio
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
import src.chatbot.simulation_chatbot_prompts as prompts
from src.chatbot.mattermost_utils import async_update_post
from src.chatbot.langchain_components import LLM, COMPRESSION_RETRIEVER, TRACING_CLIENT, TRACING_HANDLER, messages_to_string


PROMPT_CATEGORY_MAP = {
    1: "General question",
    2: "Requires context",
    3: "Submit ticket",
    4: "Generate script"
}

async def stream_response(messages, mattermost_context, update_interval=10, links=None):
    await async_update_post(mattermost_context, "🤖 _Generating response..._")

    print("CHATBOT ANSWER:")
    assistant_text = ""
    token_count = 0
    async for event in LLM.astream(messages, config={"callbacks": [TRACING_HANDLER]}):
        print(event.content, end="", flush=True)
        assistant_text += event.content
        token_count += 1
        if token_count % update_interval == 0:
            await async_update_post(mattermost_context, assistant_text)

    # manually cite sources
    if links:
        sources_suffix = "\n\n**Sources:**\n"
        sources_suffix += "\n".join(f"{i + 1}. {link}" for i, link in enumerate(links))
        print(sources_suffix)
        assistant_text += sources_suffix
    else:
        print()

    await async_update_post(mattermost_context, assistant_text + prompts.user_feedback_suffix) # ask for feedback
    return assistant_text

async def classify_prompt(prompt, message_history, mattermost_context):
    await async_update_post(mattermost_context, "🔍 _Analyzing question..._")

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
    for state in PROMPT_CATEGORY_MAP.keys():
        if str(state) in assistant_message.content:
            return state
    raise ValueError("Invalid prompt classification:", assistant_message.content)

async def basic_response(prompt, message_history, mattermost_context):
    system_message = prompts.basic_response_system_message
    user_message = HumanMessage(content=prompts.basic_prompt_template.format(conversation_history=messages_to_string(message_history), question=prompt))
    messages = [system_message, user_message]

    assistant_text = await stream_response(messages, mattermost_context)
    return assistant_text

async def ticket_response(prompt, message_history, mattermost_context):
    system_message = prompts.ticket_response_system_message
    user_message = HumanMessage(content=prompts.basic_prompt_template.format(conversation_history=messages_to_string(message_history), question=prompt))
    messages = [system_message, user_message]

    assistant_text = await stream_response(messages, mattermost_context)
    return assistant_text

async def rag_response(prompt, message_history=None, mattermost_context=None):
    await async_update_post(mattermost_context, "📄 _Searching for documents..._")
    message_history = message_history or prompts.default_message_history # evaluation script workaround

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

    assistant_message = await LLM.ainvoke(messages, config={"callbacks": [TRACING_HANDLER]})
    search_query = assistant_message.content
    print("SEARCH QUERY:", search_query)

    print("RETRIEVED DOCUMENTS:")
    retrieved_docs = await COMPRESSION_RETRIEVER.ainvoke(search_query, config={"callbacks": [TRACING_HANDLER]})
    links = None
    if isinstance(retrieved_docs, list):
        retrieved_docs = [Document(page_content=doc.page_content, metadata={"link": doc.metadata.get("link")}) for doc in retrieved_docs]
        links = [doc.metadata.get("link") for doc in retrieved_docs]
    if len(retrieved_docs) == 0:
        retrieved_docs = "No relevant documents were retrieved."
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
    user_message = HumanMessage(content=user_text.format(conversation_history=messages_to_string(message_history), question=prompt, context=retrieved_docs))
    messages = [system_message, user_message]

    assistant_text = await stream_response(messages, mattermost_context, links=links)
    return assistant_text


async def check_variables(prompt, message_history, mattermost_context):
    system_message = prompts.variable_checker_system_message
    user_text = prompts.variable_prompt_template.format(conversation_history=messages_to_string(message_history), user_message=prompt, variable_definitions=prompts.prototype_variable_definitions)
    messages = [system_message, user_text]

    assistant_message = await LLM.ainvoke(messages, config={"callbacks": [TRACING_HANDLER]})
    if "1" in assistant_message.content:
        return True
    else:
        return False

async def collect_variables(prompt, message_history, mattermost_context):
    system_message = prompts.variable_collector_system_message
    user_text = prompts.variable_prompt_template.format(conversation_history=messages_to_string(message_history), user_message=prompt, variable_definitions=prompts.prototype_variable_definitions)
    messages = [system_message, user_text]

    assistant_text = await stream_response(messages, mattermost_context)
    return assistant_text

async def generate_script(prompt, message_history, mattermost_context):
    await async_update_post(mattermost_context, "💻 _Generating script..._")

    system_message = prompts.script_generator_system_message
    user_text = prompts.script_prompt_template.format(conversation_history=messages_to_string(message_history), user_message=prompt, script_template=prompts.prototype_script_template)
    messages = [system_message, user_text]

    assistant_message = await LLM.ainvoke(messages, config={"callbacks": [TRACING_HANDLER]})
    assistant_text = assistant_message.content
    await async_update_post(mattermost_context, assistant_text + prompts.user_feedback_suffix)
    return assistant_text

async def script_response(prompt, message_history, mattermost_context):
    variables_provided = await check_variables(prompt, message_history, mattermost_context)
    if variables_provided:
        return await generate_script(prompt, message_history, mattermost_context)
    else:
        return await collect_variables(prompt, message_history, mattermost_context)


RESPONSE_MAP = {
    1: basic_response,
    2: rag_response,
    3: ticket_response,
    4: script_response,
}

async def qa_pipeline(question, message_history=None, feedback=True, mattermost_context=None):
    answer = ""
    if not message_history:
        message_history = prompts.default_message_history
    try:
        with TRACING_CLIENT.start_as_current_span(
                name="basic_rag_qa",
                input={"question": question, "messages": message_history}
        ) as qa_trace:
            question_category = await classify_prompt(question, message_history, mattermost_context)
            print("QUESTION CLASSIFICATION:", PROMPT_CATEGORY_MAP[question_category])

            answer = await RESPONSE_MAP[question_category](question, message_history, mattermost_context)
            tags = [mattermost_context.get("post_id")] if mattermost_context else None
            qa_trace.update_trace(
                output={"answer": answer},
                # metadata={"mattermost_context": mattermost_context},
                tags=tags
            )

            if feedback:
                await create_feedback(qa_trace.trace_id)
            return answer

    except asyncio.CancelledError as error:
        print("qa_pipeline():", error)
        return answer

    except Exception as error:
        print("qa_pipeline():", error)
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
            answer = await qa_pipeline(question, conversation_history)
            conversation_history.extend([HumanMessage(content=question), AIMessage(content=answer)])
            print()

        except Exception as error:
            print(error)


if __name__ == "__main__":
    asyncio.run(main())
