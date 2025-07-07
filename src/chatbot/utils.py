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


def messages_to_string(messages):
    str = "[\n"
    for msg in messages:
        if isinstance(msg, SystemMessage):
            str += f"System: {msg.content}\n"
        elif isinstance(msg, HumanMessage):
            str += f"User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            str += f"Assistant: {msg.content}\n"
        else:
            raise ValueError(f"Invalid message type: {msg.type}")
    str += "]"
    return str
