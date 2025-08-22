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

### HPC machine

To connect to the machine with MI100 GPUs:
```bash
# From CERN network or lxplus
ssh tajdovec@alihlt-gw-prod.cern.ch -p 2020
ssh epn320
```

If we want to access the llama.cpp server on our `pc-alice-ph01` machine, we have to **forward the remote port 8080** to some local port, such as 8090.
```bash
ssh -L 0.0.0.0:8090:127.0.0.1:8080 -J tajdovec@alihlt-gw-prod.cern.ch:2020 tajdovec@epn320
# Prompted for password
```

To check the VRAM usage on AMD graphics cards and set the visible device(s):
```bash
rocm-smi
# Visible devices are not ordered
export HIP_VISIBLE_DEVICES=0
echo $HIP_VISIBLE_DEVICES
```

Because we are not using the standard NVIDIA CUDA toolkit, we have to compile llama.cpp with HIP support:
```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
HIPCXX="$(hipconfig -l)/clang" HIP_PATH="$(hipconfig -R)" \
    cmake -S . -B build -DGGML_HIP=ON -DAMDGPU_TARGETS=gfx908 -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build --config Release -- -j 16
# On finish [100%] Built target llama-server
```

To manage active ssh connections on local device and remote LLM server(s):
```bash
ps -ef | grep ssh
ps aux | grep llama
# To kill all ssh connections
pkill -f "^ssh -[lu]"
# To terminate all llama-server instances
pkill -f "^llama.cpp"
```

---

**Enable port forwarding and run the llama.cpp server on remote machine:**
```bash
ssh -f -L 0.0.0.0:<local_port>:127.0.0.1:<remote_port> -J tajdovec@alihlt-gw-prod.cern.ch:2020 tajdovec@epn320 "HIP_VISIBLE_DEVICES=<x> llama.cpp/build/bin/llama-server --hf-repo <user>/<model>:<quant> --n-gpu-layers 1000 --no-kv-offload --ctx-size 32000 --n-predict 4000 --port <remote_port>"
# Configure --n-predict
```

We selected the best performing models of sizes up to 30B parameters. Currently, the available LLM instances are:

