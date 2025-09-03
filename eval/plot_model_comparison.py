import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# plot configuration
RESULT_DIR = "eval/results/models/external_qwen_judge"
PLOT_DIR = "img/plots/models/external_qwen_judge"
MODEL_FILES = [
    {
        "before": "base_old_qwen.json",
        "after": "rag_old_qwen.json",
        "label": "Qwen2.5-7B-Instruct*",
        "color": "darkorchid"
    },
    {
        "before": "base_gemini_flash.json",
        "after": None,
        "label": "Gemini-2.5-Flash\n(API)",
        "color": "forestgreen",
    },
    {
        "before": "base_external_gemma.json",
        "after": "rag_external_gemma.json",
        "label": "gemma-3-27B-it",
        "color": "forestgreen",
    },
    {
        "before": "base_external_deepseek.json",
        "after": "rag_external_deepseek.json",
        "label": "DeepSeek-R1-Distill-32B",
        "color": "royalblue",
    },
    {
        "before": "base_external_mistral.json",
        "after": "rag_external_mistral.json",
        "label": "Mistral-Small-3.2-24B-Instruct\n(2506)",
        "color": "darkorange",
    },
    {
        "before": "base_external_gpt.json",
        "after": "rag_external_gpt.json",
        "label": "gpt-oss-20b",
        "color": "firebrick",
    },
    {
        "before": "base_external_qwen.json",
        "after": "rag_external_qwen.json",
        "label": "Qwen3-30B-A3B-Instruct\n(2507)",
        "color": "darkorchid"
    }
]

def plot_metric(metric, y_label, y_min=None, y_max=None):
    plt.figure(figsize=(14, 8))
    before_averages = []
    before_deviations = []
    after_averages = []
    after_deviations = []
    labels = []
    colors = []
    for model_file in MODEL_FILES:
        before_file = model_file["before"]
        after_file = model_file["after"]
        label = model_file["label"]
        color = model_file["color"]

        # load before results
        with open(os.path.join(RESULT_DIR, before_file), "r") as result_file:
            json_data = json.load(result_file)
            avg_item = next(item for item in json_data if item["id"] == "avg")
            std_item = next(item for item in json_data if item["id"] == "std")
            before_averages.append(avg_item[metric])
            before_deviations.append(std_item[metric])

        # load after results
        if after_file:
            with open(os.path.join(RESULT_DIR, after_file), "r") as result_file:
                json_data = json.load(result_file)
                avg_item = next(item for item in json_data if item["id"] == "avg")
                std_item = next(item for item in json_data if item["id"] == "std")
                after_averages.append(avg_item[metric])
                after_deviations.append(std_item[metric])
        else:
            after_averages.append(None)
            after_deviations.append(None)

        labels.append(label)
        colors.append(color)

    # start plot
    x = np.arange(len(labels))
    bar_width = 0.35

    # before bars
    before_x = x - bar_width / 2
    plt.bar(before_x, before_averages, bar_width, yerr=before_deviations, color=colors, alpha=0.6,
            capsize=3, ecolor="black", error_kw={"elinewidth": 0.8}, label="Base LLM")
    plt.plot(before_x, before_averages, marker="o", markersize=3, color="black", linestyle="None")
    before_patch = mpatches.Patch(facecolor="dimgray", alpha=0.6, label="Base LLM")

    # after bars
    after_x = []
    after_values = []
    after_errors = []
    after_colors = []
    for i, (val, err, color) in enumerate(zip(after_averages, after_deviations, colors)):
        if val is not None:
            after_x.append(x[i] + bar_width / 2)
            after_values.append(val)
            after_errors.append(err)
            after_colors.append(color)

    plt.bar(after_x, after_values, bar_width, yerr=after_errors, color=after_colors, alpha=0.9,
            capsize=3, ecolor="black", error_kw={"elinewidth": 0.8}, label="With RAG pipeline")
    plt.plot(after_x, after_values, marker="o", markersize=3, color="black", linestyle="None")
    after_patch = mpatches.Patch(facecolor="dimgray", alpha=0.9, label="With RAG pipeline")

    # decorations
    plt.xticks(x, labels, rotation=30)
    plt.axvline(x=1.325, color='dimgray', linestyle='--', linewidth=1) # separate external models
    plt.xlabel("Model", fontsize=12)
    plt.ylabel(y_label, fontsize=10)
    plt.ylim(y_min, y_max)
    plt.title("Results of chatbot evaluation on a dataset of 35 expert question-answer pairs", fontsize=14)
    plt.legend(handles=[before_patch, after_patch], loc="upper left", shadow=True, fontsize=10)
    plt.tight_layout()
    os.makedirs(PLOT_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOT_DIR, f"{metric}_comparison.png"))
    plt.show()


if __name__ == "__main__":
    plot_metric("bleu_score", "BLEU score ∈ [0, 1]", 0, 0.12)
    plot_metric("rouge_1_score", "ROUGE-1 score ∈ [0, 1]", 0, 0.35)
    plot_metric("rouge_l_score", "ROUGE-L score ∈ [0, 1]", 0, 0.25)
    plot_metric("semantic_similarity", "Semantic similarity score ∈ [0, 1]", 0.6, 0.9)
    plot_metric("llm_judge_score", "LLM-as-judge score ∈ [1, 5]", 1, 5)
    plot_metric("time", "Response time (seconds)", 0, 100)
