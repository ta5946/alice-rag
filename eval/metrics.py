import re
import time
import evaluate
from sklearn.metrics.pairwise import cosine_similarity
import eval.llm_judge_prompts as prompts
from src.chatbot.langchain_components import LLM, EMBEDDINGS


def bleu_score(correct_answer, generated_answer):
    evaluator = evaluate.load("bleu")
    bleu_scores = evaluator.compute(predictions=[generated_answer], references=[[correct_answer]])
    return bleu_scores["bleu"]

def rouge_score(correct_answer, generated_answer, rouge_type="rougeL"):
    evaluator = evaluate.load("rouge")
    rouge_scores = evaluator.compute(predictions=[generated_answer], references=[correct_answer])
    return float(rouge_scores[rouge_type])

def semantic_similarity_score(correct_answer, generated_answer):
    embeddings = EMBEDDINGS.embed_documents([generated_answer, correct_answer])
    similarity_scores = cosine_similarity([embeddings[0]], [embeddings[1]])
    return float(similarity_scores[0][0])

def llm_judge_score(question, correct_answer, generated_answer, llm=LLM, timeout=0):
    time.sleep(timeout) # rate limit workaround

    user_message = prompts.llm_judge_prompt_template.format(question=question, correct_answer=correct_answer, generated_answer=generated_answer)
    messages = [prompts.llm_judge_system_prompt, user_message]

    llm.temperature = 0.0 # deterministic inference
    llm.top_p = 1.0
    assistant_message = llm.invoke(messages)
    assistant_text = str(assistant_message.content)
    assistant_text = assistant_text.split("</think>", 1)[1] if "</think>" in assistant_text else assistant_text # parse reasoning content
    assistant_text = assistant_text.strip() # remove whitespace
    print(assistant_text)
    correctness_scores = re.findall(r"[1-5]", assistant_text)
    if len(correctness_scores) >= 1:
        return int(correctness_scores[0])
    else:
        raise ValueError("Invalid correctness score:", assistant_text)


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
