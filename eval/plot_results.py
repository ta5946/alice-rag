import os
import json
import matplotlib.pyplot as plt

RESULT_PATH = "eval/results/gemini_lite_judge"
PLOT_PATH = "img/plots/gemini_lite_judge"


# plot configuration
PLOT_TITLE = "Results of evaluation on 25 question-answer pairs"
MODEL_RESULTS = ["base_qwen_results.json", "base_gemini_results.json", "rag_qwen_results.json", "extended_rag_qwen_results.json"]
MODEL_NAMES = ["Qwen2.5-7B", "Gemini-2.5-Flash", "Qwen2.5-7B + RAG", "Qwen2.5-7B + Extended RAG"]
MODEL_COLORS = ["mediumorchid", "steelblue", "firebrick", "darkorange"]

def plot_metric(metric, y_label, y_min=None, y_max=None):
    plt.figure(figsize=(10, 6))
    for result, model, color in zip(MODEL_RESULTS, MODEL_NAMES, MODEL_COLORS):
        with open(os.path.join(RESULT_PATH, result), "r") as result_file:
            average_metrics = next(item for item in json.load(result_file) if item["id"] == "average") # get average metrics
            plt.bar(model, average_metrics[metric], color=color, label=model)

    plt.ylim(y_min, y_max)
    plt.ylabel(y_label)
    plt.xlabel("Model")
    plt.title(PLOT_TITLE)
    os.makedirs(PLOT_PATH, exist_ok=True)
    plt.savefig(os.path.join(PLOT_PATH, f"{metric}_comparison.png"))
    plt.show()


if __name__ == "__main__":
    plot_metric("bleu_score", "BLEU score ∈ [0, 1]", 0, 0.1)
    plot_metric("rouge_l_score", "ROUGE-L score ∈ [0, 1]", 0, 0.2)
    plot_metric("semantic_similarity", "Semantic similarity score ∈ [0, 1]", 0.5, 1)
    plot_metric("llm_judge_score", "LLM-as-judge score ∈ [1, 5]", 1, 5)
    plot_metric("time", "Response time (seconds)", 0, 50)
