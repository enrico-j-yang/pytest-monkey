# Agent Configuration Guide

This document provides working guidelines for AI assistants on the pytest-monkey project.

## Project Overview

pytest-monkey is a pytest plugin and CLI tool for running tests multiple times in random order. Core features:

- Randomly select and run tests multiple times from a test collection
- Ensure test order reproducibility via seed parameter
- Automatically generate JSON/HTML test reports

## Tech Stack

- Python 3.12
- pytest (test framework)
- tqdm (progress bar)
- PDM (package management)

## Project Structure

```
pytest-monkey/
├── runner/               # Core module
│   ├── core.py          # RunnerCore - integrates all components
│   ├── collector.py     # TestCollector - collects pytest test items
│   ├── selector.py      # RandomSelector - randomly selects tests
│   ├── executor.py      # TestExecutor - executes single tests
│   ├── reporter.py      # ResultReporter - generates reports
│   └── models.py        # Data models (TestResult, RunReport)
├── pytest_monkey.py          # pytest plugin entry
├── random_runner.py         # CLI entry
├── tests/                   # Test directory
└── reports/                 # Report output directory (generated at runtime)
```

## Development Guidelines

### Coding Style

- Use English comments and docstrings
- Use dataclass for data model definitions
- Add type annotations to functions and classes
- Keep module responsibilities single and focused

### Testing Requirements

- All new features must have corresponding unit tests
- Test files go in `tests/test_runner/` directory
- Write tests using pytest
- Run tests: `pytest tests/`

### Code Quality Checks

**Mandatory Rule**: After modifying pytest scripts, run the following pylint check:

```bash
pylint --rcfile=.pylintrc --output-format=parseable --disable=R -rn .
```

Fix all errors reported by pylint until the score reaches 10.

### Core Component Interaction

RunnerCore is the central coordinator, working in this order:

1. TestCollector.collect() → Collect test items
2. RandomSelector.select() → Select random sequence
3. TestExecutor.execute() → Execute each test
4. ResultReporter → Record results, generate report

When modifying any component, ensure interface compatibility with RunnerCore.

## Common Tasks

### Adding New Features

1. Implement feature in corresponding module
2. Update RunnerCore (if integration needed)
3. Update CLI/plugin parameters (random_runner.py, pytest_monkey.py)
4. Write unit tests
5. Update README.md

### Modifying Report Format

- Modify `generate_html()` or `generate_json()` in `runner/reporter.py`
- Ensure data comes from `RunReport` in `runner/models.py`

### Adding New Selection Strategies

- Extend RandomSelector in `runner/selector.py`
- Or create new selector class, replace in RunnerCore

## Notes

- Test execution uses pytest.main() internal mechanism, ensure correct test context
- Random seed defaults to 10-digit number for easy reproduction
- Report directory defaults to `./reports`, auto-created before running