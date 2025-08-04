import os
import json
import numpy as np
from tqdm import tqdm
from src.chatbot.langchain_components import LLM, GEMINI
from eval.metrics import *


# evaluation configuration
ANSWER_PATH = "eval/answers/5_sample/base_gemini_answers_2000.json"
RESULT_PATH = "eval/results/5_sample/gemma_judge/base_gemini_results_2000.json"
JUDGE = LLM
TIMEOUT = 0

def calculate_results(judge, timeout):
    # load answers
    with open(ANSWER_PATH, "r") as answer_file:
        qa_dataset = json.load(answer_file)

    # get metrics for each answer
    results = []
    for item in tqdm(qa_dataset, desc="Calculating metrics", unit="question"):
        item_scores = {
            "id": item["id"],
            "times": [],
            "bleu_scores": [],
            "rouge_1_scores": [],
            "rouge_l_scores": [],
            "semantic_similarities": [],
            "llm_judge_scores": []
        }

        for i, generated_answer in enumerate(item["generated_answers"]):
            if not generated_answer: # empty answer workaround
                continue

            try:
                judge_score = llm_judge_score(item["question"], item["correct_answer"], generated_answer, judge, timeout)
            except Exception as error:
                print("calculate_results():", error)
                judge_score = 1
            item_scores["times"].append(item["times"][i])
            item_scores["bleu_scores"].append(bleu_score(item["correct_answer"], generated_answer))
            item_scores["rouge_1_scores"].append(rouge_score(item["correct_answer"], generated_answer, "rouge1"))
            item_scores["rouge_l_scores"].append(rouge_score(item["correct_answer"], generated_answer, "rougeL"))
            item_scores["semantic_similarities"].append(semantic_similarity_score(item["correct_answer"], generated_answer))
            item_scores["llm_judge_scores"].append(judge_score)

        item_scores["mean_time"] = np.mean(item_scores["times"]) # sample mean
        item_scores["mean_bleu_score"] = np.mean(item_scores["bleu_scores"])
        item_scores["mean_rouge_1_score"] = np.mean(item_scores["rouge_1_scores"])
        item_scores["mean_rouge_l_score"] = np.mean(item_scores["rouge_l_scores"])
        item_scores["mean_semantic_similarity"] = np.mean(item_scores["semantic_similarities"])
        item_scores["mean_llm_judge_score"] = np.mean(item_scores["llm_judge_scores"])
        item_scores["std_time"] = np.std(item_scores["times"], ddof=1) # sample standard deviation
        item_scores["std_bleu_score"] = np.std(item_scores["bleu_scores"], ddof=1)
        item_scores["std_rouge_1_score"] = np.std(item_scores["rouge_1_scores"], ddof=1)
        item_scores["std_rouge_l_score"] = np.std(item_scores["rouge_l_scores"], ddof=1)
        item_scores["std_semantic_similarity"] = np.std(item_scores["semantic_similarities"], ddof=1)
        item_scores["std_llm_judge_score"] = np.std(item_scores["llm_judge_scores"], ddof=1)

        results.append(item_scores)

    # calculate averages and deviations per metric
    averages = {
        "id": "avg",
        "time": np.mean([item["mean_time"] for item in results]),
        "bleu_score": np.mean([item["mean_bleu_score"] for item in results]),
        "rouge_1_score": np.mean([item["mean_rouge_1_score"] for item in results]),
        "rouge_l_score": np.mean([item["mean_rouge_l_score"] for item in results]),
        "semantic_similarity": np.mean([item["mean_semantic_similarity"] for item in results]),
        "llm_judge_score": np.mean([item["mean_llm_judge_score"] for item in results])
    }
    deviations = {
        "id": "std",
        "time": np.mean([item["std_time"] for item in results]),
        "bleu_score": np.mean([item["std_bleu_score"] for item in results]),
        "rouge_1_score": np.mean([item["std_rouge_1_score"] for item in results]),
        "rouge_l_score": np.mean([item["std_rouge_l_score"] for item in results]),
        "semantic_similarity": np.mean([item["std_semantic_similarity"] for item in results]),
        "llm_judge_score": np.mean([item["std_llm_judge_score"] for item in results])
    }

    results.append(averages)
    print(f"Averages for {ANSWER_PATH}:\n{averages}")
    results.append(deviations)
    print(f"Deviations for {ANSWER_PATH}:\n{deviations}")

    # save results
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    print(f"Saving results to {RESULT_PATH}")
    with open(RESULT_PATH, "w") as result_file:
        json.dump(results, result_file, indent=4)


if __name__ == "__main__":
    calculate_results(JUDGE, TIMEOUT)
