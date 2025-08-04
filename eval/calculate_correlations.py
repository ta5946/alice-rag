import os
import json
from sklearn.metrics import mean_squared_error
from scipy.stats import zscore, pearsonr, spearmanr

RESULTS_DIR = "eval/results/1_sample"


if __name__ == "__main__":
    results = {}
    # Load judge scores
    for folder in sorted(os.listdir(RESULTS_DIR)):
        scores = []
        for file in sorted(os.listdir(f"{RESULTS_DIR}/{folder}")):
            if file.endswith('.json'):
                with open(f"{RESULTS_DIR}/{folder}/{file}") as json_file:
                    json_data = json.load(json_file)
                    scores.extend([item["llm_judge_score"] for item in json_data if item["id"] != "average"])
        results[folder] = scores

    # Compare pairs
    for f1, s1 in results.items():
        for f2, s2 in results.items():
            if f1 < f2:
                # Normalize scores
                d1 = zscore(s1)
                d2 = zscore(s2)

                # Correlation metrics
                pearson, _ = pearsonr(d1, d2)
                spearman, _ = spearmanr(d1, d2)
                rmse = mean_squared_error(d1, d2) ** 0.5
                print(f"{f1} vs {f2}: Pearson={pearson:.3f}, Spearman={spearman:.3f}, RMSE={rmse:.3f}")
