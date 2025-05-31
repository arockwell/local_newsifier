# Fix Linter Gameplan

## Overview
We have 4,453 linting issues across the codebase that need to be addressed. This plan provides a systematic approach to fixing these issues, prioritized by severity and impact.

## Current Issue Summary

### Critical Issues (Fix First)
1. **F821 - Undefined names (7 issues)**: These can cause runtime errors
2. **F811 - Redefinition of unused imports (153 issues)**: Conflicting imports
3. **E722 - Bare except (2 issues)**: Security and debugging concerns

### High Priority Issues
1. **F401 - Unused imports (376 issues)**: Clean up imports
2. **E501 - Line too long (290 issues)**: Code readability
3. **F841 - Unused variables (22 issues)**: Code cleanliness

### Medium Priority Issues
1. **W293 - Blank lines with whitespace (3,038 issues)**: Most common issue
2. **W291 - Trailing whitespace (253 issues)**: Formatting
3. **W292 - No newline at end of file (62 issues)**: File formatting

### Lower Priority Issues
1. **D*** - Documentation/docstring issues (~50 issues)**: Documentation
2. **E302/E303/E305 - Blank line issues (84 issues)**: Formatting
3. **Other E*** issues**: Various style violations

## Step-by-Step Fix Process

### Phase 1: Automated Fixes (Quick Wins)
1. **Remove trailing whitespace and blank line issues**
   ```bash
   # This will fix W291, W292, W293, and W391
   poetry run black src tests
   poetry run isort src tests
   ```

2. **Fix line length issues automatically where possible**
   ```bash
   # Black will handle most E501 issues
   poetry run black src tests --line-length 100
   ```

### Phase 2: Critical Manual Fixes
1. **Fix undefined names (F821)**
   - Search for each undefined name
   - Add proper imports or fix typos
   - Priority files: Check services and tools modules

2. **Fix bare except clauses (E722)**
   - Replace with specific exception types
   - Add proper error handling

3. **Fix import issues (F811, F401)**
   - Remove duplicate imports
   - Remove unused imports
   - Use isort to organize imports properly

### Phase 3: Semi-Automated Fixes
1. **Create a script to fix common issues**
   ```python
   # scripts/fix_linting.py
   - Remove unused variables (F841)
   - Fix comparison issues (E711, E712)
   - Replace lambda assignments with def (E731)
   ```

2. **Fix docstring issues**
   - Add missing docstrings for public modules/classes/methods
   - Fix docstring formatting

### Phase 4: Module-by-Module Cleanup
1. **Start with core modules**
   - `src/local_newsifier/models/`
   - `src/local_newsifier/database/`
   - `src/local_newsifier/config/`

2. **Then service modules**
   - `src/local_newsifier/services/`
   - `src/local_newsifier/crud/`

3. **Then API and CLI**
   - `src/local_newsifier/api/`
   - `src/local_newsifier/cli/`

4. **Finally tests**
   - `tests/`

## Implementation Strategy

### Day 1: Automated Fixes
- [ ] Run black and isort to fix formatting issues
- [ ] Commit automated fixes
- [ ] Re-run linter to see remaining issues

### Day 2: Critical Issues
- [ ] Fix all F821 (undefined names)
- [ ] Fix all E722 (bare except)
- [ ] Fix duplicate imports (F811)
- [ ] Create script for semi-automated fixes

### Day 3-4: Import Cleanup
- [ ] Remove all unused imports (F401)
- [ ] Organize imports with isort
- [ ] Fix any circular import issues

### Day 5-6: Code Quality
- [ ] Fix unused variables (F841)
- [ ] Fix comparison issues (E711, E712)
- [ ] Fix lambda assignments (E731)
- [ ] Fix line length issues not handled by black

### Day 7: Documentation
- [ ] Add missing docstrings
- [ ] Fix docstring formatting
- [ ] Ensure all public APIs are documented

## Testing Protocol
After each phase:
1. Run the full test suite: `make test`
2. Run linter to verify fixes: `make lint`
3. Check for any new issues introduced
4. Commit changes with descriptive messages

## Success Metrics
- Zero F*** (flake8) errors
- Zero E*** errors (except E501 where necessary)
- Minimal W*** warnings
- All tests passing
- Documentation coverage >80%

## Tools and Commands

### Useful Commands
```bash
# Count specific issue types
poetry run flake8 src tests --select=F821 --count

# Fix imports automatically
poetry run isort src tests

# Format code
poetry run black src tests

# Check specific file
poetry run flake8 path/to/file.py

# Run with specific ignores
poetry run flake8 src tests --ignore=D,W293
```

### Flake8 Configuration
Consider adding `.flake8` configuration:
```ini
[flake8]
max-line-length = 100
extend-ignore = D203, D212, W503
exclude = .git,__pycache__,build,dist
per-file-ignores =
    __init__.py:F401
    conftest.py:F401,F811
```

## Notes
- Some docstring warnings (D***) may be optional depending on project standards
- W503 (line break before binary operator) conflicts with W504 and is often ignored
- Consider using pre-commit hooks to prevent future issues
