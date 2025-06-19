#
# A chatbot to answer questions posted on mattermost
# to the user associated with the chatbot.
# Integrates LLM / RAG / mattermost 
#


__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import requests
from mattermostdriver import Driver
import json
import asyncio
from embedder import embed_documents

from chromadb import Client
from chromadb import PersistentClient

# Load persisted DB
client = PersistentClient(path="chroma_store")
collection = client.get_collection(name="chroma_docs")

def search_chroma(query: str, top_k: int = 3):
    query_embedding = embed_documents([query])[0]  # 1 vector

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas"]
    )
    return results

def format_rag_prompt(question, documents, metadatas):
    cited_context = ""
    sources_list = []

    for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
        cited_context += f"[{i}] {doc.strip()}\n\n"
        src = meta.get("source", "Unknown")
        sources_list.append(f"[{i}] Source: {src}")

    prompt = f"""You are a helpful system expert. Use only the information from the retrieved notes below to answer the question. Cite relevant facts using [n] notation. If the answer is unknown, say "I don't know".

### Retrieved Notes:
{cited_context}

### Question:
{question}

### Answer:"""
    return prompt, sources_list


def generate_response(question, thread_posts=None, top_k=3):
    # Embed the questio
    # question_embedding = embed_documents([question])[0]
    # print ("Embedded quest ", question_embedding)

    # Retrieve top-k docs from ChromaDB
    print ("Going to chroma")
    results = search_chroma(question, top_k=top_k)
    #num_results = len(results)
    print ("Returned from chroma")
    contexts = results['documents'][0]

    documents = results['documents'][0]
    metadatas = results['metadatas'][0]

    # Build prompt + citations
    base_prompt, sources = format_rag_prompt(question, documents, metadatas)

    # Add chat history if any
    if thread_posts and len(thread_posts) > 1:
        history = format_thread_as_prompt(thread_posts, bot_user_id)
        full_prompt = base_prompt + "\n\n### Chat History:\n" + history
    else:
        full_prompt = base_prompt

    #print ("Creating prompt")
    # Format thread history if exists
    #thread_history = ""
    #if thread_posts and len(thread_posts) > 1:
    #    thread_history = format_thread_as_prompt(thread_posts, bot_user_id)
    #print ("Finished creating prompt")

    # Build prompt including retrieved context and thread chat history
    #prompt = (
    #    "You are a helpful expert system. Use the following context from past notes and the conversation history to answer the question.\n\n"
    #    "### Retrieved Notes:\n"
    #    + "\n---\n".join(contexts) +
    #    "\n\n### Conversation History:\n"
    #    + thread_history +
    #    f"\nUser question:\n{question}\n\nAnswer:"
    #)

    # Query LLM server
    try:
        print ("Going to LLM")
        response = requests.post("http://localhost:8080/completion", json={
            "prompt": full_prompt,
            "n_predict": 512,
            "temperature": 0.2,
            "stop": ["###"]
        })
        answer = response.json().get("content", "").strip()
    except Exception as e:
        answer = f"[LLM error: {e}]"
        sources = []

    # Append sources list
    if sources and any(f"[{i}]" in answer for i in range(1, len(sources)+1)):
        answer += "\n\n---\nSources:\n" + "\n".join(sources)
    return answer

# Configuration
driver = Driver({
    'url': 'mattermost.web.cern.ch',
    'token': 'API_TOKEN_OF_THE_BOTUSER'
    'scheme': 'https',
    'port': 443,
    'verify': True,
    'websocket': True,
    'debug': False
})

# Login
driver.login()
bot_user_id = driver.users.get_user('me')['id']
print(f"Logged in as bot user: {bot_user_id}")

import requests

# formats chat history into new promp to keep state
def format_thread_as_prompt(posts, bot_user_id):
    prompt = ""
    for post in posts:
        user = "Assistant" if post['user_id'] == bot_user_id else "User"
        prompt += f"{user}: {post['message']}\n"
    prompt += "Assistant: "
    print ("Prompt ", prompt)
    return prompt

