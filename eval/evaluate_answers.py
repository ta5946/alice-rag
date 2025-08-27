import os
import json
import numpy as np
from tqdm import tqdm
from src.chatbot.langchain_components import *
from eval.metrics import *


# evaluation configuration
ANSWER_DIR = "eval/answers/final"
RESULT_DIR = "eval/results/final"
JUDGES = [External.DEEPSEEK]
TIMEOUT = 0

def single_calculate_results(answer_path, judge, timeout, result_path):
    # load answers
    with open(answer_path, "r") as answer_file:
        qa_dataset = json.load(answer_file)

    # get metrics for each answer
    results = []
    for item in tqdm(qa_dataset, desc="Calculating metrics", unit="question"):
        try:
            judge_score = llm_judge_score(item["question"], item["correct_answer"], item["generated_answer"], judge, timeout)
        except Exception as error:
            print("calculate_results():", error)
            judge_score = None # return None on error

        item_scores = {
            "id": item["id"],
            "time": item["time"],
            "bleu_score": bleu_score(item["correct_answer"], item["generated_answer"]),
            "rouge_1_score": rouge_score(item["correct_answer"], item["generated_answer"], "rouge1"),
            "rouge_l_score": rouge_score(item["correct_answer"], item["generated_answer"]),
            "semantic_similarity": semantic_similarity_score(item["correct_answer"], item["generated_answer"]),
            "llm_judge_score": judge_score
        }
        results.append(item_scores)

    # calculate average scores without None values
    valid_results = [item for item in results if item["llm_judge_score"] is not None]

    average_scores = {
        "id": "average",
        "time": sum(item["time"] for item in results) / len(results),
        "bleu_score": sum(item["bleu_score"] for item in results) / len(results),
        "rouge_1_score": sum(item["rouge_1_score"] for item in results) / len(results),
        "rouge_l_score": sum(item["rouge_l_score"] for item in results) / len(results),
        "semantic_similarity": sum(item["semantic_similarity"] for item in results) / len(results),
        "llm_judge_score": sum(item["llm_judge_score"] for item in valid_results) / len(valid_results) if valid_results else None
    }
    results.append(average_scores)
    print(f"Average scores for {answer_path}:\n{average_scores}")

    # save results
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    print(f"Saving results to {result_path}")
    with open(result_path, "w") as result_file:
        json.dump(results, result_file, indent=4)

def multiple_calculate_results(answer_path, judge, timeout, result_path):
    # load answers
    with open(answer_path, "r") as answer_file:
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
                judge_score = None # return None on error

            item_scores["times"].append(item["times"][i])
            item_scores["bleu_scores"].append(bleu_score(item["correct_answer"], generated_answer))
            item_scores["rouge_1_scores"].append(rouge_score(item["correct_answer"], generated_answer, "rouge1"))
            item_scores["rouge_l_scores"].append(rouge_score(item["correct_answer"], generated_answer, "rougeL"))
            item_scores["semantic_similarities"].append(semantic_similarity_score(item["correct_answer"], generated_answer))
            item_scores["llm_judge_scores"].append(judge_score)

        # filter out None values for judge scores
        valid_judge_scores = [score for score in item_scores["llm_judge_scores"] if score is not None]

        item_scores["mean_time"] = np.mean(item_scores["times"]) # sample mean
        item_scores["mean_bleu_score"] = np.mean(item_scores["bleu_scores"])
        item_scores["mean_rouge_1_score"] = np.mean(item_scores["rouge_1_scores"])
        item_scores["mean_rouge_l_score"] = np.mean(item_scores["rouge_l_scores"])
        item_scores["mean_semantic_similarity"] = np.mean(item_scores["semantic_similarities"])
        item_scores["mean_llm_judge_score"] = np.mean(valid_judge_scores) if valid_judge_scores else None

        item_scores["std_time"] = np.std(item_scores["times"], ddof=1) # sample standard deviation
        item_scores["std_bleu_score"] = np.std(item_scores["bleu_scores"], ddof=1)
        item_scores["std_rouge_1_score"] = np.std(item_scores["rouge_1_scores"], ddof=1)
        item_scores["std_rouge_l_score"] = np.std(item_scores["rouge_l_scores"], ddof=1)
        item_scores["std_semantic_similarity"] = np.std(item_scores["semantic_similarities"], ddof=1)
        item_scores["std_llm_judge_score"] = np.std(valid_judge_scores, ddof=1) if len(valid_judge_scores) > 1 else None

        results.append(item_scores)

    # calculate averages and deviations per metric without None values
    valid_mean_judge_scores = [item["mean_llm_judge_score"] for item in results if item["mean_llm_judge_score"] is not None]
    valid_std_judge_scores = [item["std_llm_judge_score"] for item in results if item["std_llm_judge_score"] is not None]
    averages = {
        "id": "avg",
        "time": np.mean([item["mean_time"] for item in results]),
        "bleu_score": np.mean([item["mean_bleu_score"] for item in results]),
        "rouge_1_score": np.mean([item["mean_rouge_1_score"] for item in results]),
        "rouge_l_score": np.mean([item["mean_rouge_l_score"] for item in results]),
        "semantic_similarity": np.mean([item["mean_semantic_similarity"] for item in results]),
        "llm_judge_score": np.mean(valid_mean_judge_scores) if valid_mean_judge_scores else None
    }
    deviations = {
        "id": "std",
        "time": np.mean([item["std_time"] for item in results]),
        "bleu_score": np.mean([item["std_bleu_score"] for item in results]),
        "rouge_1_score": np.mean([item["std_rouge_1_score"] for item in results]),
        "rouge_l_score": np.mean([item["std_rouge_l_score"] for item in results]),
        "semantic_similarity": np.mean([item["std_semantic_similarity"] for item in results]),
        "llm_judge_score": np.mean(valid_std_judge_scores) if valid_std_judge_scores else None
    }

    results.append(averages)
    print(f"Averages for {answer_path}:\n{averages}")
    results.append(deviations)
    print(f"Deviations for {answer_path}:\n{deviations}")

    # save results
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    print(f"Saving results to {result_path}")
    with open(result_path, "w") as result_file:
        json.dump(results, result_file, indent=4)

def evaluate_directory(answer_dir, judges, timeout, result_dir):
    for judge in judges:
        judge_prefix = judge_name(judge)

        answer_files = os.listdir(answer_dir)
        answer_files.sort()
        for answer_file in answer_files:
            if not answer_file.endswith(".json"):
                continue
            answer_path = os.path.join(answer_dir, answer_file)
            result_path = os.path.join(result_dir, judge_prefix, answer_file)
            if os.path.exists(result_path):
                print(f"Skipping {answer_path} with {judge_prefix}")
                continue

            print(f"Evaluating {answer_path} with {judge_prefix}...")
            multiple_calculate_results(answer_path, judge, timeout, result_path)


if __name__ == "__main__":
    evaluate_directory(ANSWER_DIR, JUDGES, TIMEOUT, RESULT_DIR)
