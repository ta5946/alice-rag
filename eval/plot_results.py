import os
import json
import matplotlib.pyplot as plt

RESULT_PATH = "eval/results/synthetic/gemma_judge"
PLOT_PATH = "img/plots/synthetic/gemma_judge"


# plot configuration
N_SAMPLES = 5
PLOT_TITLE = f"Results of evaluation on 25 questions (with {N_SAMPLES} sampled answers per question)"
MODEL_RESULTS = ["med_rag_qwen_1000.json", "rag_qwen_medium_questions.json", "rag_qwen_all_paraphrased.json"]
MODEL_NAMES = ["Qwen2.5 + Medium RAG", "+ Synthetic questions and answers", "+ Paraphrased documents"]
MODEL_COLORS = [
    "#1f77b4",  # medium blue
    "#ff4136",  # vivid red
    "#ff851b",  # bright orange
]

def plot_metric(metric, y_label, y_min=None, y_max=None):
    plt.figure(figsize=(12, 8))
    for result, model, color in zip(MODEL_RESULTS, MODEL_NAMES, MODEL_COLORS):
        with open(os.path.join(RESULT_PATH, result), "r") as result_file:
            json_data = json.load(result_file)
            averages = next(item for item in json_data if item["id"] == "avg") # get metric averages
            deviations = next(item for item in json_data if item["id"] == "std") # get metric deviations
            plt.bar(model, averages[metric], yerr=deviations[metric], color=color, capsize=5, ecolor="black")
            plt.plot(model, averages[metric], marker="o", markersize=5, color="black")

    plt.ylim(y_min, y_max)
    plt.ylabel(y_label)
    plt.xlabel("Model")
    plt.title(PLOT_TITLE)
    os.makedirs(PLOT_PATH, exist_ok=True)
    plt.savefig(os.path.join(PLOT_PATH, f"{metric}_comparison.png"))
    plt.show()


if __name__ == "__main__":
    plot_metric("bleu_score", "BLEU score ∈ [0, 1]", 0, 0.15)
    plot_metric("rouge_l_score", "ROUGE-L score ∈ [0, 1]", 0, 0.25)
    plot_metric("semantic_similarity", "Semantic similarity score ∈ [0, 1]", 0.5, 1)
    plot_metric("llm_judge_score", "LLM-as-judge score ∈ [1, 5]", 1, 5)
    plot_metric("time", "Response time (seconds)", 0, 80)
