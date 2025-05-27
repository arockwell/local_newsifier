# Platform-Specific Wheel Directory Reorganization

## Current Issues

1. **Mixed Architecture Wheels**: The `linux-x86_64` directory contains 16 aarch64 wheels that should be in a separate directory
2. **Non-Standard Naming**: Directory `linux-x86_64` should be `py312-linux-x86_64` to match the convention
3. **Incomplete Platform Support**: Missing several platform combinations

## Current Structure
```
wheels/
├── linux-x86_64/        # Mixed x86_64 and aarch64 wheels (287 files)
├── py312/               # Cross-platform wheels (220 files)
├── py312-linux-arm64/   # Linux ARM64 (only 12 files)
├── py312-linux-x64/     # Linux x64 (288 files) - duplicate?
├── py312-macos-arm64/   # macOS ARM64 (260 files)
└── py313-macos-arm64/   # Python 3.13 (only 3 files)
```

## Proposed Structure
```
wheels/
├── py312/               # Cross-platform pure Python wheels
├── py312-linux-x86_64/  # Linux x86_64 specific wheels
├── py312-linux-aarch64/ # Linux ARM64/aarch64 specific wheels
├── py312-macos-x86_64/  # macOS Intel specific wheels
└── py312-macos-arm64/   # macOS Apple Silicon specific wheels
```

## Action Plan

### 1. Clean up linux-x86_64 directory
- Move aarch64 wheels to `py312-linux-aarch64/`
- Rename directory to `py312-linux-x86_64/`

### 2. Consolidate duplicate directories
- Check if `py312-linux-x64` is identical to `linux-x86_64`
- Merge and remove duplicates

### 3. Standardize naming
- Use consistent naming: `py{version}-{os}-{arch}`
- OS: linux, macos, windows
- Arch: x86_64, aarch64, arm64

### 4. Update build scripts
- Ensure scripts create correct directory names
- Add validation to prevent mixed architectures

## Wheel Categories

### Pure Python Wheels (any platform)
These go in `py312/`:
- Files ending in `-py3-none-any.whl`
- Files ending in `-py2.py3-none-any.whl`

### Platform-Specific Wheels
These go in `py312-{os}-{arch}/`:
- Files with `manylinux` in the name
- Files with `macosx` in the name
- Files with `win` in the name
- Files with specific architecture tags (cp312-cp312-...)

## Migration Commands

```bash
# Create proper directories
mkdir -p wheels/py312-linux-aarch64

# Move aarch64 wheels from linux-x86_64
cd wheels/linux-x86_64
for wheel in *aarch64*.whl; do
    mv "$wheel" ../py312-linux-aarch64/
done

# Rename linux-x86_64 to py312-linux-x86_64
cd ..
mv linux-x86_64 py312-linux-x86_64

# Check for duplicates between py312-linux-x64 and py312-linux-x86_64
diff -r py312-linux-x64 py312-linux-x86_64
```
