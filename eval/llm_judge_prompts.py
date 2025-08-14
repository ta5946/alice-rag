from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate

llm_judge_system_prompt = SystemMessage(
    content="""You are a chatbot response evaluator.
    You are provided with a question, correct answer and a chatbot generated answer.
    Your task is to grade the correctness of the generated answer on a scale of 1 to 5.
    Respond only with a correctness score and nothing else."""
)
llm_judge_prompt_template = PromptTemplate.from_template("""QUESTION:
{question}

CORRECT ANSWER:
{correct_answer}

GENERATED ANSWER:
{generated_answer}""")  # soft reasoning switch is \no_think
