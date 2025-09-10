# AskALICE chatbot developer notes

_10. 9. 2025_


## Project requirements

### Software

To run this chatbot application we need:
- A host machine with **Ubuntu 24.04 LTS** and **Python 3.12** installed,
- Libraries defined in the `requirements.txt` file, easiest installed in a virtual environment,
- Docker images identified by digests/hashes in the `langfuse/images.txt` file,
- An LLM available through an **API endpoint** (either local or remote).

### Hardware

To run the current medium sized LLMs we need a GPU on some external machine with at least **32 GB of VRAM**, preferably either NVIDIA or AMD.
The chatbot project, including the embedding and reranking models which are part of the code requires at least 8 GB of VRAM on the host.

If encountering Out of Memory (**OOM**) errors, try reducing the batch size, precision or using lighter models.


## Current setup / state

### Brief

| Machine                              | Location                                   | Service                                  | In case of error                      |
|--------------------------------------|--------------------------------------------|------------------------------------------|---------------------------------------|
| **pc-alice-ph01**                    | /home/tajdovec/langfuse/docker-compose.yml | LangFuse container                       | Restart container                     |
| pc-alice-ph01                        | /home/tajdovec/rag/docker-compose.yml      | Open WebUI container                     | Restart container                     |
| pc-alice-ph01                        | /home/tajdovec/rag/run.py                  | AskALICE chatbot                         | Run script again                      |
| **alihlt-gw-prod.cern.ch -> epn320** | None, use the predefined ssh commands      | llama.cpp containers and port forwarding | Kill services, execute commands again |

### LangFuse (tracing) server

The LangFuse server is run as a Docker container on the host machine `tajdovec@pc-alice-ph01` from `/home/tajdovec/langfuse` with:
```bash
docker compose up
```

The whole directory was cloned from the LangFuse GitHub repository as described here: https://langfuse.com/self-hosting/deployment/docker-compose

Server can be configured by changing the variables in `docker-compose.yml`.
It is available at the default port: http://pc-alice-ph01:3000.

User accounts, projects and organizations can be created through the web interface. In case of error just restart the Docker container.

Project home:
![LangFuse project home](/img/ss/langfuse.png)

Tracing setup:
- Sign up as a new user
- Create a new organization
- Create a new project
- Use the API key in the chatbot environment (described later)

### llama.cpp LLM server

To serve LLMs we are using `alihlt-gw-prod.cern.ch`, more specifically `epn320`.
To connect to the HPC machine, start the llama.cpp server (with a specific LLM) and forward the port:
```bash
# smaller qwen
ssh -f -L 0.0.0.0:8090:127.0.0.1:8090 -J tajdovec@alihlt-gw-prod.cern.ch:2020 tajdovec@epn320 "HIP_VISIBLE_DEVICES=0 llama.cpp/build/bin/llama-server --hf-repo unsloth/gpt-oss-20b-GGUF:Q8_0 --alias gpt-oss-20b --n-gpu-layers 1000 --ctx-size 32000 --n-predict 4000 --jinja --port 8090"
# larger qwen
ssh -f -L 0.0.0.0:8091:127.0.0.1:8091 -J tajdovec@alihlt-gw-prod.cern.ch:2020 tajdovec@epn320 "HIP_VISIBLE_DEVICES=1 llama.cpp/build/bin/llama-server --hf-repo unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF:Q6_K --alias Qwen3-30B-A3B-Instruct-2507 --n-gpu-layers 1000 --ctx-size 32000 --n-predict 4000 --jinja --port 8091"
# etc
```

API keys are not set (can be "any" or "empty"). For more details about llama.cpp build instructions refer to: https://github.com/ggml-org/llama.cpp

We can connect to epn320 and inspect the GPU utilization with rocm-smi:
```bash
ssh tajdovec@alihlt-gw-prod.cern.ch -p 2020
ssh epn320
rocm-smi
```

