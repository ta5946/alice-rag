import os
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error
from scipy.stats import zscore, pearsonr, spearmanr


RESULTS_DIR = "eval/results/1_sample"
PLOT_DIR = "img/plots/correlations"

def plot_pearson_heatmap(pearson_matrix, folder_names):
    plt.figure(figsize=(12, 10))
    sns.heatmap(pearson_matrix, annot=True, cmap="coolwarm", center=0, xticklabels=folder_names, yticklabels=folder_names)
    plt.title("LLM Judge Pearson Correlation")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "pearson_correlation_heatmap.png"))
    plt.show()

def plot_spearman_heatmap(spearman_matrix, folder_names):
    plt.figure(figsize=(12, 10))
    sns.heatmap(spearman_matrix, annot=True, cmap="coolwarm", center=0, xticklabels=folder_names, yticklabels=folder_names)
    plt.title("LLM Judge Spearman Correlation")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "spearman_correlation_heatmap.png"))
    plt.show()

def plot_rmse_heatmap(rmse_matrix, folder_names):
    plt.figure(figsize=(12, 10))
    sns.heatmap(rmse_matrix, annot=True, cmap="coolwarm", xticklabels=folder_names, yticklabels=folder_names)
    plt.title("LLM Judge Root Mean Squared Error")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "rmse_heatmap.png"))
    plt.show()


if __name__ == "__main__":
    results = {}
    # Load judge scores
    for folder in sorted(os.listdir(RESULTS_DIR)):
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

    # Generate heatmaps
    os.makedirs(PLOT_DIR, exist_ok=True)
    folder_names = [name.replace("_judge", "") for name in folder_names]
    plot_pearson_heatmap(pearson_matrix, folder_names)
    plot_spearman_heatmap(spearman_matrix, folder_names)
    plot_rmse_heatmap(rmse_matrix, folder_names)
