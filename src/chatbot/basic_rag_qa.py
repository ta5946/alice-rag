import re
import asyncio
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
import src.chatbot.simulation_chatbot_prompts as prompts
from src.chatbot.mattermost_utils import USER_PARAMS_RE, async_update_post, get_thread_tags
from src.chatbot.langchain_components import *


PROMPT_CATEGORY_MAP = {
    1: "rag_question",
    2: "script_request"
}

# response streaming helper
async def stream_response(llm, db, messages, mattermost_context, update_interval=10, links=None, status="🤖 _Generating response..._"):
    await async_update_post(mattermost_context, status)

    print("CHATBOT ANSWER:")
    assistant_text = ""
    token_count = 0
    async for event in llm.astream(messages, config={"callbacks": [TRACING_HANDLER]}):
        print(event.content, end="", flush=True)
        assistant_text += event.content
        token_count += 1
        if token_count % update_interval == 0:
            try:
                await asyncio.wait_for(async_update_post(mattermost_context, assistant_text), timeout=0.5) # avoid blocking
            except Exception as error:
                print("Skipping async_update_post():", error)
                continue

    # manual source citation
    if links:
        links = list(dict.fromkeys(links)) # deduplicate links
        sources_suffix = "\n\n**Sources:**\n"
        sources_suffix += "\n".join(f"{i + 1}. {link}" for i, link in enumerate(links))
        print(sources_suffix)
        assistant_text += sources_suffix
    else:
        print()

    await async_update_post(mattermost_context, assistant_text + prompts.user_feedback_suffix.format(llm=get_llm_name(llm), db=get_db_name(db))) # ask for feedback
    return assistant_text

# MESSAGE CLASSIFICATION
async def classify_prompt(llm, prompt, message_history, mattermost_context):
    await async_update_post(mattermost_context, "🔍 _Analyzing question..._")

    system_message = prompts.classifier_system_message
    user_text = prompts.classifier_prompt_template
    user_message = HumanMessage(content=user_text.format(conversation_history=messages_to_string(message_history), question=prompt))
    messages = [system_message, user_message]

    assistant_message = await ainvoke_deterministic_llm(llm, messages, callbacks=[TRACING_HANDLER])
    for state in PROMPT_CATEGORY_MAP.keys():
        if str(state) in assistant_message.content:
            return state
    raise ValueError("Invalid prompt classification:", assistant_message.content)

# BASIC QUESTION
async def basic_response(llm, db, prompt, message_history, mattermost_context):
    system_message = prompts.basic_response_system_message
    user_message = HumanMessage(content=prompts.basic_prompt_template.format(conversation_history=messages_to_string(message_history), question=prompt))
    messages = [system_message, user_message]

    assistant_text = await stream_response(llm, db, messages, mattermost_context)
    return assistant_text

# BUG REPORT
async def ticket_response(llm, db, prompt, message_history, mattermost_context):
    system_message = prompts.ticket_response_system_message
    user_message = HumanMessage(content=prompts.basic_prompt_template.format(conversation_history=messages_to_string(message_history), question=prompt))
    messages = [system_message, user_message]

    assistant_text = await stream_response(llm, db, messages, mattermost_context)
    return assistant_text

# RAG QUESTION
async def generate_search_query(llm, prompt, message_history, mattermost_context):
    await async_update_post(mattermost_context, "🔍 _Generating search query..._")
    system_message = prompts.querier_system_message
    user_text = prompts.querier_prompt_template
    user_message = HumanMessage(content=user_text.format(conversation_history=messages_to_string(message_history), question=prompt))
    messages = [system_message, user_message]

    assistant_message = await llm.ainvoke(messages, config={"callbacks": [TRACING_HANDLER]})
    search_query = assistant_message.content
    print("SEARCH QUERY:", search_query)
    return search_query

async def retrieve_documents(db, search_query, mattermost_context):
    await async_update_post(mattermost_context, "📄 _Searching for documents..._")
    retrieved_docs = await ainvoke_db_config(db, search_query, callbacks=[TRACING_HANDLER])
    # retrieved_docs = await db.ainvoke(search_query, config={"callbacks": [TRACING_HANDLER]})
    if isinstance(retrieved_docs, list):
        retrieved_docs = [Document(page_content=doc.page_content, metadata={"link": doc.metadata.get("link")}) for doc in retrieved_docs]
    if len(retrieved_docs) == 0:
        retrieved_docs = "No relevant documents were retrieved."
    # print("RETRIEVED DOCUMENTS:")
    # print(retrieved_docs)
    return retrieved_docs

async def rag_response(llm, db, prompt, message_history=None, mattermost_context=None, include_links=True):
    message_history = message_history or prompts.default_message_history # evaluation script workaround
    search_query = await generate_search_query(llm, prompt, message_history, mattermost_context)
    retrieved_docs = await retrieve_documents(db, search_query, mattermost_context)
    print("RETRIEVED DOCUMENTS:", len(retrieved_docs))
    if include_links and isinstance(retrieved_docs, list):
        links = [doc.metadata.get("link") for doc in retrieved_docs]
    else:
        links = None

    system_message = prompts.rag_response_system_message
    user_text = prompts.rag_prompt_template
    user_message = HumanMessage(content=user_text.format(conversation_history=messages_to_string(message_history), question=prompt, context=retrieved_docs))
    messages = [system_message, user_message]

    assistant_text = await stream_response(llm, db, messages, mattermost_context, links=links)
    return assistant_text