Output:
```text
========================================= ROCm System Management Interface =========================================
=================================================== Concise Info ===================================================
Device  Node  IDs              Temp    Power  Partitions          SCLK     MCLK     Fan  Perf  PwrCap  VRAM%  GPU%  
              (DID,     GUID)  (Edge)  (Avg)  (Mem, Compute, ID)                                                    
====================================================================================================================
0       4     0x738c,   4106   44.0°C  55.0W  N/A, N/A, 0         1502Mhz  1200Mhz  0%   high  290.0W  97%    0%    
1       5     0x738c,   2833   45.0°C  56.0W  N/A, N/A, 0         1502Mhz  1200Mhz  0%   high  290.0W  89%    0%    
2       3     0x738c,   57403  44.0°C  55.0W  N/A, N/A, 0         1502Mhz  1200Mhz  0%   high  290.0W  96%    0%    
3       2     0x738c,   14370  43.0°C  61.0W  N/A, N/A, 0         1502Mhz  1200Mhz  0%   high  290.0W  61%    0%    
4       8     0x738c,   45163  44.0°C  56.0W  N/A, N/A, 0         1502Mhz  1200Mhz  0%   high  290.0W  40%    0%    
5       9     0x738c,   26738  42.0°C  56.0W  N/A, N/A, 0         1502Mhz  1200Mhz  0%   high  290.0W  0%     0%    
6       7     0x738c,   16474  43.0°C  56.0W  N/A, N/A, 0         1502Mhz  1200Mhz  0%   high  290.0W  31%    0%    
7       6     0x738c,   38979  42.0°C  50.0W  N/A, N/A, 0         1502Mhz  1200Mhz  0%   high  290.0W  91%    0%    
====================================================================================================================
=============================================== End of ROCm SMI Log ================================================
```

We are serving **7 models**, exposed on ports http://pc-alice-ph01:8090 to http://pc-alice-ph01:8096.

To check the current running services:
```bash
 ps aux | grep tajdovec
```

