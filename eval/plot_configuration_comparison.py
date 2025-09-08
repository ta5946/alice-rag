import os
import json
import numpy as np
import matplotlib.pyplot as plt

RESULT_DIR = "eval/results/vectorstores/external_qwen_judge"
PLOT_DIR = "img/plots/configurations/external_qwen_judge"
SCORE_COLOR = "mediumblue"
TIME_COLOR = "firebrick"
CONFIG_FILES = [
    {
        "file": "base.json",
        "label": "No RAG\n(n=0)"
    },
    {
        "file": "analysis_bge_base_low.json",
        "label": "Low recall\n(n=5)"
    },
    {
        "file": "analysis_bge_base_med.json",
        "label": "Medium recall\n(n=10)"
    },
    {
        "file": "analysis_bge_base_high.json",
        "label": "High recall\n(n=15)"
    },
    {
        "file": "analysis_bge_base_max.json",
        "label": "Maximum recall\n(n=20)"
    }
]


def plot_score_and_time(metric, y_label, y_min=None, y_max=None):
    fig, ax1 = plt.subplots(figsize=(14, 8))
    score_averages = []
    score_deviations = []
    time_averages = []
    time_deviations = []
    labels = []
    for config in CONFIG_FILES:
        with open(os.path.join(RESULT_DIR, config["file"]), "r") as result_file:
            json_data = json.load(result_file)
            avg_item = next(item for item in json_data if item["id"] == "avg")
            dev_item = next(item for item in json_data if item["id"] == "std")
            score_averages.append(avg_item[metric])
            time_averages.append(avg_item["time"])
            score_deviations.append(dev_item[metric])
            time_deviations.append(dev_item["time"])
            labels.append(config["label"])

    # score on left axis
    x = np.arange(len(labels))

    ax1.errorbar(x[0], score_averages[0], yerr=score_deviations[0],
                 color=SCORE_COLOR, capsize=4, capthick=2, marker="o", markersize=5)
    ax1.errorbar(x[1:], score_averages[1:], yerr=score_deviations[1:],
                 color=SCORE_COLOR, capsize=4, capthick=2, marker="o", markersize=5)

    ax1.set_xticks(x)
    ax1.axvline(x=0.5, color='dimgray', linestyle='--', linewidth=2)
    ax1.set_xticklabels(labels, rotation=30)
    ax1.set_xlabel("Database configuration", fontsize=12)
    ax1.set_ylim(y_min, y_max)
    ax1.set_ylabel(y_label, color=SCORE_COLOR, fontsize=12)
    ax1.tick_params(axis="y", labelcolor=SCORE_COLOR)

    # time on right axis
    ax2 = ax1.twinx()

    ax2.errorbar(x[0], time_averages[0], yerr=time_deviations[0],
                 color=TIME_COLOR, capsize=4, capthick=2, marker="o", markersize=5)
    ax2.errorbar(x[1:], time_averages[1:], yerr=time_deviations[1:],
                 color=TIME_COLOR, capsize=4, capthick=2, marker="o", markersize=5)

    ax2.set_ylim(0, 60)
    ax2.set_ylabel("Response time (seconds)", color=TIME_COLOR, fontsize=12)
    ax2.tick_params(axis="y", labelcolor=TIME_COLOR)

    # plot decorations
    plt.title("Results of chatbot evaluation on a dataset of 35 expert question-answer pairs", fontsize=14)
    plt.tight_layout()
    os.makedirs(PLOT_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOT_DIR, f"{metric}_and_time_comparison.png"))
    plt.show()


if __name__ == "__main__":
    plot_score_and_time("bleu_score", "BLEU score ∈ [0, 1]", 0, 0.12)
    plot_score_and_time("rouge_l_score", "ROUGE-L score ∈ [0, 1]", 0, 0.25)
    plot_score_and_time("semantic_similarity", "Semantic similarity score ∈ [0, 1]", 0.6, 0.9)
    plot_score_and_time("llm_judge_score", "LLM-as-judge score ∈ [1, 5]", 1, 5)