# SCRIPT REQUEST
async def script_confirmation_response(llm, db, prompt, message_history, mattermost_context):
    await async_update_post(mattermost_context, "🤖 _Generating response..._")

    assistant_text = prompts.script_confirmation_response
    await async_update_post(mattermost_context, assistant_text)
    return assistant_text

async def script_generation_response(llm, db, prompt, message_history, mattermost_context):
    system_message = prompts.script_response_system_message
    user_text = prompts.script_prompt_template.format(conversation_history=messages_to_string(message_history), user_message=prompt, script_template=prompts.script_template, variable_definitions=prompts.variable_definitions)
    messages = [system_message, user_text]

    assistant_text = await stream_response(llm, db, messages, mattermost_context, status="💻 _Generating script..._") # custom status
    return assistant_text

# CHATBOT CONFIGURATION
VALID_PARAMS = {
    "model": {
        "default": LLM,
        "gpt": External.GPT,
        "qwen": External.QWEN,
        "mistral": External.MISTRAL,
        "gemma": External.GEMMA,
        "deepseek": External.DEEPSEEK
    },
    "db": {
        "default": MED_DB_CONFIG,
        "low": LOW_DB_CONFIG,
        "med": MED_DB_CONFIG,
        "high": HIGH_DB_CONFIG,
        "max": MAX_DB_CONFIG
    }
}

def get_chatbot_params(user_question, mattermost_context):
    # default configuration
    chatbot_params = {
        "model": VALID_PARAMS["model"]["default"],
        "db": VALID_PARAMS["db"]["default"]
    }

    # first check thread
    tracing_tags = get_thread_tags(mattermost_context.get("thread_id")) if mattermost_context else []
    for tag in tracing_tags:
        for param in VALID_PARAMS.keys():
            if not tag.startswith(param):
                continue
            tag_key = tag.split(":", 1)[1]
            for param_key, param_value in VALID_PARAMS[param].items():
                if tag_key.lower().startswith(param_key):
                    print(f"Setting chatbot parameter {param} to {param_key} from thread tags!")
                    chatbot_params[param] = param_value

    # override with user flags
    cleaned_question = re.sub(USER_PARAMS_RE, "", user_question, flags=re.IGNORECASE).strip()
    matches = re.findall(USER_PARAMS_RE, user_question, flags=re.IGNORECASE)
    for param, param_key in matches:
        param = param.lower()
        param_key = param_key.lower()
        if param in VALID_PARAMS and param_key in VALID_PARAMS[param]:
            print(f"Setting chatbot parameter {param} to {param_key} from user params!")
            chatbot_params[param] = VALID_PARAMS[param][param_key]

    return cleaned_question, chatbot_params

def get_llm_name(llm):
    return llm.model_name

def get_db_name(db):
    return db.get("name")


RESPONSE_MAP = {
    1: rag_response,
    2: script_generation_response
}

# there is no additional latency caused by Mattermost interface!
async def qa_pipeline(question, message_history=None, feedback=True, mattermost_context=None, dev_mode=False):
    answer = ""
    if not message_history:
        message_history = prompts.default_message_history
    question, chatbot_params = get_chatbot_params(question, mattermost_context)
    llm = chatbot_params.get("model")
    db = chatbot_params.get("db")
    try:
        with TRACING_CLIENT.start_as_current_span(
                name="askALICE RAG",
                input={"question": question, "messages": message_history}
        ) as qa_trace:
            question_category = await classify_prompt(llm, question, message_history, mattermost_context)
            print("QUESTION CLASSIFICATION:", PROMPT_CATEGORY_MAP[question_category])

            # TODO add script confirmation response
            answer = await RESPONSE_MAP[question_category](llm, db, question, message_history, mattermost_context)
            tags = []
            tags.append(f"mode:{'dev' if dev_mode else 'prod'}")
            tags.append(f"model:{get_llm_name(llm)}")
            tags.append(f"db:{get_db_name(db)}")
            tags.append(f"post_id:{mattermost_context.get('post_id')}") if mattermost_context else None
            tags.append(f"thread_id:{mattermost_context.get('thread_id')}") if mattermost_context else None
            qa_trace.update_trace(output={"answer": answer}, tags=tags)

            if feedback:
                await create_feedback(qa_trace.trace_id)
            return answer

    except asyncio.CancelledError as error:
        print("qa_pipeline():", error)
        return answer

    except Exception as error:
        print("qa_pipeline():", error)
        return answer

# USER FEEDBACK
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
            print("main():", error)


if __name__ == "__main__":
    asyncio.run(main())
