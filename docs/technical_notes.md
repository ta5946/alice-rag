# ALICE chatbot development notes

_27. 6. 2025_

_Tjaš Ajdovec_


## Setup

### Environment and configuration

If you need to refresh the Docker group use:
```bash
newgrp docker
```

To activate the python virtual environment with the required packages:
```bash
source ~/.virtualenvs/alice-rag/bin/activate
```

To set python path to the project directory:
```bash
export PYTHONPATH="~/rag:$PYTHONPATH"
```

The **chatbot configuration** is stored and can be changed in the `.env` file similar to the `.env.example`. This includes the selection of language model,
embedding model and vector database properties.

### LLM server

To run the models we are using a CUDA compiled version of the **llama.cpp** server. It can be run as a Docker container with:
```bash
docker run --gpus all -p 8080:8080 -v "./models/llama.cpp:/root/.cache/llama.cpp" ghcr.io/ggml-org/llama.cpp:server-cuda --hf-repo <user>/<model>:<quant> --n-gpu-layers 50 --no-kv-offload --host 0.0.0.0
```

An example of a HuggingFace model repository is `TheBloke/Mistral-7B-Instruct-v0.1-GGUF:Q4_K_M`. The GPU utilization can be adjusted with the number of layers.
The current version of the LLM server is found in the `docker-compose.yml` file. Web interface for testing purposes is available [here](http://pc-alice-ph01:8080/).
With CUDA support, the interface is about 5x faster (~55 tokens per second).


## Models used

### LLM selection

Models were selected based on [Chatbot Arena](https://huggingface.co/spaces/lmarena-ai/chatbot-arena-leaderboard) scores, the number of HuggingFace downloads 
and space limitations of the NVIDIA GeForce RTX 2080 GPU.

| Model                      | Quantization | Size   | Context length | Notes                                              |
|----------------------------|--------------|--------|----------------|----------------------------------------------------|
| Mistral-7B-Instruct-v0.1   | 4 bit        | 4.4 GB | ?              | Initial model, has special token repetition issues |
| Mistral-7B-Instruct-v0.3   | 6 bit        | 6.0 GB | 32k tokens     | Improved version of Mistral                        |
| Qwen2.5-7B-Instruct        | 6 bit        | 6.7 GB | 32k tokens     | Good at instruction following, useful for RAG      |
| Meta-Llama-3.1-8B-Instruct | 6 bit        | 6.6 GB | 32k tokens     | All around model                                   |
| gemma-3-12b-it             | 3 bit        | 6.0 GB | 8k tokens      | Quantization may be too heavy                      |

To estimate the VRAM usage of a model for some number of layers and context length: https://huggingface.co/spaces/oobabooga/accurate-gguf-vram-calculator.

###  Embedding model

For document embedding we can use the **sentence-transformers** library. Models are pulled from HuggingFace repository, such as `BAAI/bge-base-en-v1.5`
and cached locally under `/models`. 

> We can later upgrade the model to `BAAI/bge-m3` or others (check [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)).

### Reranking model

For cross scoring the query and the documents we also use a LangChain wrapper of the sentence-transformers library. The current `BAAI/bge-reranker-base`
can be upgraded to a larger `BAAI/bge-reranker-v2-m3`. Some manual testing showed better performance of explicit similarity scoring over the default cosine 
similarity of document embeddings.


## Data and indexing

### Documents

_At this point the documentation from https://github.com/AliceO2Group/simulation/tree/main/docs and working simulation examples from https://github.com/AliceO2Group/AliceO2/tree/dev/run/SimExamples
are stored in the `/data` directory. Later they should be pulled directly from the repositories._

See how **indexer** works and also check other relevant GitHub repos.

### Vector store

The script `indexer.py` 1. Reads the repositories and file types declared in the YAML file, 2. Creates a persistent Chroma vector database, 3. Computes hashes for pulled
documents, 4. Computes embeddings and stores new or changed documents. It works without issues so far.

By default, ChromaDB uses cosine similarity = 1 - cosine distance to return the *top k* most similar documents to the query.
It then uses a reranker to cross score them and return only the *top n* which are used as problem context for the LLM.

To clean up the vector store use:
```bash
rm -rf data/
```

### Chunking

Chunk size is defined in the `.env` file in characters. The number of tokens per chunk is approximately this / 4.
The current retrieval parameters are:
- `chunk_size=1000` characters,
- `chunk_overlap=100` characters,
- `similarity_threshold=0.25` cosine similarity retrieval threshold,
- `top_k=20` retrieved chunks,
- `top_n=5` final reranked chunks.

Compact language models do not perform better when flooded with context, so the number of chunks is limited to 5.
When using a more capable generative model (LLM), the parameters can be increased within the limits of reasonable context length (32k tokens).


## RAG pipeline

### LangChain ecosystem

TODO + / -, describe components, tracing and annotating runs

### LangFuse tracing

Is an open source alternative to LangSmith. To set up a self-hosted LangFuse server:

```bash
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up
```

Open `langfuse/docker-compose.yml` and set `NEXTAUTH_URL=http://<your-public-ip>:3000`. 
Then continue to creating an account, organization and set up a project where you can trace your LLM runs.

To view the history of chatbot RAG pipeline runs use credentials `user@cern.ch/password1.` and log in to the project home at
http://pc-alice-ph01:3000/project/cmcn8idin0007ob07gtv37lmu.


### Mattermost integration

The chatbot is integrated as a user **ask.alice.beta@cern.ch** in Mattermost, with its own `MATTERMOST_TOKEN`. It only responds to direct messages.
The RAG domain has been limited to O2 simulation documentation.

To persistently run the mattermost event handling script:
```bash
nohup python src/chatbot/mattermost_listener.py > chatbot.log 2>&1
# or
python run.py
```


## Evaluation

### Component testing

The `/tests` directory contains short scripts for testing basic functionalities of individual LangChain components. This includes the LLM, embedding model, 
reranking model and vector store. They can be run with `pytest` from the root directory.

_Due to GPU limitations, stop the chatbot service before running the tests and vice versa._

### Chatbot evaluation plan

The folder `doc/evaluation_ideas` contains ideas for evaluating a RAG chatbot without a human annotated question-answer dataset.
They are based on deep research conducted by ChatGPT and Gemini.

> Generate a synthetic dataset by creating a question-answer pair for each document <d, q, a>.

Retrieval evaluation:
- Mean Reciprocal Rank (**MRR**) is the average retrieval rank of the relevant document for some question.
- Recall at K (**recall@k**) is the proportion of time the relevant document is retrieved in the top K results.
- _LLM-as-a-judge_ can determine the ratio of relevant documents in the top K results.

Faithfulness evaluation:
- Citation Accuracy is the proportion of time the LLM correctly cites the relevant document.
- _LLM-as-a-judge_ can determine the ratio of claims that are supported by the retrieved documents.

Response evaluation:
- **ROUGE** score measures the overlap between the generated response and correct answer.
- Or use **Semantic similarity** between the generated response and correct answer.
- _LLM-as-a-judge_ can score the response on a scale from 1 to 5 based on some criteria.

Chatbot evaluation:
- _Human-in-the-loop_ can provide feedback on the generated responses, such as helpfulness.


## Question extraction

### Mattermost

To create a dataset of frequent questions about ALICE O2 simulations requiring support from experts, we scraped the [O2 Simulation Mattermost channel](https://mattermost.web.cern.ch/alice/channels/o2-simulation).
We filtered out system messages, bug reports and answers from the experts. Then used the LLM to extract the actual questions which took around 10 minutes.
Result is ~110 straightforward questions in stored in the file `src/scraper/questions_v2.json`.


## TODOs and improvements

- Enable LLM reasoning (Qwen3?)
- Build an evaluation question-answer dataset
- Benchmark the base LLM and RAG chatbot using answer correctness metrics
- _Scrape Jira issues from O2 (filters general, production request)_
- Implement the environment variable collection and script generating capability
- Chatbot in Mattermost channel could tell the user to submit a Jira ticket
