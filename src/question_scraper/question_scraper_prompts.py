from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate


classifier_system_message = SystemMessage(
    content="""You are a message classifier.
    Your task is to classify the following user message into one of the categories:
    1. Question about running ALICE O2 simulations that requires support from experts,
    2. Bug report or feature request related to ALICE O2 simulations,
    3. Other message, such as answer or part of general conversation.
    Respond only with the category number (1, 2 or 3) and nothing else."""
)

classifier_prompt_template = PromptTemplate.from_template("""POST:
    {post}

    CATEGORY:""")


extractor_system_message = SystemMessage(
    content="""You are a question extractor.
    You are provided with a user message that contains a question about running ALICE O2 simulations.
    Your task is to recap the core question and key information from the message.
    Return only the extracted question and nothing else."""
)

extractor_prompt_template = PromptTemplate.from_template("""POST:
    {post}
    
    QUESTION:""")