```text
tajdovec 2084916  0.0  0.0  21904 10752 ?        Ss   Aug18   0:00 /usr/lib/systemd/systemd --user
tajdovec 2084917  0.0  0.0 193788  4776 ?        S    Aug18   0:00 (sd-pam)
tajdovec 2090741  0.0  0.0   5888  1536 ?        Ss   Aug18   0:00 tmux new -s llm
tajdovec 2090742  0.0  0.0  17756  3072 pts/2    Ss+  Aug18   0:00 -bash
root     2200988  0.0  0.0  40624  7680 ?        Ss   Aug19   0:00 sshd: tajdovec [priv]
root     2200991  0.0  0.0  40624  7680 ?        Ss   Aug19   0:00 sshd: tajdovec [priv]
root     2200993  0.0  0.0  40624  7680 ?        Ss   Aug19   0:00 sshd: tajdovec [priv]
root     2200995  0.0  0.0  40624  7680 ?        Ss   Aug19   0:00 sshd: tajdovec [priv]
root     2200997  0.0  0.0  40624  7680 ?        Ss   Aug19   0:00 sshd: tajdovec [priv]
tajdovec 2201007  0.0  0.0  41504  6232 ?        S    Aug19   0:03 sshd: tajdovec@notty
tajdovec 2201019  1.3  0.2 71939320 2114796 ?    Ssl  Aug19 418:53 llama.cpp/build/bin/llama-server --hf-repo unsloth/gpt-oss-20b-GGUF:Q8_0 --alias gpt-oss-20b --n-gpu-layers 1000 --ctx-size 32000 --n-predict 4000 --jinja --port 8090
tajdovec 2201248  0.0  0.0  40756  4704 ?        S    Aug19   0:19 sshd: tajdovec@notty
tajdovec 2201249  2.4  0.1 83403456 2056064 ?    Ssl  Aug19 762:09 llama.cpp/build/bin/llama-server --hf-repo unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF:Q6_K --alias Qwen3-30B-A3B-Instruct-2507 --n-gpu-layers 1000 --ctx-size 32000 --n-predict 4000 --jinja --port 8091
tajdovec 2201479  0.0  0.0  40756  4796 ?        S    Aug19   0:02 sshd: tajdovec@notty
tajdovec 2201480  0.4  0.1 83740792 1712800 ?    Ssl  Aug19 139:05 llama.cpp/build/bin/llama-server --hf-repo unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF:Q8_0 --alias Mistral-Small-3.2-24B-Instruct-2506 --n-gpu-layers 1000 --ctx-size 32000 --n-predict 4000 --jinja --port 8092
tajdovec 2201518  0.0  0.0  40760  4760 ?        S    Aug19   0:01 sshd: tajdovec@notty
tajdovec 2201520  2.1  0.3 82449528 3458700 ?    Ssl  Aug19 695:30 llama.cpp/build/bin/llama-server --hf-repo unsloth/gemma-3-27b-it-GGUF:Q6_K --alias gemma-3-27b-it --n-gpu-layers 1000 --ctx-size 32000 --n-predict 4000 --jinja --port 8093
tajdovec 2201754  0.0  0.0  40756  4804 ?        S    Aug19   0:03 sshd: tajdovec@notty
tajdovec 2201775  3.4  0.1 81614336 1677428 ?    Ssl  Aug19 1088:52 llama.cpp/build/bin/llama-server --hf-repo unsloth/DeepSeek-R1-Distill-Qwen-32B-GGUF:Q4_K_M --alias DeepSeek-R1-Distill-Qwen-32B --n-gpu-layers 1000 --ctx-size 32000 --n-predict 4000 --jinja --port 8094
root     2284073  0.0  0.0  40624  7680 ?        Ss   Aug20   0:00 sshd: tajdovec [priv]
tajdovec 2284083  0.0  0.0  40764  4720 ?        S    Aug20   0:05 sshd: tajdovec@notty
tajdovec 2284084  0.3  0.1 61072140 1376496 ?    Ssl  Aug20 103:41 llama.cpp/build/bin/llama-server --hf-repo MaziyarPanahi/Qwen2.5-7B-Instruct-GGUF:Q6_K --alias Qwen2.5-7B-Instruct --n-gpu-layers 1000 --ctx-size 32000 --n-predict 4000 --jinja --port 8095
root     2284666  0.0  0.0  40624  7680 ?        Ss   Aug20   0:00 sshd: tajdovec [priv]
tajdovec 2284672  0.0  0.0  40976  4804 ?        S    Aug20   0:00 sshd: tajdovec@notty
tajdovec 2284673  0.0  0.1 57631648 2065484 ?    Ssl  Aug20  27:33 llama.cpp/build/bin/llama-server --hf-repo bartowski/gemma-2-9b-it-GGUF:Q4_K_M --alias gemma-2-9b-it --n-gpu-layers 1000 --ctx-size 32000 --n-predict 4000 --jinja --port 8096
root     4130748  0.0  0.0  40624  7680 ?        Ss   14:36   0:00 sshd: tajdovec [priv]
tajdovec 4130755  0.0  0.0  40624  4768 ?        S    14:36   0:00 sshd: tajdovec@pts/0
tajdovec 4130756  0.0  0.0  17768  3072 pts/0    Ss   14:36   0:00 -bash
tajdovec 4135511  0.0  0.0  19192  3072 pts/0    R+   15:56   0:00 ps aux
tajdovec 4135512  0.0  0.0   6408  1536 pts/0    S+   15:56   0:00 grep --color=auto tajdovec
```

### Open WebUI interface

Can be initialized on the host machine `tajdovec@pc-alice-ph01` from `/home/tajdovec/rag` with:
```bash
docker compose up
```

It is available at http://pc-alice-ph01:8081 and unifies all base LLMs (without document knowledge or RAG!). No authentication is required.
This UI is just set up for preliminary testing the models.

User interface:
![Open WebUI user interface](/img/ss/open_webui.png)

### AskALICE chatbot

Everything in this section is run on the host machine `tajdovec@pc-alice-ph01` from `/home/tajdovec/rag`.

First we have to create a `.env` file from the provided `.env.example` template and fill in the required variables.
- LANGFUSE_SECRET_KEY
- LLM_API_KEY
- MATTERMOST_TOKEN
- GEMINI_API_KEY

After that the vector database can be built with:
```bash
python src/data_indexer/index.py
# destination directory is data/chroma but can be changed in the environment
```

And the chatbot can be started with:
```bash
python run.py
```

This starts the Mattermost listener that handles direct messages from real users. Logs are available in the `logs/chatbot.log` file.

