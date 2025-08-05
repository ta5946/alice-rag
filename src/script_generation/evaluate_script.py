#!/usr/bin/env python3

# evaluate_script.py
# Validation stub for Anchored MC workflows
# This script evaluates a shell script by parsing its environment variables, validating them, and simulating its execution
# It returns a JSON object with a summary of variable checks and a list of detailed errors

import os, sys, re, subprocess, tempfile, shutil, stat
import json


# Define all variables and their validation rules, error messages, and default values
ENVIRONMENT_VARIABLES = {
    "ALIEN_JDL_LPMRUNNUMBER": (True, lambda x: x.isdigit() and int(x) > 0, "must be a positive integer", None),
    "ALIEN_JDL_LPMANCHORPASSNAME": (True, lambda x: bool(x.strip()), "must be a non-empty string", None),
    "ALIEN_JDL_LPMINTERACTIONTYPE": (True, lambda x: x in ("pp", "Pb-Pb"), "must be 'pp' or 'Pb-Pb'", None),
    "SPLITID": (True, lambda x: x.isdigit() and 1 <= int(x) <= 100, "must be an integer between 1 and 100", None),
    "NTIMEFRAMES": (True, lambda x: x.isdigit() and int(x) > 0, "must be a positive integer", None),
    "ALIEN_JDL_CPULIMIT": (False, lambda x: x.isdigit() and int(x) > 0, "must be a positive integer", "8"),
    "ALIEN_JDL_SIMENGINE": (False, lambda x: x in ("TGeant3", "TGeant4", "VMC"), "must be 'TGeant3', 'TGeant4', or 'VMC'", "TGeant4"),
    "ALIEN_JDL_ANCHOR_SIM_OPTIONS": (False, lambda x: not x or x.startswith("-"), "must be empty or contain a valid flag like '-gen' or '--trigger-external'", ""),
    "NSIGEVENTS": (False, lambda x: x.isdigit() and int(x) > 0, "must be a positive integer", "10000"),
    "CYCLE": (False, lambda x: x.isdigit() and int(x) >= 0, "must be a non-negative integer", "0"),
}

# Regex to find "export VAR=value" lines
EXPORT_RE = re.compile(r"^export\s+(\w+)=(.+)", re.M)

# Helper function to parse shell exports
def parse_exports(script_text):
    return {
        k: v.split("#", 1)[0].strip(" \"")
        for k, v in EXPORT_RE.findall(script_text)
    }

# Helper function to simulate script execution
def can_run(script_text):
    stub_src = os.path.join(os.getcwd(), "anchorMC.sh")
    if not os.path.isfile(stub_src):
        return 1, "Error: Required stub 'anchorMC.sh' not found."

    with tempfile.TemporaryDirectory() as d:
        stub_dst = os.path.join(d, "anchorMC.sh")
        shutil.copy(stub_src, stub_dst)
        os.chmod(stub_dst, stat.S_IRWXU)

        # Create a temporary wrapper to run the user script
        wrapper_path = os.path.join(d, "run.sh")
        wrapped_text = f"#!/usr/bin/env bash\nset -e\n{script_text}"
        wrapped_text = re.sub(r"\${O2DPG_ROOT}/MC/run/ANCHOR/anchorMC.sh", "./anchorMC.sh", wrapped_text)
        with open(wrapper_path, "w") as f:
            f.write(wrapped_text)
        os.chmod(wrapper_path, stat.S_IRWXU)

        result = subprocess.run(["bash", wrapper_path], cwd=d,
                                stderr=subprocess.PIPE, text=True)
        return result.returncode, result.stderr

# Main function to evaluate the script
def evaluate_script(path):
    errors = []
    try:
        with open(path) as f:
            script_text = f.read()
    except FileNotFoundError:
        return {
            "required_variables": 0/5,
            "valid_variables": 0/10,
            "script_runs": 0,
            "errors": [f"Error: Script file '{path}' not found."]
        }

    env = parse_exports(script_text)
    req_set = 0
    valid_count = 0

    # Create a final environment dictionary with defaults for optional variables
    final_env = env.copy()
    for var, (_, _, _, default) in ENVIRONMENT_VARIABLES.items():
        if var not in final_env and default is not None:
            final_env[var] = default

    for var, (is_req, validator, error_msg, _) in ENVIRONMENT_VARIABLES.items():
        if is_req:
            if var in env:
                req_set += 1
            else:
                errors.append(f"Required variable '{var}' is not set.")

        if var in final_env:
            if validator(final_env[var]):
                valid_count += 1
            elif var in env:
                errors.append(f"Invalid value for '{var}': {error_msg}. Value was '{env[var]}'.")

    return_code, stderr = can_run(script_text)
    if return_code != 0 or stderr.strip():
        errors.append(f"Script run failed with exit code {return_code}. Output: {stderr.strip()}")

    return {
        "required_variables": req_set/5,
        "valid_variables": valid_count/10,
        "can_run": return_code == 0,
        "errors": errors
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python evaluate_script.py <script.sh>", file=sys.stderr)
        sys.exit(1)

    results = evaluate_script(sys.argv[1])
    print(json.dumps(results, indent=2))
    sys.exit(0)
