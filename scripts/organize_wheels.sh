#!/bin/bash
# Organize existing wheels into version-specific and platform-specific directories
# Usage: ./scripts/organize_wheels.sh

set -e

# Determine current platform
if [[ "$(uname)" == "Darwin" ]]; then
    OS_TYPE="macos"
elif [[ "$(uname)" == "Linux" ]]; then
    OS_TYPE="linux"
elif [[ "$(uname)" == *"MINGW"* ]] || [[ "$(uname)" == *"MSYS"* ]]; then
    OS_TYPE="windows"
else
    OS_TYPE="other"
fi

# Create an abbreviated architecture name
MACHINE_TYPE=$(uname -m)
if [[ "$MACHINE_TYPE" == "x86_64" ]] || [[ "$MACHINE_TYPE" == "AMD64" ]]; then
    ARCH="x64"
elif [[ "$MACHINE_TYPE" == "arm64" ]] || [[ "$MACHINE_TYPE" == "aarch64" ]]; then
    ARCH="arm64"
else
    ARCH="$MACHINE_TYPE"
fi

CURRENT_PLATFORM="${OS_TYPE}-${ARCH}"
echo "Current platform: $CURRENT_PLATFORM"

# Create version-specific directories for legacy compatibility
mkdir -p wheels/py310 wheels/py311 wheels/py312 wheels/py313

# Create platform-specific directories
mkdir -p wheels/py310-${CURRENT_PLATFORM} wheels/py311-${CURRENT_PLATFORM} wheels/py312-${CURRENT_PLATFORM} wheels/py313-${CURRENT_PLATFORM}

# Count wheels that need to be organized
WHEEL_COUNT=$(find wheels -maxdepth 1 -name "*.whl" | wc -l)
echo "Found $WHEEL_COUNT wheels to organize"

if [ "$WHEEL_COUNT" -eq 0 ]; then
  echo "No wheels found in the root directory. All wheels may already be organized."
  exit 0
fi

# Move wheels to appropriate directories based on filename pattern
echo "Organizing wheels by Python version and platform..."