All scripts should be run from the project **root directory**!
Besides that, my user `.profile` contains:
```bash
# activate virtual environment
source ~/.virtualenvs/alice-rag/bin/activate

# navigate to project directory
cd ~/rag

# set python path
export PYTHONPATH="~/rag:$PYTHONPATH"
export CUDA_VISIBLE_DEVICES=0

To check the GPU utilization and running processes:
```bash
nvidia-smi
ps aux | grep python
```

Output should look like:
```text 
Wed Sep 10 16:25:48 2025       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 575.57.08              Driver Version: 575.57.08      CUDA Version: 12.9     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 2080        On  |   00000000:01:00.0 Off |                  N/A |
| 27%   37C    P8             20W /  225W |    4720MiB /   8192MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
                                                                                         
+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A            2271      G   /usr/lib/xorg/Xorg                      105MiB |
|    0   N/A  N/A            2534      G   /usr/bin/gnome-shell                      9MiB |
|    0   N/A  N/A            8514      C   python                                 4600MiB |
+-----------------------------------------------------------------------------------------+

root        1190  0.0  0.0  34904  6636 ?        Ss   Jun27   0:00 /usr/bin/python3 /usr/bin/networkd-dispatcher --run-startup-triggers
root        2177  0.0  0.0 112264  8052 ?        Ssl  Jun27   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
tajdovec    8514  1.0  6.0 21612272 1957320 ?    Ssl  16:02   0:14 python src/chatbot/mattermost_listener.py
tajdovec   72551  0.0  0.0   9144  2236 pts/6    S+   16:25   0:00 grep --color=auto python
root     1591843  0.2  3.3 10005204 1100108 ?    Ssl  Sep03  23:43 /usr/local/bin/python3 -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8081 --forwarded-allow-ips * --workers 1
```

> Note that the chatbot was never tested with multiple users at the same time so this may introduce some issues.


## Key files and directories

Below is a brief description of the most important files and directories in this project. Also take a look at the utilities and dependent files!

| File                                         | Description                                                |
|----------------------------------------------|------------------------------------------------------------|
| `run.py`                                     | Main script to run the chatbot service                     |
| `.env.example`                               | Example environment variables to be configured.            |
| `logs/chatbot.log`                           | Chatbot logs.                                              |
| `src/data_indexer/index.py`                  | Script to create or update the vector database             |
| `src/data_indexer/knowledge_base.yml`        | Definition of GitHub repositories and file types.          |
| `src/chatbot/basic_rag_qa.py`                | Simulation and analysis RAG pipeline implementation.       |
| `src/chatbot/langchain_components.py`        | Generic LangChain components.                              |
| `src/chatbot/simulation_chatbot_prompts.py`  | Simulation, analysis and anchoredMC LLM prompts.           |
| `src/chatbot/mattermost_listener.py`         | Service that handles Mattermost messages.                  |
| `eval/datasets/final_expert_qa_dataset.json` | Final expert evaluation dataset (35 question-answer pairs) |
| `data/knowledge_base`                        | Files that are also included in the current knowledge base |

### How to change or add another LLM?

Create a new ChatOpenAI object in `langchain_components.py` like:
```python
QWEN = ChatOpenAI(
    model="Qwen3-30B-A3B-Instruct-2507",
    base_url="http://pc-alice-ph01:8091",
    api_key="any"
)
```

And then define it in `basic_rag_qa.py` in VALID_PARAMS["model"].

### How to change the embeddings?

Change these environment variables in `.env` to use different embeddings:
- HF_EMBEDDINGS_REPO,
- HF_RERANKER_REPO,
- CHROMA_THRESHOLD (optional)

And these to not mix different vector databases:
- CHROMA_COLLECTION_NAME,
- INDEXER_HASHES_FILE,
- INDEXER_DATA_DIR

### How to change other RAG parameters?

To change retrieval parameters create a database configuration object in `langchain_components.py` like:
```python
LOW_DB_CONFIG = {
    "db": DB,
    "name": "low recall",
    "top_k": 25,
    "top_n": 5,
    "similarity_threshold": 0.5
}
```

And use it in `basic_rag_qa.py` in VALID_PARAMS["db_config"].


_If something does not work as expected, always feel free to contact me [tjas.ajdovec@gmail.com](mailto:tjas.ajdovec@gmail.com)_
