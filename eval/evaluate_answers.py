import os
import json
from tqdm import tqdm
from eval.metrics import *


# evaluation configuration
ANSWER_PATH = "eval/answers/rag_qwen_answers.json"
RESULTS_PATH = "eval/results/rag_qwen_results.json"

def calculate_results():
    # load answers
    with open(ANSWER_PATH, "r") as answer_file:
        qa_dataset = json.load(answer_file)

    # get metrics for each answer
    results = []
    for item in tqdm(qa_dataset, desc="Calculating metrics", unit="question"):
        item_scores = {
            "id": item["id"],
            "time": item["time"],
            "bleu_score": bleu_score(item["correct_answer"], item["generated_answer"]),
            "rouge_1_score": rouge_score(item["correct_answer"], item["generated_answer"], "rouge1"),
            "rouge_l_score": rouge_score(item["correct_answer"], item["generated_answer"]),
            "semantic_similarity": semantic_similarity_score(item["correct_answer"], item["generated_answer"]),
            "llm_judge_score": llm_judge_score(item["question"], item["correct_answer"], item["generated_answer"])
        }
        results.append(item_scores)

    # calculate average scores
    average_scores = {
        "id": "average",
        "time": sum(item["time"] for item in results) / len(results),
        "bleu_score": sum(item["bleu_score"] for item in results) / len(results),
        "rouge_1_score": sum(item["rouge_1_score"] for item in results) / len(results),
        "rouge_l_score": sum(item["rouge_l_score"] for item in results) / len(results),
        "semantic_similarity": sum(item["semantic_similarity"] for item in results) / len(results),
        "llm_judge_score": sum(item["llm_judge_score"] for item in results) / len(results)
    }
    results.append(average_scores)
    print(f"Average scores for {ANSWER_PATH}:\n{average_scores}")

    # save results
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    print(f"Saving results to {RESULTS_PATH}")
    with open(RESULTS_PATH, "w") as results_file:
        json.dump(results, results_file, indent=4)


if __name__ == "__main__":
    calculate_results()
