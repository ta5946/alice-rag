from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from src.chatbot.langchain_components import LLM
import src.scraper.mattermost_scraper_prompts as prompts


def classify_post(post):
    system_message = prompts.classifier_system_message
    user_text = PromptTemplate.from_template("""POST:
    {post}
    
    CATEGORY:""")
    user_message = HumanMessage(content=user_text.format(post=post))
    messages = [system_message, user_message]

    assistant_message = LLM.invoke(messages)
    if "1" in assistant_message.content:
        return 1
    elif "2" in assistant_message.content:
        return 2
    elif "3" in assistant_message.content:
        return 3
    else:
        raise ValueError("Invalid message classification:", assistant_message.content)

def extract_question(post):
    system_message = prompts.extractor_system_message
    user_text = PromptTemplate.from_template("""POST:
    {post}
    
    QUESTION:""")
    user_message = HumanMessage(content=user_text.format(post=post))
    messages = [system_message, user_message]

    assistant_message = LLM.invoke(messages)
    return assistant_message.content.strip()


def qe_pipeline(post):
    print("POST:", post)
    post_category = classify_post(post)

    if post_category == 1: # contains a question
        post_question = extract_question(post)
        print("QUESTION:", post_question)
        return post_question
    else:
        return None
