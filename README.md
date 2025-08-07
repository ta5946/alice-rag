## ALICE chatbot

A set of prototype scripts for hosting a minimal RAG chatbot for ALICE, more specifically the O2 simulation documentation.


## Repository structure:

- `data`: Static documents about O2 simulation used for RAG testing purposes.
- `docs`: More project documentation and [technical notes](docs/technical_notes.md). Also contains research on different chatbot evaluation approaches.
- `eval`: Chatbot evaluation data, metrics and plots. Judge evaluation correlation metrics.
- `indexer`: Contains scripts to put document resources (specified in a yml) into a Chroma vector database using some (free) text embedding model.
- `mattermost_interact`: A mattermost chatbot implementation talking to Chroma and a local LLM.
- `img/plots`: Plots of chatbot evaluation results for different iterations.
- `models`: This directory will be created to store the downloaded HuggingFace models.
- `src`: Main executable files.
    - `chatbot`: RAG pipeline and chatbot interface.
    - `indexer`: Document indexing and vector store management.
    - `scraper`: Data scraping from external platforms, such as Mattermost and Jira.
    - `script_generation`: Examples and checkers for chatbot code generation feature (anchoredMC scripts).
- `tests` Short scripts for testing the functionality of individual components, such as LLM and embedding models.
- `.env.example`: Configurable environment to be copied into `.env` and modified for local use.
- `docker-compose.yml`: Docker compose file to run the LLM server (and other services) as a container.
- `run.py`: Starts the chatbot service and connects it to Mattermost.

Project outline and goals are available at: https://codimd.web.cern.ch/JgVlNcgvTjC38GURvriLhA.
