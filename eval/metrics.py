import re
import evaluate
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate
from src.chatbot.langchain_components import LLM, EMBEDDINGS


def bleu_score(correct_answer, generated_answer):
    evaluator = evaluate.load("bleu")
    bleu_scores = evaluator.compute(predictions=[generated_answer], references=[[correct_answer]])
    return bleu_scores["bleu"]

def rouge_score(correct_answer, generated_answer, rouge_type="rougeL"):
    evaluator = evaluate.load("rouge")
    rouge_scores = evaluator.compute(predictions=[generated_answer], references=[correct_answer])
    return float(rouge_scores[rouge_type]) # TODO try other rouge types

def semantic_similarity_score(correct_answer, generated_answer):
    embeddings = EMBEDDINGS.embed_documents([generated_answer, correct_answer])
    similarity_scores = cosine_similarity([embeddings[0]], [embeddings[1]])
    return float(similarity_scores[0][0])

def llm_judge_score(question, correct_answer, generated_answer):
    llm_judge_system_prompt = SystemMessage(
        content="""You are a chatbot response evaluator.
        You are provided with a question, correct answer and a chatbot generated answer.
        Your task is to grade the correctness of the generated answer on a scale of 1 to 5.
        Respond only with a correctness score and nothing else."""
    )
    user_text = PromptTemplate.from_template("""QUESTION:
    {question}
    
    CORRECT ANSWER:
    {correct_answer}
    
    GENERATED ANSWER:
    {generated_answer}""")
    user_message = user_text.format(question=question, correct_answer=correct_answer, generated_answer=generated_answer)
    messages = [llm_judge_system_prompt, user_message]

    assistant_message = LLM.invoke(messages, temperature=0)
    correctness_scores = re.findall(r"[1-5]", assistant_message.content)
    if len(correctness_scores) == 1:
        return int(correctness_scores[0])
    else:
        raise ValueError("Invalid correctness score:", assistant_message.content)


if __name__ == "__main__":
    question = "What is the capital of France?"
    correct_answer = "Paris is the capital of France."
    generated_answers = [
        "The capital of France is Paris.",
        "Geneva is not a French city."
    ]

    # print(bleu_score(correct_answer, generated_answers[0])) # 0.0
    # print(bleu_score(correct_answer, generated_answers[1])) # 0.0
    # print(rouge_score(correct_answer, generated_answers[0])) # 0.6666666666666666
    # print(rouge_score(correct_answer, generated_answers[1])) # 0.16666666666666666
    # print(semantic_similarity_score(correct_answer, generated_answers[0])) # 0.9729812727756343
    # print(semantic_similarity_score(correct_answer, generated_answers[1])) # 0.6108495799294349
    # print(llm_judge_score(question, correct_answer, generated_answers[0])) # 5
    # print(llm_judge_score(question, correct_answer, generated_answers[1])) # 1
