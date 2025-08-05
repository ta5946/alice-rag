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

### Search query

Before invoking the vector database, the LLM takes in the conversation history and user message to **generate a search query**.
The keyword based search proved to be less effective than using sentences or questions.
We also try to **reduce noise** by avoiding frequent terms, such as "O2", "simulation", "o2-sim", "documentation", "ALICE".

> For more details take a look at [this conversation](./chats/search_query_issue.md) about the search query generation issue.


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

### Correctness results

First we evaluated 3 different models on the expert labeled question-answer dataset. It consisted of 25 pairs.
- **Qwen2.5-7B-Instruct** is the base local LLM,
- **Qwen-RAG** is a RAG chatbot using this model and O2 simulation documentation,
- **Gemini-2.5-Flash** is a state-of-the-art API model from Google: https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash.

> Google offers a free tier API key with a rate limit depending on the model https://ai.google.dev/gemini-api/docs/rate-limits#free-tier.

Current results indicate that RAG pipeline introduces **new information**, that was not present in the general pretraining:

| **Chatbot model**   | **BLEU score** | **ROUGE-L score** | **Semantic similarity** | **Qwen judge score** | **Gemini judge score** | **Inference time (s / question)** |
|---------------------|----------------|-------------------|-------------------------|----------------------|------------------------|-----------------------------------|
| Qwen2.5-7B-Instruct | 0.010          | 0.060             | 0.734                   | 2.80                 | 1.44                   | 16.6                              |
| Gemini-2.5-Flash    | 0.006          | 0.038             | 0.737                   | 2.72                 | 2.52                   | 19.1                              |
| Qwen-RAG            | 0.070          | 0.159             | 0.797                   | 3.16                 | 3.12                   | 14.7                              |
| Qwen-Extended-RAG   | 0.066          | 0.158             | 0.798                   | 3.44                 | 3.88                   | 44.4                              |

This table _should be updated_ with:
- More expert questions,
- More models,
- Different RAG parameters (configurations).

### Initial evaluation

For the first iteration of evaluation we used 3 similarity metrics and 2 different judges.
Each chatbot model generated only one response to each question in the dataset and the generated answers were compared to correct ones.
Extended RAG represents a configuration focused on high recall and no time constraints.

1. BLEU score comparison:
![BLEU score comparison](/img/plots/1_sample/qwen_judge/bleu_score_comparison.png)

2. ROUGE-L score comparison:
![ROUGE-L score comparison](/img/plots/1_sample/qwen_judge/rouge_l_score_comparison.png)

3. Semantic similarity comparison:
![Semantic similarity comparison](/img/plots/1_sample/qwen_judge/semantic_similarity_comparison.png)

4. Qwen-as-judge comparison:
![Qwen-as-Judge comparison](/img/plots/1_sample/qwen_judge/llm_judge_score_comparison.png)

5. Gemini-as-judge comparison:
![Gemini-as-Judge comparison](/img/plots/1_sample/gemini_judge/llm_judge_score_comparison.png)

6. Average response time comparison:
![Average_response time comparison](/img/plots/1_sample/qwen_judge/time_comparison.png)

#### Findings:
- BLEU is the least relevant metric for our task,
- A single answer (sample with `temperature = 0.7`) is not reliable enough,
- Google Gemini API does not guarantee deterministic results (unfit for judge),
- Gemini-2.5-Flash has a hard limit of 250 requests per day (Flash-Lite has 1000)
- RAG parameters impact both the results and inference time.

#### Propositions:
- Focus on ROUGE-L, semantic similarity and LLM judge score.
- Set a latency requirement (e.g. 30 seconds per question),
- Find a capable open source LLM judge,
- Sample `n >= 5` answers to increase the evaluation reliability,
- Visualize the results with a **box plot** (instead of bar chart).

