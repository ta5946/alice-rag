import os
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from mattermostdriver import Driver
from basic_rag_qa import qa_pipeline
from dotenv import load_dotenv

load_dotenv()


# patch https://github.com/Vaelor/python-mattermost-driver/issues/115
import ssl

create_default_context_orig = ssl.create_default_context
def cdc(*args, **kwargs):
    kwargs["purpose"] = ssl.Purpose.SERVER_AUTH
    return create_default_context_orig(*args, **kwargs)
ssl.create_default_context = cdc


driver = Driver({
    "url": os.getenv("MATTERMOST_URL"),
    "token": os.getenv("MATTERMOST_TOKEN"),
    "scheme": 'https',
    "port": int(os.getenv("MATTERMOST_PORT")),
    "verify": True,
    "websocket": True
})

driver.login()
bot_id = driver.users.get_user("me").get("id")

async def get_thread_messages(thread_id):
    try:
        posts = driver.posts.get_thread(thread_id).get("posts")
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

        thinking_post = driver.posts.create_post({
            "channel_id": channel_id,
            "message": "_🤖 Thinking..._",
            "root_id": thread_id
        })
        bot_message = qa_pipeline(post_message, thread_messages, feedback=False)

        driver.posts.update_post(thinking_post.get("id"), {
            "id": thinking_post.get("id"),
            "channel_id": channel_id,
            "message": bot_message,
            "root_id": thread_id
        })

    except Exception as error:
        print(f"event_handler(): {error}")


if __name__ == '__main__':
    driver.init_websocket(event_handler) # wait for events
