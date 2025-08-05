#!/usr/bin/env bash

# anchorMC.sh
# Validation stub for Anchored MC workflows
# This script is used by evaluate_script.py to check for correct environment variable settings
# It exits with error status on the first validation failure

# Exit on any error
set -e

# Set default values for optional variables if they are not set
: ${ALIEN_JDL_CPULIMIT:=8}
: ${ALIEN_JDL_SIMENGINE:="TGeant4"}
: ${ALIEN_JDL_ANCHOR_SIM_OPTIONS:=""}
: ${NSIGEVENTS:=10000}
: ${CYCLE:=0}

# Define validation functions for reuse
function is_positive_int() {
    [[ "$1" =~ ^[0-9]+$ ]] && (( "$1" > 0 ))
}

function is_non_neg_int() {
    [[ "$1" =~ ^[0-9]+$ ]] && (( "$1" >= 0 ))
}

# Helper functions for specific validations
function is_non_empty() {
    [ -n "$1" ]
}

function is_interaction_type() {
    [[ "$1" == "pp" || "$1" == "Pb-Pb" ]]
}

function is_split_id() {
    is_positive_int "$1" && (( "$1" <= 100 ))
}

function is_sim_engine() {
    [[ "$1" == "TGeant3" || "$1" == "TGeant4" || "$1" == "VMC" ]]
}

# New function to validate simulation options
function is_valid_sim_options() {
    # Check if the string is empty or starts with a hyphen
    [[ -z "$1" ]] || [[ "$1" =~ ^- ]]
}

# Define all variables and their validation rules
declare -a required_vars=(
  "ALIEN_JDL_LPMRUNNUMBER:is_positive_int:must be a positive integer"
  "ALIEN_JDL_LPMANCHORPASSNAME:is_non_empty:must be non-empty"
  "ALIEN_JDL_LPMINTERACTIONTYPE:is_interaction_type:must be 'pp' or 'Pb-Pb'"
  "SPLITID:is_split_id:must be an integer between 1 and 100"
  "NTIMEFRAMES:is_positive_int:must be a positive integer"
)

declare -a optional_vars=(
  "ALIEN_JDL_CPULIMIT:is_positive_int:must be a positive integer"
  "ALIEN_JDL_SIMENGINE:is_sim_engine:must be TGeant3, TGeant4, or VMC"
  "ALIEN_JDL_ANCHOR_SIM_OPTIONS:is_valid_sim_options:must be empty or contain a valid flag like '-gen' or '--trigger-external'"
  "NSIGEVENTS:is_positive_int:must be a positive integer"
  "CYCLE:is_non_neg_int:must be a non-negative integer"
)

# Generic validation loop for required variables
for var_info in "${required_vars[@]}"; do
    IFS=':' read -r var_name validator_func error_msg <<< "$var_info"

    # Check if the variable is set
    if [ -z "${!var_name}" ]; then
        echo "ERROR: Required variable $var_name is not set" >&2
        exit 1
    fi

    # Run the specific validator function
    if ! "$validator_func" "${!var_name}"; then
        echo "ERROR: $var_name $error_msg" >&2
        exit 1
    fi
done

# Generic validation loop for optional variables
for var_info in "${optional_vars[@]}"; do
    IFS=':' read -r var_name validator_func error_msg <<< "$var_info"

    if ! "$validator_func" "${!var_name}"; then
        echo "ERROR: $var_name $error_msg" >&2
        exit 1
    fi
done

# If all checks pass, return success
exit 0
