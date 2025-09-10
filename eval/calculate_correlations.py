import os
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error
from scipy.stats import zscore, pearsonr, spearmanr


RESULTS_DIR = "eval/results/1_sample"
PLOT_DIR = "img/plots/correlations"
MODEL_FOLDERS = [
    {
        "folder": "external_deepseek_judge",
        "label": "DeepSeek-R1-Distill-32B"
    },
    {
        "folder": "external_gemma_judge",
        "label": "gemma-3-27B-it"
    },
    {
        "folder": "external_gpt_judge",
        "label": "gpt-oss-20b"
    },
    {
        "folder": "external_mistral_judge",
        "label": "Mistral-Small-3.2-24B-Instruct"
    },
    {
        "folder": "external_qwen_judge",
        "label": "Qwen3-30B-A3B-Instruct"
    },
    {
        "folder": "gemini_judge",
        "label": "Gemini-2.5-Flash"
    },
    {
        "folder": "gemini_lite_judge",
        "label": "Gemini-2.5-Flash-Lite"
    },
    {
        "folder": "gemma_judge",
        "label": "gemma-2-9b-it"
    },
    {
        "folder": "llama_judge",
        "label": "Meta-Llama-3.1-8B-Instruct"
    },
    {
        "folder": "mistral_judge",
        "label": "Mistral-7B-Instruct-v0.3"
    },
    {
        "folder": "qwen2.5_judge",
        "label": "Qwen2.5-7B-Instruct"
    }
]


def plot_pearson_heatmap(pearson_matrix, labels):
    plt.figure(figsize=(12, 10))
    sns.heatmap(pearson_matrix, annot=True, cmap="coolwarm", xticklabels=labels, yticklabels=labels, center=0.5)
    plt.title("LLM-as-judge score Pearson coorelations between models")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "pearson_correlation_heatmap.png"))
    plt.show()

def plot_spearman_heatmap(spearman_matrix, labels):
    plt.figure(figsize=(12, 10))
    sns.heatmap(spearman_matrix, annot=True, cmap="coolwarm", xticklabels=labels, yticklabels=labels, center=0.5)
    plt.title("LLM-as-judge score Spearman coorelations between models")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "spearman_correlation_heatmap.png"))
    plt.show()

def plot_rmse_heatmap(rmse_matrix, labels):
    plt.figure(figsize=(12, 10))
    sns.heatmap(rmse_matrix, annot=True, cmap="coolwarm", xticklabels=labels, yticklabels=labels)
    plt.title("LLM-as-judge score root mean squared errors (RMSE) between models")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "rmse_heatmap.png"))
    plt.show()


if __name__ == "__main__":
    results = {}
    # Load judge scores
    for folder in [model_folder["folder"] for model_folder in MODEL_FOLDERS]:
        scores = []
        for file in sorted(os.listdir(f"{RESULTS_DIR}/{folder}")):
            if file.endswith(".json"):
                with open(f"{RESULTS_DIR}/{folder}/{file}") as json_file:
                    json_data = json.load(json_file)
                    scores.extend([item["llm_judge_score"] for item in json_data if item["id"] != "average"])
        results[folder] = scores

    # Compare pairs
    folder_names = list(results.keys())
    pearson_matrix = np.zeros((len(folder_names), len(folder_names)))
    spearman_matrix = np.zeros((len(folder_names), len(folder_names)))
    rmse_matrix = np.zeros((len(folder_names), len(folder_names)))

    for i, f1 in enumerate(folder_names):
        for j, f2 in enumerate(folder_names):
            s1 = results[f1]
            s2 = results[f2]

            if f1 < f2:
                # Normalize scores
                d1 = zscore(s1)
                d2 = zscore(s2)

                # Correlation metrics
                pearson, _ = pearsonr(d1, d2)
                spearman, _ = spearmanr(d1, d2)
                rmse = mean_squared_error(d1, d2) ** 0.5
                print(f"{f1} vs {f2}: Pearson={pearson:.3f}, Spearman={spearman:.3f}, RMSE={rmse:.3f}")

                # Store in matrices
                pearson_matrix[i, j] = pearson_matrix[j, i] = pearson
                spearman_matrix[i, j] = spearman_matrix[j, i] = spearman
                rmse_matrix[i, j] = rmse_matrix[j, i] = rmse
            elif f1 == f2:
                # Diagonal elements
                pearson_matrix[i, j] = 1.0
                spearman_matrix[i, j] = 1.0
                rmse_matrix[i, j] = 0.0

    # Generate heatmaps with model labels
    os.makedirs(PLOT_DIR, exist_ok=True)
    model_labels = [model_folder["label"] for model_folder in MODEL_FOLDERS]
    plot_pearson_heatmap(pearson_matrix, model_labels)
    plot_spearman_heatmap(spearman_matrix, model_labels)
    plot_rmse_heatmap(rmse_matrix, model_labels)
