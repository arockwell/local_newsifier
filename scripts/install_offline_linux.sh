#!/bin/bash
# Install local-newsifier offline from pre-built wheels (Linux x86_64 only)

set -e

echo "=== Local Newsifier Offline Installation (Linux x86_64) ==="
echo

# Check if we're on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This script is for Linux x86_64 systems only."
    echo "Current OS: $OSTYPE"
    exit 1
fi

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" != "x86_64" ]]; then
    echo "Error: This script is for x86_64 architecture only."
    echo "Current architecture: $ARCH"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ ! "$PYTHON_VERSION" =~ ^3\.(10|11|12)$ ]]; then
    echo "Error: Python 3.10, 3.11, or 3.12 is required."
    echo "Current Python version: $PYTHON_VERSION"
    exit 1
fi

echo "System check passed:"
echo "  - OS: Linux"
echo "  - Architecture: x86_64"
echo "  - Python: $PYTHON_VERSION"
echo

# Define paths
WHEEL_DIR="wheels/linux-x86_64"
REQUIREMENTS="$WHEEL_DIR/requirements.txt"

# Check if wheel directory exists
if [ ! -d "$WHEEL_DIR" ]; then
    echo "Error: Wheel directory not found: $WHEEL_DIR"
    echo "Please ensure you have the pre-built wheels for Linux x86_64."
    exit 1
fi

# Check if requirements file exists
if [ ! -f "$REQUIREMENTS" ]; then
    echo "Error: Requirements file not found: $REQUIREMENTS"
    exit 1
fi

# Count available wheels
WHEEL_COUNT=$(find "$WHEEL_DIR" -name "*.whl" 2>/dev/null | wc -l)
echo "Found $WHEEL_COUNT wheel files in $WHEEL_DIR"
echo

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip to ensure compatibility
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install from wheels
echo
echo "Installing dependencies from offline wheels..."
pip install \
    --no-index \
    --find-links "$WHEEL_DIR" \
    -r "$REQUIREMENTS"

# Install the package itself (without deps since we just installed them)
echo
echo "Installing local-newsifier package..."
pip install --no-deps -e .

# Download spaCy models if needed (this requires internet)
echo
echo "Note: spaCy language models require internet to download."
echo "If offline, you'll need to manually install them later with:"
echo "  python -m spacy download en_core_web_sm"

# Verify installation
echo
echo "Verifying installation..."
if python -c "import local_newsifier" 2>/dev/null; then
    echo "✅ local_newsifier package imported successfully!"
else
    echo "❌ Failed to import local_newsifier package"
    exit 1
fi

# Check if CLI is available
if command -v nf &> /dev/null; then
    echo "✅ CLI command 'nf' is available!"
else
    echo "⚠️  CLI command 'nf' not found in PATH"
    echo "   You may need to run: pip install -e ."
fi

echo
echo "=== Installation Complete! ==="
echo
echo "To use local-newsifier:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the CLI: nf help"
echo "  3. Configure your database and other settings"
echo
echo "For offline spaCy models, you'll need to:"
echo "  1. Download models on a machine with internet"
echo "  2. Use: python -m spacy package en_core_web_sm ./spacy_model"
echo "  3. Install the packaged model offline"