Sources:
- [How to get consistent results when using gemini api?](https://discuss.ai.google.dev/t/how-to-get-consistent-results-when-using-gemini-api/60826)
- [Is a Zero Temperature Deterministic?](https://medium.com/google-cloud/is-a-zero-temperature-deterministic-c4a7faef4d20)

### Judge evaluation

Gemini-2.5-Flash is the most capable free LLM, but it has a request limit.

#### Idea:
_Find the most similar open source judge by calculating correlation metrics based on a vector of answer scores._

| **Rank** | **Judge model**            | **Pearson correlation** | **Spearman correlation** | **RMSE distance** |
|----------|----------------------------|-------------------------|--------------------------|-------------------|
| 1        | Gemini-2.5-Flash-Lite      | 0.766                   | 0.768                    | 0.684             |
| 2        | Qwen3-8B (reasoning)       | 0.633                   | 0.643                    | 0.856             |
| 3        | Gemma-2-9b-it              | 0.558                   | 0.570                    | 0.940             |
| 4        | Mistral-7B-Instruct-v0.3   | 0.546                   | 0.553                    | 0.953             |
| 5        | Qwen2.5-7B-Instruct        | 0.489                   | 0.499                    | 1.011             |
| 6        | Meta-Llama-3.1-8B-Instruct | 0.315                   | 0.298                    | 1.171             |

#### Findings: 
- Qwen3-8B is the most reliable reasoning local LLM judge,
- Gemma-2-9b-it is the best non-reasoning (efficient) judge.


## Knowledge base

### Mattermost question extraction

To create a dataset of frequent questions about ALICE O2 simulations requiring support from experts, we scraped the [O2 Simulation Mattermost channel](https://mattermost.web.cern.ch/alice/channels/o2-simulation).
We filtered out system messages, bug reports and answers from the experts. Then used the LLM to extract the actual questions which took around 10 minutes.
Result is ~110 straightforward questions in stored in the file `src/scraper/questions_v2.json`.

### Expert dataset collection

For evaluation purposes O2 simulation experts provided some frequently asked questions and answers (FAQs). They were unorganized and given in a markdown file.
To generate a structured JSON dataset we used GPT-4.1-mini with enabled reasoning and the following prompt:

_I will provide you with text that contains questions and answers. Your task is to return a list of JSON objects with fields "author", "question", "answer". If there is no answer: set the field to None. If there are multiple questions but only one answer: restructure it into multiple parts. Do not introduce any new questions or information. Return only a list of JSON objects._

The process is demonstrated in [this chat](https://chatgpt.com/share/687e3d47-3f54-8013-916b-d15158683e78). 
The extracted knowledge / qa pairs are stored in the file `eval/datasets/qa_dataset_gpt.json`.


## Code generation

### Prototype script

Below is a minimal prototype of anchoredMC simulation script described here: https://aliceo2group.github.io/simulation/docs/o2dpgworkflow/anchored.html
For development purposes we only took a subset of all environment variables.

```bash
#!/usr/bin/env bash

# Required variables
export ALIEN_JDL_LPMRUNNUMBER=545312
export ALIEN_JDL_LPMANCHORPASSNAME=apass4
export ALIEN_JDL_LPMINTERACTIONTYPE=Pb-Pb
export SPLITID=25
export NTIMEFRAMES=3

# Optional variables
export ALIEN_JDL_CPULIMIT=12
export ALIEN_JDL_SIMENGINE=TGeant4
export ALIEN_JDL_ANCHOR_SIM_OPTIONS="-gen pythia8 --trigger-external"
export NSIGEVENTS=8000
export CYCLE=1

# Start the workflow
${O2DPG_ROOT}/MC/run/ANCHOR/anchorMC.sh
```

| Variable                       | Type     | Default | Values                        | Description                                                                                                  |
|--------------------------------|----------|---------|-------------------------------|--------------------------------------------------------------------------------------------------------------|
| **REQUIRED VARIABLES**         |
| `ALIEN_JDL_LPMRUNNUMBER`       | Required | -       | Positive integer              | The ALICE run number to which this MC job anchors, defining the experimental conditions and detector setup   |
| `ALIEN_JDL_LPMANCHORPASSNAME`  | Required | -       | String                        | The reconstruction pass/cycle identifier (e.g., apass4) that determines which reconstruction settings to use |
| `ALIEN_JDL_LPMINTERACTIONTYPE` | Required | -       | ["pp", "Pb-Pb"]               | The collision system type, either proton-proton (pp) or lead-lead (Pb-Pb) interactions                       |
| `SPLITID`                      | Required | -       | Positive integer <= 100       | Identifies which temporal split within the run to simulate, corresponding to specific timestamps             |
| `NTIMEFRAMES`                  | Required | -       | Positive integer              | Number of consecutive timeframes to generate for this MC job, defining the data volume                       |
| **OPTIONAL VARIABLES**         |
| `ALIEN_JDL_CPULIMIT`           | Optional | 8       | Positive integer              | Expected CPU time limit in hours that the workflow runner will assume for resource allocation                |
| `ALIEN_JDL_SIMENGINE`          | Optional | TGeant4 | ["TGeant3", "TGeant4", "VMC"] | Monte Carlo particle transport engine used for simulating detector interactions                              |
| `ALIEN_JDL_ANCHOR_SIM_OPTIONS` | Optional | ""      | String flags                  | Additional simulation parameters and event generator configuration (e.g., "-gen pythia8pp")                  |
| `NSIGEVENTS`                   | Optional | 10000   | Positive integer              | Maximum number of signal events per timeframe, actual count may be lower based on interaction rates          |
| `CYCLE`                        | Optional | 0       | Non-negative integer          | Cycle number within the production to simulate, allowing multiple iterations over the same time period       |

This subset covers the core anchoring parameters, job splitting configuration, and key customization options that would be most relevant for a demonstration.

### Script evaluation

The evaluation process works in 3 steps, from low to high level checking:
1. The **required variables** are collected from the generated script (static analysis). The missing optional variables are set to default values.
2. The environment **variable values** are checked against the expected values (static validation).
3. The mock `anchoredMC.sh` **script is run**. The parameters have to be set correctly (just like real simulation) and the script has to run without errors (dynamic validation).


## TODOs and improvements

- _Scrape Jira issues from O2 (filters general, production request)_
- **Fix broken chatbot citations**

### Code generation
- https://aliceo2group.github.io/simulation/docs/o2dpgworkflow/anchored.html
- Prototype script runner
- Script generation chatbot state
- Variable collection
- Script correctness (static and dynamic)

### Question answering
- More question-answer pairs
- Repeat question extraction process
- Repeat chatbot evaluation (Mistral and other models)