for wheel in wheels/*.whl; do
  # Skip if not a file
  [ -f "$wheel" ] || continue
  
  # Determine if this is a platform-specific wheel
  if [[ "$wheel" == *"macosx"* ]] || [[ "$wheel" == *"manylinux"* ]] || [[ "$wheel" == *"win"* ]]; then
    IS_PLATFORM_SPECIFIC=true
  else
    IS_PLATFORM_SPECIFIC=false
  fi
  
  # Check standard version-specific wheels
  if [[ "$wheel" == *"cp310"* ]]; then
    PYVER="310"
    echo "Processing $(basename $wheel) for Python 3.10"
    
    # Copy to both version-specific and platform-specific directories
    if [ "$IS_PLATFORM_SPECIFIC" = true ]; then
      echo "  - Moving to platform-specific directory: wheels/py${PYVER}-${CURRENT_PLATFORM}/"
      mv "$wheel" "wheels/py${PYVER}-${CURRENT_PLATFORM}/"
    else
      echo "  - Copying to version-specific directory: wheels/py${PYVER}/"
      cp "$wheel" "wheels/py${PYVER}/"
      echo "  - Moving to platform-specific directory: wheels/py${PYVER}-${CURRENT_PLATFORM}/"
      mv "$wheel" "wheels/py${PYVER}-${CURRENT_PLATFORM}/"
    fi
  elif [[ "$wheel" == *"cp311"* ]]; then
    PYVER="311"
    echo "Processing $(basename $wheel) for Python 3.11"
    
    # Copy to both version-specific and platform-specific directories
    if [ "$IS_PLATFORM_SPECIFIC" = true ]; then
      echo "  - Moving to platform-specific directory: wheels/py${PYVER}-${CURRENT_PLATFORM}/"
      mv "$wheel" "wheels/py${PYVER}-${CURRENT_PLATFORM}/"
    else
      echo "  - Copying to version-specific directory: wheels/py${PYVER}/"
      cp "$wheel" "wheels/py${PYVER}/"
      echo "  - Moving to platform-specific directory: wheels/py${PYVER}-${CURRENT_PLATFORM}/"
      mv "$wheel" "wheels/py${PYVER}-${CURRENT_PLATFORM}/"
    fi
  elif [[ "$wheel" == *"cp312"* ]]; then
    PYVER="312"
    echo "Processing $(basename $wheel) for Python 3.12"
    
    # Copy to both version-specific and platform-specific directories
    if [ "$IS_PLATFORM_SPECIFIC" = true ]; then
      echo "  - Moving to platform-specific directory: wheels/py${PYVER}-${CURRENT_PLATFORM}/"
      mv "$wheel" "wheels/py${PYVER}-${CURRENT_PLATFORM}/"
    else
      echo "  - Copying to version-specific directory: wheels/py${PYVER}/"
      cp "$wheel" "wheels/py${PYVER}/"
      echo "  - Moving to platform-specific directory: wheels/py${PYVER}-${CURRENT_PLATFORM}/"
      mv "$wheel" "wheels/py${PYVER}-${CURRENT_PLATFORM}/"
    fi
  elif [[ "$wheel" == *"cp313"* ]]; then
    PYVER="313"
    echo "Processing $(basename $wheel) for Python 3.13"
    
    # Copy to both version-specific and platform-specific directories
    if [ "$IS_PLATFORM_SPECIFIC" = true ]; then
      echo "  - Moving to platform-specific directory: wheels/py${PYVER}-${CURRENT_PLATFORM}/"
      mv "$wheel" "wheels/py${PYVER}-${CURRENT_PLATFORM}/"
    else
      echo "  - Copying to version-specific directory: wheels/py${PYVER}/"
      cp "$wheel" "wheels/py${PYVER}/"
      echo "  - Moving to platform-specific directory: wheels/py${PYVER}-${CURRENT_PLATFORM}/"
      mv "$wheel" "wheels/py${PYVER}-${CURRENT_PLATFORM}/"
    fi
  # Check for ABI-stable wheels (cp3X-abi3, cp3Y-abi3)
  elif [[ "$wheel" == *"cp3"*"-abi3"* ]]; then
    # ABI3 wheels are compatible with all future Python versions
    # Determine minimum Python version
    if [[ "$wheel" == *"cp36-abi3"* ]]; then
      MIN_VERSION=6
    elif [[ "$wheel" == *"cp37-abi3"* ]]; then
      MIN_VERSION=7
    elif [[ "$wheel" == *"cp38-abi3"* ]]; then
      MIN_VERSION=8
    elif [[ "$wheel" == *"cp39-abi3"* ]]; then
      MIN_VERSION=9
    else
      # Default to Python 3.10+ for unknown abi3 wheels
      MIN_VERSION=10
    fi
    
    echo "Processing ABI3 wheel: $(basename $wheel) (min Python 3.$MIN_VERSION)"

    # Determine if this is a platform-specific wheel
    if [[ "$wheel" == *"macosx"* ]] || [[ "$wheel" == *"manylinux"* ]] || [[ "$wheel" == *"win"* ]]; then
      IS_PLATFORM_SPECIFIC=true
    else
      IS_PLATFORM_SPECIFIC=false
    fi
    
    # Copy to all compatible Python versions (both version-specific and platform-specific directories)
    if [ $MIN_VERSION -le 10 ]; then
      echo "  - Copying to wheels/py310/"
      cp "$wheel" wheels/py310/
      echo "  - Copying to wheels/py310-${CURRENT_PLATFORM}/"
      cp "$wheel" "wheels/py310-${CURRENT_PLATFORM}/"
    fi
    if [ $MIN_VERSION -le 11 ]; then
      echo "  - Copying to wheels/py311/"
      cp "$wheel" wheels/py311/
      echo "  - Copying to wheels/py311-${CURRENT_PLATFORM}/"
      cp "$wheel" "wheels/py311-${CURRENT_PLATFORM}/"
    fi
    if [ $MIN_VERSION -le 12 ]; then
      echo "  - Copying to wheels/py312/"
      cp "$wheel" wheels/py312/
      echo "  - Copying to wheels/py312-${CURRENT_PLATFORM}/"
      cp "$wheel" "wheels/py312-${CURRENT_PLATFORM}/"
    fi
    if [ $MIN_VERSION -le 13 ]; then
      echo "  - Copying to wheels/py313/"
      cp "$wheel" wheels/py313/
      echo "  - Copying to wheels/py313-${CURRENT_PLATFORM}/"
      cp "$wheel" "wheels/py313-${CURRENT_PLATFORM}/"
    fi
    
    # Remove original
    rm "$wheel"
  elif [[ "$wheel" == *"py3"* ]] || [[ "$wheel" == *"py2.py3"* ]] || [[ "$wheel" == *"none-any"* ]]; then
    # Pure Python wheels compatible with any version - copy to all dirs
    echo "Copying $(basename $wheel) to all version directories (pure Python wheel)"
    
    # Copy to all version-specific directories
    cp "$wheel" wheels/py310/
    cp "$wheel" wheels/py311/
    cp "$wheel" wheels/py312/
    cp "$wheel" wheels/py313/
    
    # Copy to all platform-specific directories
    cp "$wheel" "wheels/py310-${CURRENT_PLATFORM}/"
    cp "$wheel" "wheels/py311-${CURRENT_PLATFORM}/"
    cp "$wheel" "wheels/py312-${CURRENT_PLATFORM}/"
    cp "$wheel" "wheels/py313-${CURRENT_PLATFORM}/"
    
    rm "$wheel"
  else
    echo "Unknown Python version for $(basename $wheel), leaving in root directory"
  fi
done

# Create manifest files in version-specific directories
for dir in wheels/py{310,311,312,313}; do
  WHEEL_COUNT=$(find "$dir" -name "*.whl" | wc -l)
  SQLALCHEMY_WHEEL=$(find "$dir" -name "sqlalchemy*.whl" 2>/dev/null || echo "Not found")
  
  echo "Python Version: ${dir#wheels/py}" > "$dir/manifest.txt"
  echo "Platform: generic (cross-platform)" >> "$dir/manifest.txt"
  echo "Wheel Count: $WHEEL_COUNT" >> "$dir/manifest.txt"
  echo "Date: $(date)" >> "$dir/manifest.txt"
  echo "SQLAlchemy: ${SQLALCHEMY_WHEEL##*/}" >> "$dir/manifest.txt"
