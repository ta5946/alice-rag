import os
import json
import asyncio
from basic_rag_qa import qa_pipeline
from src.chatbot.mattermost_utils import MATTERMOST_DRIVER, BOT_ID, get_thread_messages, delayed_score_message
from dotenv import load_dotenv

load_dotenv()


async def handle_post(event_data):
    try:
        print("HANDLING POST")
        print(event_data)
        post_data = json.loads(event_data.get("post"))
        if post_data.get("user_id") == BOT_ID:  # ignore bot messages
            return

        channel_id = post_data.get("channel_id")
        post_id = post_data.get("id")
        post_message = post_data.get("message")
        thread_id = post_data.get("root_id") or post_id
        thread_messages = get_thread_messages(thread_id)
        thread_messages = thread_messages[:-1] if thread_messages and thread_messages[-1].content == post_message else thread_messages  # exclude last message

        bot_post = MATTERMOST_DRIVER.posts.create_post({
            "channel_id": channel_id,
            "root_id": thread_id
        })
        mattermost_context = {
            "channel_id": channel_id,
            "thread_id": thread_id,
            "post_id": bot_post.get("id"),
            "user_id": post_data.get("user_id"),
        }
        dev_mode = mattermost_context.get("user_id") == os.getenv("MATTERMOST_DEV_USER_ID")

        # generate chatbot response
        asyncio.create_task(
            qa_pipeline(post_message, thread_messages, feedback=False, mattermost_context=mattermost_context, dev_mode=dev_mode)
        )

    except Exception as error:
        print(f"handle_post(): {error}")

async def handle_reaction(event_data):
    try:
        print("HANDLING REACTION")
        print(event_data)
        reaction_data = json.loads(event_data.get("reaction"))
        post_id = reaction_data.get("post_id")
        emoji_name = reaction_data.get("emoji_name")

        score_context = {
            "name": "helpfulness",
            "value": 0,
            "comment": "User feedback on whether the chatbot answer was helpful (+1) or not (-1)."
        }

        # log the user feedback
        if emoji_name == "+1":
            score_context["value"] = 1 # positive feedback
        elif emoji_name == "-1":
            score_context["value"] = -1 # negative feedback
        else:
            return
        asyncio.create_task(
            delayed_score_message(post_id, score_context)
        )

    except Exception as error:
        print(f"handle_reaction(): {error}")


async def event_handler(event):
    try:
        event = json.loads(event)
        event_data = event.get("data")
        if event.get("event") == "posted" and event_data.get("channel_type") == "D": # direct messages only
            await handle_post(event_data)
        elif event.get("event") == "reaction_added":
            await handle_reaction(event_data)

    except Exception as error:
        print(f"event_handler(): {error}")


if __name__ == '__main__':
    MATTERMOST_DRIVER.init_websocket(event_handler) # wait for events
