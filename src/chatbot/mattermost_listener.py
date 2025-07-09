import json
import asyncio
from basic_rag_qa import qa_pipeline
import simulation_chatbot_prompts as prompts
from mattermost_utils import MATTERMOST_DRIVER, BOT_ID, get_thread_messages
from dotenv import load_dotenv

load_dotenv()


async def event_handler(event):
    try:
        event = json.loads(event)
        event_data = event.get("data")
        if not (event.get("event") == "posted" and event_data.get("channel_type") == "D"): # direct messages only
            return
        post_data = json.loads(event_data.get("post"))
        if post_data.get("user_id") == BOT_ID: # ignore bot messages
            return

        print("HANDLING EVENT:")
        print(event)
        channel_id = post_data.get("channel_id")
        post_id = post_data.get("id")
        post_message = post_data.get("message")
        thread_id = post_data.get("root_id") or post_id
        thread_messages = get_thread_messages(thread_id)
        thread_messages = thread_messages[:-1] if thread_messages and thread_messages[-1].content == post_message else thread_messages # exclude last message

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

        # generate chatbot response
        if len(thread_messages) == 0:
            asyncio.create_task(
                qa_pipeline(post_message, prompts.default_message_history, feedback=False, mattermost_context=mattermost_context)
            )
        else:
            asyncio.create_task(
                qa_pipeline(post_message, thread_messages, feedback=False, mattermost_context=mattermost_context)
            )

    except Exception as error:
        print(f"event_handler(): {error}")


if __name__ == '__main__':
    MATTERMOST_DRIVER.init_websocket(event_handler) # wait for events