done

# Create manifest files in platform-specific directories
for dir in wheels/py{310,311,312,313}-${CURRENT_PLATFORM}; do
  WHEEL_COUNT=$(find "$dir" -name "*.whl" | wc -l)
  SQLALCHEMY_WHEEL=$(find "$dir" -name "sqlalchemy*.whl" 2>/dev/null || echo "Not found")
  
  # Extract Python version
  PYVER=${dir#wheels/py}
  PYVER=${PYVER%-*}
  
  echo "Python Version: $PYVER" > "$dir/manifest.txt"
  echo "Platform: ${CURRENT_PLATFORM}" >> "$dir/manifest.txt"
  echo "OS Type: $OS_TYPE" >> "$dir/manifest.txt"
  echo "Architecture: $ARCH" >> "$dir/manifest.txt"
  echo "Wheel Count: $WHEEL_COUNT" >> "$dir/manifest.txt"
  echo "Date: $(date)" >> "$dir/manifest.txt"
  echo "SQLAlchemy: ${SQLALCHEMY_WHEEL##*/}" >> "$dir/manifest.txt"
  
  # Create a .platform file to make it easier for scripts to identify the platform
  echo "$CURRENT_PLATFORM" > "$dir/.platform"
done

echo "Wheel organization complete."
echo "Version-specific directories: wheels/py{310,311,312,313}"
echo "Platform-specific directories: wheels/py{310,311,312,313}-${CURRENT_PLATFORM}"
echo "Remember to commit all wheel directories to the repository for offline installation."