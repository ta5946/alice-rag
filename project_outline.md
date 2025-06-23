# RAG chatbot self-hosted notes

Short notes and code pointers for self-hosted RAG setup, with a mattermost chat interface.

## Ingredients

- llama.cpp for self-hosting LLM models from huggingface
- an LLM model file (I tried mistral-7b-instruct-v0.1.Q4_K_M.gguf) 
- chroma-DB as the vector database for text-chunks
- a script that reads ALICE expert documents and puts chunks into chroma-DB (only needed initially or when adding documents)
- a script that connects mattermost with Chroma and the hosted LLM (the runtime)

## Step 1: Hosting your own LLM

- An LLM is needed for the language and reasoning capabilities
- git clone `https://github.com/ggerganov/llama.cpp` providing a generic C++ interface to LLMs.
- build it
- download a model file (`model.gguf`) from huggingface; Without a powerful NVIDA GPU we need to restrict to smaller models such as Mistral-7B
- run it with `llama-server -m model.gguf -t 8 --port 8090`
- test it with 
    ```
    curl http://localhost:8090/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Why is the sky blue?",
    "n_predict": 128}'
    ```
    
## Step 2: Create a document database for domain knowledge retrieval

- needs text embedder model
- and ChromaDB
- code to follow
- idea is to maintain a list of ALICE documents (URLs, markdowns, notes) and embedd them into the database with a cron-job

## Step 3: A python script doing RAG and connecting mattermost with the LLM/Chroma

- python code in `https://github.com/sawenzel/alice-rag/`
