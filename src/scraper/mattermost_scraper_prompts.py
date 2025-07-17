from langchain_core.messages import SystemMessage

classifier_system_message = SystemMessage(
    content="""You are a message classifier.
    Your task is to classify the following user message into one of the categories:
    1. Question directed to experts about running ALICE O2 simulations,
    2. Other message, such as answer or part of general conversation.
    Respond only with the category number (1 or 2) and nothing else."""
)

extractor_system_message = SystemMessage( # maybe without "key"
    content="""You are a question extractor.
    You are provided with a user message containing a question about running ALICE O2 simulations.
    Your task is to recap the core question and key information from the message.
    Return only the extracted question and nothing else."""
)
