#!/bin/bash

# Script to download spaCy models during app initialization


MODELS=("en_core_web_sm" "en_core_web_lg")

for MODEL in "${MODELS[@]}"; do
    echo "Checking for spaCy model $MODEL..."

    # Check if model is already installed
    python - <<EOF 2>/dev/null
import spacy
spacy.load("$MODEL")
EOF

    if [ $? -ne 0 ]; then
        echo "SpaCy model $MODEL not found. Downloading..."
        python -m spacy download "$MODEL"
        if [ $? -eq 0 ]; then
            echo "Successfully downloaded spaCy model $MODEL"
        else
            echo "ERROR: Failed to download spaCy model $MODEL"
            exit 1
        fi
    else
        echo "SpaCy model $MODEL is already installed"
    fi
done

# Continue to the next command
echo "SpaCy model initialization complete"
exit 0
