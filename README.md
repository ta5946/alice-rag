A set of prototype scripts for a minimal RAG chatbot for ALICE.

The structure is:
- `indexer`: Contains scripts to put document resources (specified in a yml) into a Chroma vector database using some (free) text embedding model.
- `mattermost_interact`: A mattermost chatbot implementation talking to Chroma and a local LLM.
 