| Model Name                                                                                                     | Instance URL              | Notes                               |
|----------------------------------------------------------------------------------------------------------------|---------------------------|-------------------------------------|
| [gpt-oss-20b](https://huggingface.co/unsloth/gpt-oss-20b-GGUF)                                                 | http://pc-alice-ph01:8090 | Reasoning model                     |
| [Qwen3-30B-A3B-Instruct-2507](https://huggingface.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF)                 | http://pc-alice-ph01:8091 | Faster because of active parameters |
| [Mistral-Small-3.2-24B-Instruct-2506](https://huggingface.co/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF) | http://pc-alice-ph01:8092 |                                     |
| [gemma-3-27b-it](https://huggingface.co/unsloth/gemma-3-27b-it-GGUF)                                           | http://pc-alice-ph01:8093 | Slower architecture?                |
| [DeepSeek-R1-Distill-Qwen-32B](https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-32B-GGUF)               | http://pc-alice-ph01:8094 | Hard reasoning model                |

They are all reachable via API endpoint like `<llm_url>/v1` or through the unified [OpenWebUI chat interface](http://pc-alice-ph01:8081).

### GitHub workflows

So far we are installing all the dependencies and running Pylint on files and packages in this repository.
You can run the Python linter locally with:
```bash
pip install pylint
pylint $(git ls-files '*.py')
```


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

### "Training" documents

_At this point the documentation from https://github.com/AliceO2Group/simulation/tree/main/docs and working simulation examples from https://github.com/AliceO2Group/AliceO2/tree/dev/run/SimExamples
are stored in the `/data` directory. Later they should be pulled directly from the repositories._

See how **indexer** works and also check other relevant GitHub repos.

### Defined resources

As mentioned later, the script `src/data_indexer/index.py` reads the GitHub repositories and file types from the `knowledge_base.yaml` configuration.
The defined resources are then treated with the appropriate _Loader_ and stored in the vector database.
Currently (18. 8. 2025) that includes **real data**:
- ALICE O2 simulation documentation from https://github.com/AliceO2Group/simulation,
- Script and configuration examples from https://github.com/AliceO2Group/O2DPG,
- Parts of O2 software project from https://github.com/AliceO2Group/AliceO2,
- Selected presentations on O2 simulations from https://github.com/ta5946/alice-rag/tree/master/data/knowledge_base/presentations.

And **synthetic data**:
- Question and answer pairs generated by an LLM on previously mentioned documents, available here https://github.com/ta5946/alice-rag/tree/master/data/knowledge_base/synthetic.

For more details or potential configuration changes refer to the [YAML file](/src/data_indexer/knowledge_base.yml).

### Vector store

The script `index.py` 1. Reads the repositories and file types declared in the YAML file, 2. Creates a persistent Chroma vector database, 3. Computes hashes for pulled
documents, 4. Computes embeddings and stores new or changed documents. It works without issues so far.

By default, ChromaDB uses cosine similarity = 1 - cosine distance to return the *top k* most similar documents to the query.
It then uses a reranker to cross score them and return only the *top n* which are used as problem context for the LLM.

To clean up the vector store use:
```bash
rm -rf data/
```

### Text chunking

Chunk size is defined in the `.env` file in characters. The number of tokens per chunk is approximately this / 4.
The current retrieval parameters are:
- `chunk_size=1000` characters,
- `chunk_overlap=100` characters,
- `similarity_threshold=0.25` cosine similarity retrieval threshold,
- `top_k=20` retrieved chunks,
- `top_n=5` final reranked chunks.

Compact language models do not perform better when flooded with context, so the number of chunks is limited to 5.
When using a more capable generative model (LLM), the parameters can be increased within the limits of reasonable context length (32k tokens).

Update: Evaluated different text chunking strategies, such as `RecursiveCharacterTextSplitter()` with different chunk sizes (500, 1000 and 2000) and `SemanticChunker()`.
Semantic chunking did not improve chatbot performance. 1000 character chunks are the most effective with Qwen2.5-7B-Instruct and bge-base-en-v1.5.

![Text chunking comparison](/img/plots/chunk_size/gemma_judge/llm_judge_score_comparison.png)

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

### Real world examples

Below are some questions brought up by real users in the [O2 simulation Mattermost channel](https://mattermost.web.cern.ch/alice/channels/o2-simulation) 
and answers generated by the _current version_ of askALICE chatbot (13. 8. 2025, https://github.com/ta5946/alice-rag/commit/31438f37eb002b8a23ab10f19ad4e9c4208995bf).

```text
D:  3. 6. 2025
Q:  Dear experts,
    I'm trying to find the PYTHIA tune used in general purpose Run3 pp simulations.
    Looking at O2DPG for "tune" (in particular in the o2dpg_sim_workflow `externalPythia8Config == None` case, or in .cfg files or mkpy8cfg.py) , I do not see any setting for it except for some PWG specific configs. So can I safely assume that the tune used is the default PYTHIA tune? (Monash 2013 if I understand the PYTHIA documentation correctly)

A:  Based on the provided context, if `externalPythia8Config == None` in the o2dpg_sim_workflow or in the .cfg files or mkpy8cfg.py, you can safely assume that the default PYTHIA tune used is Monash 2013, as this is the default setting for Pythia8 in the examples and documentation provided.

    **Sources:**
    1. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo_Transcript.md
    2. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_Nov2024/MCTutorial4Giacalone.pdf
    3. https://github.com/ta5946/alice-rag/blob/master/data/knowledge_base/ALICE-simulation-tutorial.pptx-1.pdf
    4. https://github.com/AliceO2Group/AliceO2/blob/dev/doc/DetectorSimulation.md
    5. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo.pdf
    6. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo.pdf
    7. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_Nov2024/MCTutorial4Giacalone.pdf
    8. https://github.com/ta5946/alice-rag/blob/master/data/knowledge_base/ALICE-simulation-tutorial.pptx-1.pdf
    9. https://github.com/ta5946/alice-rag/blob/master/data/knowledge_base/MC_Tutorials.pdf
    10. https://github.com/ta5946/alice-rag/blob/master/data/knowledge_base/MC_Tutorials.pdf
    
    ---
    
    _Help us improve the askALICE chatbot by providing your feedback. React to this message with 👍 if the answer was helpful or 👎 if it was not._


D:  23. 6. 2025
Q:  Is there a way to run this without ALICE reconstruction? Just pure MC truth?

A:  To run the simulation without ALICE reconstruction and just use pure MC truth, you can use the `MCReplay` engine as described in the documentation. This engine allows you to replay a simulation based on steps logged by the `MCStepLogger`. Here is how you can do it:
    
    ```bash
    o2-sim-serial -n <ref_nevents> -e MCReplay -g extkinO2 --extKinFile o2sim_Kine.root -o replay
    ```
    
    Make sure to use a different output prefix to avoid overwriting the hit files that you are interested in. Also, ensure you use the same modules and settings as in the reference run.
    
    **Sources:**
    1. https://github.com/AliceO2Group/AliceO2/blob/dev/doc/DetectorSimulation.md
    2. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo.pdf
    3. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_Nov2024/MCTutorial4Giacalone.pdf
    4. https://github.com/ta5946/alice-rag/blob/master/data/knowledge_base/ALICE-simulation-tutorial.pptx-1.pdf
    5. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo.pdf
    6. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo.pdf
    7. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_Nov2024/MCTutorial4Giacalone.pdf
    8. https://github.com/ta5946/alice-rag/blob/master/data/knowledge_base/ALICE-simulation-tutorial.pptx-1.pdf
    9. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_Nov2024/MCTutorial4Giacalone.pdf
    10. https://github.com/ta5946/alice-rag/blob/master/data/knowledge_base/ALICE-simulation-tutorial.pptx-1.pdf
    
    ---
    
    _Help us improve the askALICE chatbot by providing your feedback. React to this message with 👍 if the answer was helpful or 👎 if it was not._


D:  30. 7. 2025
Q:  Hello, I wanted to use official ALICE centrality Rivet implementation, but I get an error:
       Rivet.Analysis.ALICE_2025_angular: ERROR  No reference calibration file for CentralityProjection ALICE_2015_CENT_PP found.
       Did you mean to generate one yourself?
       Once generated, you can preload the calibration file using the -p flag
    
    Do you have any suggestions? Is there some example / manual for using ALICE centrality? I found examples of how it should be implemented in the cc code, but it seems I am missing "calibration file" which should probably be generated beforehand...

A:  It seems like you are encountering an issue with the centrality calibration file required for running the Rivet analysis. To address this, I recommend creating a JIRA ticket in our project management system. Here’s how you can proceed:
    
    1. **Navigate to the JIRA System**: Go to [this link](https://alice.its.cern.ch/jira/projects/O2) to open the JIRA system.
    2. **Create a New Issue**: Click on the "Create" button (usually represented by a green plus sign) to start a new issue.
    3. **Select the Correct Component**: Choose "Simulation" as the component for your ticket.
    4. **Fill Out the Ticket Details**:
       - **Summary**: Provide a clear summary of your issue, e.g., "Missing Centrality Calibration File for Rivet Analysis".
       - **Description**: Include the error message you received and any additional information that might be useful, such as the commands you used and any relevant configuration files.
       - **Steps to Reproduce**: If possible, provide detailed steps to reproduce the issue.
       - **Additional Information**: Mention that you are using the official ALICE centrality Rivet implementation and that you need guidance on generating the calibration file.
    
    5. **Attach Relevant Files**: If you have any configuration files or commands that you used, consider attaching them to the ticket.
    
    6. **Submit the Ticket**: Once you have filled out all the necessary details, submit the ticket.
    
    By following these steps, you will ensure that the issue is properly documented and can be addressed by the relevant team members. If you need more guidance or have any questions, feel free to ask!
    
    ---
    
    _Help us improve the askALICE chatbot by providing your feedback. React to this message with 👍 if the answer was helpful or 👎 if it was not._


D:  7. 8. 2025
Q:  I'm working on injected resonances (L1520) and getting a good number of generated particles, but the reconstruction efficiency is only around 2%. I wanted to test with TGeant3 to see how it performs, but if it's no longer tested, there's no strong reason for me to pursue it further. 
    Also, is there a way to provide configuration to TGeant4, or does it handle everything automatically?

A:  TGeant4 is the default engine in o2-sim, and you can use TGeant3 by specifying the `-e TGeant3` option when running the `o2-sim` executable. However, there is no mention in the provided context that TGeant3 is no longer tested. Therefore, if you want to test TGeant3, you can proceed with it.

    Regarding configuration, you can provide specific settings for TGeant4 by using the `G4` parameter, which influences the Geant4 engine, such as the physics list. For example, you can set the physics list to "G4.physicsmode=kFTFP_BERT_optical_biasing". If you need to test TGeant3, you can do so by running the command `o2-sim -n 10 -g pythia8pp --noGeant -e TGeant3`, which will use TGeant3 for the particle transport while skipping Geant4.
    
    **Sources:**
    1. https://github.com/AliceO2Group/simulation/blob/main/docs/transport/geometry.md
    2. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo_Transcript.md
    3. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_Nov2024/MCTutorial4Giacalone.pdf
    4. https://github.com/ta5946/alice-rag/blob/master/data/knowledge_base/ALICE-simulation-tutorial.pptx-1.pdf
    5. https://github.com/AliceO2Group/simulation/blob/main/docs/transport/README.md
    6. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo_Transcript.md
    7. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo.pdf
    8. https://github.com/AliceO2Group/O2DPG/blob/master/DATA/aliecs_documentation/README.md
    9. https://github.com/AliceO2Group/AliceO2/blob/dev/run/SimExamples/TParticle/README.md
    10. https://github.com/AliceO2Group/simulation/blob/main/additional_resources/talks/O2_AnalysisTutorial_April2023/ALICE-Run3-MC-HowTo.pdf
    
    ---
    
    _Help us improve the askALICE chatbot by providing your feedback. React to this message with 👍 if the answer was helpful or 👎 if it was not._
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
![Average response time comparison](/img/plots/1_sample/qwen_judge/time_comparison.png)

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

#### Update:
We repeated the evaluation with some **larger models** (external, served on the AMD machine) and plotted **heatmaps**.
The correlations between more capable models and Gemini API are higher, but nothing stands out.

_We should use one or a few external models as judges, for example Qwen3-30B-A3B-Instruct or Gemma-3-27b-it._

- Pearson correlations:
![Person correlation heatmap](/img/plots/correlations/pearson_correlation_heatmap.png)

- Spearman correlations:
![Spearman correlation heatmap](/img/plots/correlations/spearman_correlation_heatmap.png)

- Root mean squared errors (RMSE):
![Root mean squared error heatmap](/img/plots/correlations/rmse_heatmap.png)

### Second evaluation

For the second iteration of chatbot evaluation we sampled `n = 5` answers and used Gemma-2-9b-it as judge.
The plots contain an error bar of +- 1 standard deviation calculated as mean standard deviation across all questions (per metric).
We also defined low, medium and high recall RAG configurations to observe the performance to response time trade-off.

1. ROUGE-L score comparison:
![ROUGE-L score comparison](/img/plots/5_sample/gemma_judge/rouge_l_score_comparison.png)

2. Semantic similarity comparison:
![Semantic similarity comparison](/img/plots/5_sample/gemma_judge/semantic_similarity_comparison.png)

3. Gemma-as-judge comparison:
![Gemma-as-Judge comparison](/img/plots/5_sample/gemma_judge/llm_judge_score_comparison.png)

4. Average response time comparison:
![Average_response time comparison](/img/plots/5_sample/gemma_judge/time_comparison.png)


### Third evaluation

In this iteration we tried to expand the training dataset by generating artificial / **synthetic data**:
- Question and answer pairs for each existing document,
- Or paraphrased version of each existing document.

Both strategies **doubled** our training data from 3000 chunks to almost 6000 chunks, but did not improve results (answer correctness metrics).
![Gemma-as-Judge comparison](/img/plots/synthetic/gemma_judge/llm_judge_score_comparison.png)

We also tested larger embedder (`BAAI/bge-m3`) and reranker (`BAAI/bge-reranker-v2-m3`), which were slower and degraded results.
For example see this [debug question](/eval/answers/embeddings/info.txt). 
_We should repeat that in the final evaluation with._

### Final evaluation

#### Plan:
- Construct a larger expert labeled dataset,
- Use smaller embeddings for now,
- Evaluate base GEMINI, OLD_QWEN,
- Evaluate all external models with and without RAG,
- Use QWEN and GEMMA as judges,
- Select the best performing model,
- Try to upscale embeddings,
- Try to include analysis documentation,
- Try to include synthetic data,


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

Below is a minimal prototype of anchoredMC simulation script described here: https://aliceo2group.github.io/simulation/docs/o2dpgworkflow/anchored.html.
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

| Variable                       | Type     | Default | Values                        | Description                                                                                                          |
|--------------------------------|----------|---------|-------------------------------|----------------------------------------------------------------------------------------------------------------------|
| **REQUIRED VARIABLES**         |
| `ALIEN_JDL_LPMRUNNUMBER`       | Required | -       | Positive integer              | The ALICE run number to which this MC job anchors, defining the experimental conditions and detector setup           |
| `ALIEN_JDL_LPMANCHORPASSNAME`  | Required | -       | Any string                    | The reconstruction pass/cycle identifier (for example "apass4") that determines which reconstruction settings to use |
| `ALIEN_JDL_LPMINTERACTIONTYPE` | Required | -       | ["pp", "Pb-Pb"]               | The collision system type, either proton-proton (pp) or lead-lead (Pb-Pb) interactions                               |
| `SPLITID`                      | Required | -       | Positive integer <= 100       | Identifies which temporal split within the run to simulate, corresponding to specific timestamps                     |
| `NTIMEFRAMES`                  | Required | -       | Positive integer              | Number of consecutive timeframes to generate for this MC job, defining the data volume                               |
| **OPTIONAL VARIABLES**         |
| `ALIEN_JDL_CPULIMIT`           | Optional | 8       | Positive integer              | Expected CPU time limit in hours that the workflow runner will assume for resource allocation                        |
| `ALIEN_JDL_SIMENGINE`          | Optional | TGeant4 | ["TGeant3", "TGeant4", "VMC"] | Monte Carlo particle transport engine used for simulating detector interactions                                      |
| `ALIEN_JDL_ANCHOR_SIM_OPTIONS` | Optional | ""      | String flags                  | Additional simulation parameters and event generator configuration (for example "-gen pythia8pp")                    |
| `NSIGEVENTS`                   | Optional | 10000   | Positive integer              | Maximum number of signal events per timeframe, actual count may be lower based on interaction rates                  |
| `CYCLE`                        | Optional | 0       | Non-negative integer          | Cycle number within the production to simulate, allowing multiple iterations over the same time period               |

This subset covers the core anchoring parameters, job splitting configuration, and key customization options that would be most relevant for a demonstration.
The goal is to design a chatbot state that can generate such scripts in a multi-turn conversation with the user.
One technique to achieve this is slot filling. Example workflow:
```text
Step 1: User says “Run it with fast mode.”
Step 2: LLM infers B = fast, A = ?
Step 3: LLM asks “Which environment would you like to run in? (e.g., production, staging)”
Step 4: User replies “Production.”
Step 5: LLM returns final:
```

### Script evaluation

The evaluation process works in 3 steps, from low to high level checking:
1. The **required variables** are collected from the generated script (static analysis). The missing optional variables are set to default values.
2. The environment **variable values** are checked against the expected values (static validation).
3. The mock `anchoredMC.sh` **script is run**. The parameters have to be set correctly (just like real simulation) and the script has to run without errors (dynamic validation).

## Commit summarization

### Commit messages

Another use case of our LLM server is to use it for **automatic changelog generation** as part of the GitHub workflow.
To test this functionality we scraped commits from the [AliceO2 repository](https://github.com/AliceO2Group/AliceO2) and grouped them by weeks.
This is done in `scrape_commits.sh` script.
Example commit history to be summarized:
```json
{
  "start_date": "2025-06-23",
  "end_date": "2025-06-29",
  "commit_history": [
    {
      "message": "o2-sim: Fix for merger exit status analysis",
      "author": "swenzel"
    },
    {
      "message": "Fix vertex copying for last timeframe in collisioncontext",
      "author": "swenzel"
    },
    {
      "message": "Bump actions/checkout from 3 to 4",
      "author": "dependabot[bot]"
    },
    {
      "message": "Bump actions/stale from 1 to 9",
      "author": "dependabot[bot]"
    },
    {
      "message": "Bump actions/setup-python from 2 to 5 (#14299)",
      "author": "dependabot[bot]"
    },
    {
      "message": "Replace type name hash with a different string hash in preparation for string-based expressions (#14398)",
      "author": "Anton Alkin"
    },
    {
      "message": "DPL: avoid unintialised member (#14449)",
      "author": "Giulio Eulisse"
    },
    {
      "message": "A3: Add sensitive RICH layers to geometry (#14450)",
      "author": "Nicol\u00f2 Jacazio"
    },
    {
      "message": "jobutils: Sanitize return code treatment",
      "author": "swenzel"
    },
    {
      "message": "DPL: improve logs for new calibration scheme (#14030)",
      "author": "Giulio Eulisse"
    },
    {
      "message": "DPL Analysis: add `DefinesDelayed`",
      "author": "Anton Alkin"
    },
    {
      "message": "ITS: GPU add missing output to GPUWorkflowSpec",
      "author": "Felix Schlepper"
    },
    {
      "message": "ITS: cleanup unused GPU code",
      "author": "Felix Schlepper"
    },
    {
      "message": "Using only propagateMcLabels",
      "author": "Christian Sonnabend"
    },
    {
      "message": "Cleanup + handling of deconvolution",
      "author": "Christian Sonnabend"
    },
    {
      "message": "Fix for cluster flags",
      "author": "Christian Sonnabend"
    },
    {
      "message": "GPU/TPCClusterFinder: Fix out-of-bounds write.",
      "author": "Felix Weiglhofer"
    },
    {
      "message": "Move bulk of the code to cxx to not expose extra headers",
      "author": "shahoian"
    },
    {
      "message": "ITS: redefine seeding vertex label",
      "author": "Felix Schlepper"
    },
    {
      "message": "Avoid missing dictionary (#14443)",
      "author": "Giulio Eulisse"
    },
    {
      "message": "IWYU: BinningPolicy.h (#14323)",
      "author": "V\u00edt Ku\u010dera"
    },
    {
      "message": "Fix using namespace arrow, arrow::io (#14442)",
      "author": "Giulio Eulisse"
    },
    {
      "message": "DPL: make sure Lifetime::Sporadic is kept (#14434)",
      "author": "Giulio Eulisse"
    },
    {
      "message": "ITS: GPU report found neighbours (#14438)",
      "author": "Felix Schlepper"
    },
    {
      "message": "ITS3: move the energy deposition wrt. centre of response (#14415)",
      "author": "Chunzheng Wang"
    },
    {
      "message": "DigiContext: Bugfix for start of history effect",
      "author": "swenzel"
    },
    {
      "message": "DPL: enable new EoS by default and set data processing and exit transition timeouts (#14429)",
      "author": "ehellbar"
    },
    {
      "message": "ITS: GPU add needed synchronization (#14439)",
      "author": "Felix Schlepper"
    },
    {
      "message": "EPNstderrMonitor: remove static declaration of InfoLoggerMessageOption when sending messages to IL",
      "author": "Ernst Hellbar"
    },
    {
      "message": "ITS3: fix tracking after refactor (#14433)",
      "author": "Felix Schlepper"
    }
  ]
}
```

### Changelog generation

In `generate_changelogs.py` file we demonstrated requesting the LLM server with the `curl` command.
We use the _system prompt for prompt engineering_ and the user prompt to provide the commit history (between 2 dates or tags).
Current changelog generator prompt is:
```text
You are a changelog / release notes generator.
You are provided with a list of commit messages and their authors.
Your task is to summarize the commits and generate a short changelog like:

## What's Changed
- FST: Fix running TPC at P2 online without GPUs by @davidrohr
- ITS Calibration: always reset chipDone counter independently on hits by @iravasen in #13386
- Simplify builder holders by @ktf
- Add support for bitmap in ROFRecords by @mconcas in #13385
- Avoid doing one iteration when the tree has no entries by @ktf

Try to group together similar commits and changes from the same author.
The final list should contain 5 to 10 items.
Return only the generated changelog in markdown format and nothing else.
```

Example of a generated changelog:

---
## What's Changed
- o2-sim: Fix for merger exit status analysis by @swenzel
- Fix vertex copying for last timeframe in collisioncontext by @swenzel
- Sanitize return code treatment in jobutils by @swenzel
- Avoid unintialised member in DPL by @Giulio Eulisse
- Improve logs for new calibration scheme in DPL by @Giulio Eulisse
- Add `DefinesDelayed` to DPL Analysis by @Anton Alkin
- Fix out-of-bounds write in GPU/TPCClusterFinder by @Felix Weiglhofer
- Redefine seeding vertex label in ITS by @Felix Schlepper
- Add needed synchronization in ITS by @Felix Schlepper
- Fix using namespace arrow, arrow::io by @Giulio Eulisse
- Enable new EoS by default and set data processing and exit transition timeouts in DPL by @ehellbar
---


## Future work

### Knowledge base
- _Scrape Jira issues from O2 (filters general, production request)_
- _Cluster Mattermost questions by similarity / topic_

### Question answering
- Repeat chatbot evaluation (Mistral and other models)
- Configure LLM and RAG in Mattermost with prefix like `#deepseek` or `/llm_deepseek`
