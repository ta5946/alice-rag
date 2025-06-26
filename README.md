## ALICE chatbot

A set of prototype scripts for hosting a minimal RAG chatbot for ALICE, more specifically the O2 simulation documentation.


## Repository structure:

- `data`: Static documents about O2 simulation used for RAG testing purposes.
- `doc`: More project documentation.
- `indexer`: Contains scripts to put document resources (specified in a yml) into a Chroma vector database using some (free) text embedding model.
- `mattermost_interact`: A mattermost chatbot implementation talking to Chroma and a local LLM.
- `models`: This directory will be created to store the downloaded HuggingFace models.
- `src`: Main executable files (to be merged with `indexer` and `mattermost_interact`).
- `tests` Short scripts for testing the functionality of individual components, such as LLM and embedding models.
- `.env.example`: Configurable environment to be copied into `.env` and modified for local use.
- `docker-compose.yml`: Docker compose file to run the LLM server (and other services) as a container.

Project outline and goals are available at: https://codimd.web.cern.ch/JgVlNcgvTjC38GURvriLhA.
