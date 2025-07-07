import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from basic_rag_qa import qa_pipeline
import simulation_chatbot_prompts as prompts
from utils import MATTERMOST_DRIVER
from dotenv import load_dotenv

load_dotenv()


MATTERMOST_DRIVER.login()
bot_id = MATTERMOST_DRIVER.users.get_user("me").get("id")

async def get_thread_messages(thread_id):
    try:
        posts = MATTERMOST_DRIVER.posts.get_thread(thread_id).get("posts")
        sorted_posts = sorted(posts.values(), key=lambda p: p["create_at"])
        messages = []
        for post in sorted_posts:
            if post.get("user_id") == bot_id:
                messages.append(AIMessage(content=post.get("message")))
            else:
                messages.append(HumanMessage(content=post.get("message")))
        return messages
    except Exception as error:
        print(f"get_thread_messages(): {error}")
        return []

async def event_handler(event):
    try:
        event = json.loads(event)
        event_data = event.get("data")
        if not (event.get("event") == "posted" and event_data.get("channel_type") == "D"): # direct messages only
            return
        post_data = json.loads(event_data.get("post"))
        if post_data.get("user_id") == bot_id: # ignore bot messages
            return

        print("HANDLING EVENT:")
        print(event)
        channel_id = post_data.get("channel_id")
        post_id = post_data.get("id")
        post_message = post_data.get("message")
        thread_id = post_data.get("root_id") or post_id
        thread_messages = await get_thread_messages(thread_id)
        thread_messages = thread_messages[:-1] if thread_messages and thread_messages[-1].content == post_message else thread_messages # exclude last message

        thinking_post = MATTERMOST_DRIVER.posts.create_post({
            "channel_id": channel_id,
            "message": "_🤖 Thinking..._",
            "root_id": thread_id
        })

        # generate chatbot response
        if len(thread_messages) == 0:
            bot_message = await qa_pipeline(post_message, prompts.default_message_history, feedback=False)
        else:
            bot_message = await qa_pipeline(post_message, thread_messages, feedback=False)

        MATTERMOST_DRIVER.posts.update_post(thinking_post.get("id"), {
            "id": thinking_post.get("id"),
            "channel_id": channel_id,
            "message": bot_message,
            "root_id": thread_id
        })

    except Exception as error:
        print(f"event_handler(): {error}")


if __name__ == '__main__':
    MATTERMOST_DRIVER.init_websocket(event_handler) # wait for events
