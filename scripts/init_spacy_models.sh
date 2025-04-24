#!/bin/bash

# Script to download spaCy models during app initialization

echo "Checking for spaCy model en_core_web_lg..."

# Check if model is already installed
python -c "import spacy; spacy.load('en_core_web_lg')" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "SpaCy model en_core_web_lg not found. Downloading..."
    python -m spacy download en_core_web_lg
    if [ $? -eq 0 ]; then
        echo "Successfully downloaded spaCy model en_core_web_lg"
    else
        echo "ERROR: Failed to download spaCy model en_core_web_lg"
        exit 1
    fi
else
    echo "SpaCy model en_core_web_lg is already installed"
fi

# Continue to the next command
echo "SpaCy model initialization complete"
exit 0
