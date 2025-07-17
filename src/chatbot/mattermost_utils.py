import os
import asyncio
from mattermostdriver import Driver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langfuse import get_client
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

TRACING_CLIENT = get_client()


def get_thread_messages(thread_id):
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

def update_post(mattermost_context, message):
    if mattermost_context:
        try:
            MATTERMOST_DRIVER.posts.update_post(mattermost_context.get("post_id"), {
                "id": mattermost_context.get("post_id"),
                "channel_id": mattermost_context.get("channel_id"),
                "root_id": mattermost_context.get("thread_id"),
                "message": message
            })

        except Exception as error:
            print(f"update_post(): {error}")

async def async_update_post(mattermost_context, message):
    await asyncio.to_thread(update_post, mattermost_context, message)


def score_message(post_id, score_context):
    try:
        trace_list = TRACING_CLIENT.api.trace.list(tags=[post_id])
        trace = trace_list.data[0]
        TRACING_CLIENT.create_score(
            trace_id=trace.id,
            score_id=trace.id, # to override previous score
            name=score_context.get("name"),
            value=score_context.get("value"),
            comment=score_context.get("comment")
        )

    except Exception as error:
        print(f"score_trace(): {error}")

async def delayed_score_message(post_id, score_context, delay=2):
    await asyncio.sleep(delay)
    await asyncio.to_thread(score_message, post_id, score_context)
