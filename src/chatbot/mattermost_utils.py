import os
from mattermostdriver import Driver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()


# patch https://github.com/Vaelor/python-mattermost-driver/issues/115
import ssl

create_default_context_orig = ssl.create_default_context
def cdc(*args, **kwargs):
    kwargs["purpose"] = ssl.Purpose.SERVER_AUTH
    return create_default_context_orig(*args, **kwargs)
ssl.create_default_context = cdc

MATTERMOST_DRIVER = Driver({
    "url": os.getenv("MATTERMOST_URL"),
    "token": os.getenv("MATTERMOST_TOKEN"),
    "scheme": 'https',
    "port": int(os.getenv("MATTERMOST_PORT")),
    "verify": True,
    "websocket": True
})

MATTERMOST_DRIVER.login()
BOT_ID = MATTERMOST_DRIVER.users.get_user("me").get("id")


async def get_thread_messages(thread_id):
    try:
        posts = MATTERMOST_DRIVER.posts.get_thread(thread_id).get("posts")
        sorted_posts = sorted(posts.values(), key=lambda p: p["create_at"])
        messages = []
        for post in sorted_posts:
            if post.get("user_id") == BOT_ID:
                messages.append(AIMessage(content=post.get("message")))
            else:
                messages.append(HumanMessage(content=post.get("message")))
        return messages
    except Exception as error:
        print(f"get_thread_messages(): {error}")
        return []

async def update_post(mattermost_context, message):
    try:
        MATTERMOST_DRIVER.posts.update_post(mattermost_context.get("post_id"), {
            "id": mattermost_context.get("post_id"),
            "channel_id": mattermost_context.get("channel_id"),
            "root_id": mattermost_context.get("thread_id"),
            "message": message
        })
    except Exception as error:
        print(f"update_post(): {error}")
