#!/bin/bash

# Script for scraping weekly commit messages from AliceO2 GitHub repository
# Date range: 23 June 2025 to 10 August 2025

set -e

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq not installed. Please install with: sudo apt install jq"
    exit 1
fi

# Create output directory
OUTPUT_DIR="./data/scraped/o2_commits"
mkdir -p "$OUTPUT_DIR"

# Clone the repository and tags
echo "Cloning repository..."
git clone https://github.com/AliceO2Group/AliceO2.git AliceO2
cd AliceO2
git fetch --all --tags

# Define weekly ranges
declare -A weeks=(
    ["1"]="2025-06-23 2025-06-29"
    ["2"]="2025-06-30 2025-07-06"
    ["3"]="2025-07-07 2025-07-13"
    ["4"]="2025-07-14 2025-07-20"
    ["5"]="2025-07-21 2025-07-27"
    ["6"]="2025-07-28 2025-08-03"
    ["7"]="2025-08-04 2025-08-10"
)

# Process each week
for week in $(echo "${!weeks[@]}" | tr ' ' '\n' | sort -n); do
    IFS=' ' read -ra data <<< "${weeks[$week]}"
    start_date="${data[0]}"
    end_date="${data[1]}"

    echo "Processing week $week ($start_date → $end_date)..."

    # Get commit messages and create a JSON file
    git log --since="$start_date 00:00:00" --until="$end_date 23:59:59" --pretty=format:"%s" | \
        jq -R -s --arg start_date "$start_date" --arg end_date "$end_date" \
        'split("\n") | map(select(length > 0)) | {start_date: $start_date, end_date: $end_date, commit_messages: .}' \
        > "../$OUTPUT_DIR/week_$week.json"

    echo "  $(jq '.commit_messages | length' "../$OUTPUT_DIR/week_$week.json") commits"
done

# Cleanup
cd ..
rm -rf AliceO2
echo "✅  Complete! Files saved in: $OUTPUT_DIR"
