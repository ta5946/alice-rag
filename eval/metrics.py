import re
from rouge_score import rouge_scorer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate
from src.chatbot.langchain_components import LLM, EMBEDDINGS


def rouge_score(generated_answer, correct_answer):
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    rouge_scores = scorer.score(correct_answer, generated_answer)
    rouge_l_score = rouge_scores['rougeL'].fmeasure # TODO try other rouge types
    return rouge_l_score

def semantic_similarity_score(generated_answer, correct_answer):
    embeddings = EMBEDDINGS.embed_documents([generated_answer, correct_answer])
    similarity_scores = cosine_similarity([embeddings[0]], [embeddings[1]])
    return float(similarity_scores[0][0])

def llm_judge_score(question, generated_answer, correct_answer):
    llm_judge_system_prompt = SystemMessage(
        content="""You are a chatbot response evaluator.
        You are provided with a question, correct answer and a chatbot generated answer.
        Your task is to rate the correctness of the generated answer on a scale of 1 to 5.
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

    assistant_message = LLM.invoke(messages)
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

    print(rouge_score(generated_answers[0], correct_answer)) # 0.6666666666666666
    print(rouge_score(generated_answers[1], correct_answer)) # 0.16666666666666666
    print(semantic_similarity_score(generated_answers[0], correct_answer)) # 0.9729812727756343
    print(semantic_similarity_score(generated_answers[1], correct_answer)) # 0.6108495799294349
    print(llm_judge_score(question, generated_answers[0], correct_answer)) # 5
    print(llm_judge_score(question, generated_answers[1], correct_answer)) # 1
