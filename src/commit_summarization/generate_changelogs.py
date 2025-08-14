import os
import json
import subprocess


COMMIT_DIR = "./data/scraped/o2_commits"

# Changelog generator system prompt
SYSTEM_PROMPT = """You are a changelog / release notes generator.
You are provided with a list of commit messages and their authors.
Your task is to summarize the commits and generate a short changelog like:

## What's Changed
- FST: Fix running TPC at P2 online without GPUs by @davidrohr
- ITS Calibration: always reset chipDone counter independently on hits by @iravasen in #13386
- Simplify builder holders by @ktf
- Add support for bitmap in ROFRecords by @mconcas in #13385
- Avoid doing one iteration when the tree has no entries by @ktf

Try to group together similar commits and changes from the same author.
The final list should contain 5 to 10 items.
Return only the generated changelog in markdown format and nothing else.
"""

if __name__ == "__main__":
    files = os.listdir(COMMIT_DIR)
    files.sort()
    for file in files:
        if not file.endswith(".json"):
            continue

        # Load JSON file
        commit_file_path = os.path.join(COMMIT_DIR, file)
        with open(commit_file_path, "r") as commit_file:
            commit_json = json.load(commit_file)
            commit_history = commit_json.get("commit_history")

            # Prepare the payload
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"COMMIT HISTORY:\n{commit_history}"
                    }
                ],
                "temperature": 0
            }
            payload_str = json.dumps(payload)

            # Execute curl
            curl = [
                "curl",
                "http://pc-alice-ph01:8080/v1/chat/completions",
                "-H", "Content-Type: application/json",
                "-d", payload_str
            ]
            response = subprocess.run(curl, capture_output=True, text=True)
            response_json = json.loads(response.stdout)

            # Save model response
            response_text = response_json["choices"][0]["message"]["content"]
            print(response_text)
            commit_json["generated_changelog"] = response_text
            with open(commit_file_path, "w") as commit_file:
                json.dump(commit_json, commit_file, indent=4)
