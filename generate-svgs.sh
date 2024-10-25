#!/bin/bash

# Array of model strings
models=(
    "gpt-3.5-turbo"
    "gpt-4o-mini"
    "gpt-4o"
    "o1-preview"
    "o1-mini"
    "claude-3-5-sonnet-20240620"
    "claude-3-5-sonnet-20241022"
    "claude-3-haiku-20240307"
    "claude-3-opus-20240229"
    "gemini-1.5-flash-001"
    "gemini-1.5-flash-002"
    "gemini-1.5-pro-001"
    "gemini-1.5-pro-002"
    "gemini-1.5-flash-8b-001"
    "cerebras-llama3.1-8b"
    "cerebras-llama3.1-70b"
)

mkdir -p failures

# Loop through each model
for model in "${models[@]}"; do
    output_file="$model.svg"
    timestamp=$(date '+%Y%m%d%H%M')
    failure_file="failures/$model.$timestamp.txt"
    
    # Check if file already exists
    if [ ! -f "$output_file" ]; then
        echo "Generating SVG using model: $model"
        # Capture both stdout and stderr, and the exit status
        if output=$(llm -m $model 'Generate an SVG of a pelican riding a bicycle' 2>&1); then
            # LLM succeeded, try to extract SVG
            if echo "$output" | rg -U -m1 '<svg[\s\S]*?</svg>' > "$output_file" && [ -s "$output_file" ]; then
                echo "Created $output_file"
            else
                # SVG extraction failed
                echo "$output" > "$failure_file"
                echo "No SVG found - saved output to $failure_file"
                rm -f "$output_file"
            fi
        else
            # LLM command failed
            echo "LLM command failed - saved error to $failure_file"
            echo "$output" > "$failure_file"
        fi
    else
        echo "Skipping $model - file already exists"
    fi
done
