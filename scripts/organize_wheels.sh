#!/bin/bash
# Organize existing wheels into version-specific directories
# Usage: ./scripts/organize_wheels.sh

set -e

# Create version-specific directories
mkdir -p wheels/py310 wheels/py311 wheels/py312 wheels/py313

# Count wheels that need to be organized
WHEEL_COUNT=$(find wheels -maxdepth 1 -name "*.whl" | wc -l)
echo "Found $WHEEL_COUNT wheels to organize"

if [ "$WHEEL_COUNT" -eq 0 ]; then
  echo "No wheels found in the root directory. All wheels may already be organized."
  exit 0
fi

# Move wheels to appropriate directories based on filename pattern
echo "Organizing wheels by Python version..."

for wheel in wheels/*.whl; do
  if [[ "$wheel" == *"cp310"* ]]; then
    echo "Moving $(basename $wheel) to wheels/py310/"
    mv "$wheel" wheels/py310/
  elif [[ "$wheel" == *"cp311"* ]]; then
    echo "Moving $(basename $wheel) to wheels/py311/"
    mv "$wheel" wheels/py311/
  elif [[ "$wheel" == *"cp312"* ]]; then
    echo "Moving $(basename $wheel) to wheels/py312/"
    mv "$wheel" wheels/py312/
  elif [[ "$wheel" == *"cp313"* ]]; then
    echo "Moving $(basename $wheel) to wheels/py313/"
    mv "$wheel" wheels/py313/
  elif [[ "$wheel" == *"py3"* ]] || [[ "$wheel" == *"py2.py3"* ]]; then
    # Pure Python wheels compatible with any version - copy to all dirs
    echo "Copying $(basename $wheel) to all version directories (pure Python wheel)"
    cp "$wheel" wheels/py310/
    cp "$wheel" wheels/py311/
    cp "$wheel" wheels/py312/
    cp "$wheel" wheels/py313/
    rm "$wheel"
  else
    echo "Unknown Python version for $(basename $wheel), leaving in root directory"
  fi
done

# Create manifest files in each directory
for dir in wheels/py{310,311,312,313}; do
  WHEEL_COUNT=$(find "$dir" -name "*.whl" | wc -l)
  SQLALCHEMY_WHEEL=$(find "$dir" -name "sqlalchemy*.whl" 2>/dev/null || echo "Not found")
  
  echo "Python Version: ${dir#wheels/py}" > "$dir/manifest.txt"
  echo "Wheel Count: $WHEEL_COUNT" >> "$dir/manifest.txt"
  echo "Date: $(date)" >> "$dir/manifest.txt"
  echo "SQLAlchemy: ${SQLALCHEMY_WHEEL##*/}" >> "$dir/manifest.txt"
done

echo "Wheel organization complete."
echo "Remember to commit all wheel directories to the repository for offline installation."