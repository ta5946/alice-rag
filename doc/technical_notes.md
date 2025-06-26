## Environment setup

If you need to refresh the Docker group use:
```bash
newgrp docker
```

To activate the python virtual environment with the required packages:
```bash
source ~/.virtualenvs/alice-rag/bin/activate
```

The **chatbot configuration** is stored and can be changed in the `.env` file similar to the `.env.example`. This includes the selection of language model,
embedding model and vector database properties.


## LLM server

To run the models we are using a CUDA compiled version of the **llama.cpp** server. It can be run as a Docker container with:
```bash
docker run --gpus all -p 8080:8080 -v "./models/llama.cpp:/root/.cache/llama.cpp" ghcr.io/ggml-org/llama.cpp:server-cuda --hf-repo <user>/<model>:<quant> --n-gpu-layers 50 --no-kv-offload --host 0.0.0.0
```

An example of a HuggingFace model repository is `TheBloke/Mistral-7B-Instruct-v0.1-GGUF:Q4_K_M`. The GPU utilization can be adjusted with the number of layers.
The current version of the LLM server is found in the `docker-compose.yml` file. Web interface for testing purposes is available [here](http://pc-alice-ph01:8080/).
With CUDA support, the interface is about 5x faster (~55 tokens per second).


### LLM selection

Models were selected based on [Chatbot Arena](https://huggingface.co/spaces/lmarena-ai/chatbot-arena-leaderboard) scores, the number of HuggingFace downloads 
and space limitations of the NVIDIA GeForce RTX 2080 GPU.

| Model                      | Quantization | VRAM space | Context length | Notes                                              |
|----------------------------|--------------|------------|----------------|----------------------------------------------------|
| Mistral-7B-Instruct-v0.1   | 4 bit        | 4.4 GB     | ?              | Initial model, has special token repetition issues |
| Mistral-7B-Instruct-v0.3   | 6 bit        | 6.0 GB     | 32k tokens     | Improved version of Mistral                        |
| Qwen2.5-7B-Instruct        | 6 bit        | 6.7 GB     | 32k tokens     | Good at instruction following, useful for RAG      |
| Meta-Llama-3.1-8B-Instruct | 6 bit        | 6.6 GB     | 32k tokens     | All around model                                   |
| gemma-3-12b-it             | 3 bit        | 6.0 GB     | 8k tokens      | Quantization may be too heavy                      |


### LangChain ecosystem

TODO + / -


## Embedding model

For document embedding we can use the **sentence-transformers** library. Models are pulled from HuggingFace repository, such as `BAAI/bge-base-en-v1.5`
and cached locally under `/models`. 

> We can later upgrade the model to `BAAI/bge-m3` (check [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)).


## Documents
_At this point the documentation from https://github.com/AliceO2Group/simulation/tree/main/docs and working simulation examples from https://github.com/AliceO2Group/AliceO2/tree/dev/run/SimExamples
are stored in the `/data` directory. Later they should be pulled directly from the repositories._

See how **indexer** works.


## Vector store

The script `indexer.py` 1. Reads the repositories and file types declared in the YAML file, 2. Creates a persistent Chroma vector database, 3. Computes hashes for pulled
documents, 4. Computes embeddings and stores new or changed documents. It has no issues so far.


## Improvements

- Performance metrics (latency, tokens/second)
- Use reranking model after retrieval
- Enable LLM reasoning
- Include document metadata and references (links)
- Stream LLM responses (word by word)
