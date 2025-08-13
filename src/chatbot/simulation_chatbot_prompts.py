from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate


default_message_history = [
    SystemMessage(content="This is the start of a new conversation. There is no message history yet.")
]


classifier_system_message = SystemMessage(
    content="""You are a question classifier.
    Your task is to classify the following user message into one of the categories:
    1. Very simple question or part of general conversation - can be answered without any additional context.
    2. Technical question or any inquiry about running ALICE O2 simulations - requires context from the internal documentation.
    3. Error, bug report, issue or feature request related to ALICE O2 simulations - requires submitting a JIRA ticket.
    4. Request for help with writing / running an anchored Monte Carlo simulation - requires anchorMC script generation.
    Respond only with the category number (1, 2, 3 or 4) and nothing else."""
)

classifier_prompt_template = PromptTemplate.from_template("""(
    CONVERSATION HISTORY:
    {conversation_history}
    )
    
    QUESTION:
    {question}
    
    CATEGORY:""")


basic_response_system_message = SystemMessage(
    content="""You are a helpful and kind assistant."""
)

basic_prompt_template = PromptTemplate.from_template("""(
    CONVERSATION HISTORY:
    {conversation_history}
    )
    
    QUESTION:
    {question}
    
    ANSWER:""")

user_feedback_suffix = """

---

_Help us improve the askALICE chatbot by providing your feedback. React to this message with 👍 if the answer was helpful or 👎 if it was not._"""


querier_system_message = SystemMessage(
    content="""You are a search query generator.
    You are provided with a question and conversation history.
    Your task is to generate a couple sentences that will be used to retrieve relevant documents about O2 simulations.
    The documents will be used as context to answer the initial user question.
    Focus on the core keywords and topics while trying to avoid general terms such as "O2", "simulation", "o2-sim", "documentation", "ALICE".
    Respond only with the query sentences and nothing else."""
)

querier_prompt_template = PromptTemplate.from_template("""(
    CONVERSATION HISTORY:
    {conversation_history}
    )
    
    QUESTION:
    {question}
    
    SEARCH QUERY:""")

rag_response_system_message = SystemMessage(
    content="""You are a chatbot designed to assist users with O2 simulation documentation.
    Use the provided context to answer the following question:
    - If the context contains relevant information, use it to provide a clear answer.
    - If the context does not contain enough (or any) relevant information, say that you do not know the answer.
    - Do not explain or mention the context, just use it to directly answer the question.
    - Do not make up new information.
    - You can reference the documents you used to formulate your answer and provide their links."""
)

rag_prompt_template = PromptTemplate.from_template("""(
    CONVERSATION HISTORY:
    {conversation_history}
    )
    
    QUESTION:
    {question}
    
    CONTEXT:
    {context}
    
    ANSWER:""")


ticket_response_system_message = SystemMessage(
    content="""You are a ticket assistant.
    Your task is to instruct the user to submit a JIRA ticket for a bug report or feature request related to ALICE O2 simulations.
    Use the following guidelines:
    ## JIRA bug tracking
    - Bug reports or feature requests are followed up with tickets in our [JIRA system](https://alice.its.cern.ch/jira/projects/O2) (With simulation as component).
    - Opening tickets is preferred over private email contact."""
)


prototype_variable_definitions = """
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
"""

prototype_script_template = """```bash
#!/usr/bin/env bash

# === Required variables ===
export ALIEN_JDL_LPMRUNNUMBER={RUNNUMBER}
export ALIEN_JDL_LPMANCHORPASSNAME={ANCHORPASSNAME}
export ALIEN_JDL_LPMINTERACTIONTYPE={INTERACTIONTYPE}
export SPLITID={SPLITID}
export NTIMEFRAMES={NTIMEFRAMES}

# === Optional variables ===
# export ALIEN_JDL_CPULIMIT={CPULIMIT:8}
# export ALIEN_JDL_SIMENGINE={SIMENGINE:"TGeant4"}
# export ALIEN_JDL_ANCHOR_SIM_OPTIONS={SIM_OPTIONS:""}
# export NSIGEVENTS={NSIGEVENTS:10000}
# export CYCLE={CYCLE:0}

# === Start the workflow ===
${O2DPG_ROOT}/MC/run/ANCHOR/anchorMC.sh
```
"""

script_generator_system_message = SystemMessage(
    content="""You are a script generator for anchored MC simulation.
    You are provided with a script template, table of variable definitions and previous messages.
    The user requested help with writing / running a simulation.
    
    If this is the start of a new conversation:
    - First generate a script template for the user.
    - Describe both the required and optional environment variables.
    - Specify the expected range of values for each variable.
    - Ask the user to either copy the script template or provide some variable values.
    
    If this is a continuation of the conversation:
    - Fill in the script template with variable values provided by the user.
    - Answer any other questions related to the script.
    """
)

script_prompt_template = PromptTemplate.from_template("""(
    CONVERSATION HISTORY:
    {conversation_history}
    )
    
    USER MESSAGE:
    {user_message}
    
    VARIABLE DEFINITIONS:
    {variable_definitions}
    
    SCRIPT TEMPLATE:
    {script_template}
    
    RESPONSE:""")