def query_with_rag(question, k=3):
    # Embed the question
    question_embedding = embed_documents([question])[0]
    print ("Embedded quest ", question_embedding)

    # Retrieve from ChromaDB
    results = search_chroma(
        question_embedding, top_k = 3
    )
    contexts = results['documents'][0]  # top-k chunks

    # Build prompt
    prompt = (
        "You are a helpful system expert. Based on the past notes below, "
        "answer the following question.\n\n"
        "### Notes:\n"
        + "\n---\n".join(contexts) +
        f"\n\n### Question:\n{question}\n\n### Answer:"
    )

    # Send to llama.cpp server
    response = requests.post("http://localhost:8080/completion", json={
        "prompt": prompt,
        "n_predict": 512,
        "temperature": 0.7,
        "stop": ["###"]
    })
    return response.json()["content"].strip()


# first round to classify message
def classify_message(message: str) -> str:
    prompt = (
        "You are a classifier for technical support messages. "
        "Classify the message as one of the following:\n\n"
        "- needs_context: if the message is asking a technical question, requesting explanations, bug reports, simulations, logs, data issues, or references to past events.\n"
        "- general: if the message is a greeting, question about the assistant, or simple conversational message.\n\n"
        "Reply ONLY with 'needs_context' or 'general'.\n\n"
        "Examples:\n"
        "Message: How can I help you? → general\n"
        "Message: Hi, what can you do? → general\n"
        "Message: Have we seen this crash before? → needs_context\n"
        "Message: How can I do an anchoredMC simulation in AliceO2? → needs_context\n"
        "Message: What are ways to connect to the EPN farm? → needs_context\n"
        f"Message: {message}\nAnswer:"
    )

    try:
        response = requests.post("http://localhost:8080/completion", json={
            "prompt": prompt,
            "n_predict": 10,
            "temperature": 0.0,
            "stop": ["\n"]
        })
        answer = response.json()["content"].strip().lower()
        if "needs_context" in answer:
            return "needs_context"
        return "general"
    except Exception as e:
        print(f"[Classifier error: {e}]")
        return "general"  # safe fallback


# === Function to forward message to llama-server ===
def send_to_llm(message, prompt = None):
    if prompt == None:
        prompt = f"User: {message}\nAssistant:"
    try:
        response = requests.post("http://localhost:8080/completion", json={
            "prompt": prompt,
            "temperature": 0.7,
            "stream": False,
            "n_predict": 256
        })
        data = response.json()
        return data.get("content", "").strip()
    except Exception as e:
        return f"[LLM error: {e}]"

thread_classification_cache = {}

async def my_event_handler(event):
    try:
        event_data = json.loads(event) if isinstance(event, str) else event

        if event_data.get('event') == 'posted':
            post_data = json.loads(event_data['data']['post'])
            if post_data.get('user_id') != bot_user_id:
                message = post_data.get('message', '')
                channel_id = post_data.get('channel_id')

                thread_root_id = post_data.get('root_id') or post_data.get('id')

                thread = driver.posts.get_thread(thread_root_id)
                all_posts = thread['posts']
                sorted_posts = [all_posts[k] for k in sorted(all_posts, key=lambda k: all_posts[k]['create_at'])]
                length_thread = len(sorted_posts)

                print(f"Received: {message} which is part of a thread with {length_thread} messages")

                #prompt = None
                #if length_thread > 1:
                #   prompt = format_thread_as_prompt(sorted_posts, bot_user_id)

                # Post placeholder
                thinking_post = driver.posts.create_post({
                    'channel_id': channel_id,
                    'message': "_🤖 Thinking..._" ,
                    'root_id': thread_root_id
                })

                # Get LLM reply
                # Determine if we already classified this thread
                if thread_root_id not in thread_classification_cache:
                     classification = classify_message(message)
                     thread_classification_cache[thread_root_id] = classification
                     print(f"Classified thread {thread_root_id} as: {classification}")
                else:
                     classification = thread_classification_cache[thread_root_id]

                if classification == "needs_context":
                   llm_reply = generate_response(message, sorted_posts)
                else:
                   prompt = format_thread_as_prompt(sorted_posts, bot_user_id)
                   llm_reply = send_to_llm(message, prompt)

                # llm_reply = generate_response(message, thread_posts=sorted_posts)

                # Edit original post with real content
                driver.posts.update_post(thinking_post['id'], {
                    'id': thinking_post['id'],
                    'channel_id': channel_id,
                    'message': llm_reply,
                    'root_id': thread_root_id 
                })

                print(f"LLM replied: {llm_reply}")

    except Exception as e:
        print(f"Error handling event: {e}")

# Start websocket connection
driver.init_websocket(my_event_handler)

# Keep the connection alive
try:
    while True:
        asyncio.sleep(1)
except KeyboardInterrupt:
    print("\nBot stopped")
