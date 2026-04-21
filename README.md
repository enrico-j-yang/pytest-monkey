# pytest-monkey

A pytest plugin and CLI tool for running tests multiple times in random order, supporting reproducible random test runs. Similar to the Android monkey tool. Normal pytest runs all test cases sequentially once. This tool randomly runs tests a specified number of times (e.g., 10000), stopping on failure (configurable to continue). Each run prints a random seed value, allowing you to reproduce the same test order by specifying the seed.

## Features

- **Random Order Execution**: Randomly select and run tests multiple times from a test collection
- **Reproducible Runs**: Ensure test order reproducibility via seed parameter
- **pytest Plugin Mode**: Seamlessly integrate as a pytest plugin
- **Standalone CLI Tool**: Use independently as a command-line tool
- **Detailed Reports**: Automatically generate JSON and HTML format test reports
- **Failure Control**: Support continuing execution or stopping immediately on failure

## Installation

```bash
pip install pytest-monkey
```

Or using PDM:

```bash
pdm install
```

## Usage

### 1. As pytest Plugin

Add `--random-runner` option to pytest command:

```bash
# Basic usage - run 100 random tests
pytest tests/ --random-runner --random-count 100

# Specify seed to reproduce test order
pytest tests/ --random-runner --random-count 100 --random-seed 42

# Continue on failure
pytest tests/ --random-runner --random-count 100 --random-continue-on-fail

# Show test output (similar to pytest -s)
pytest tests/ --random-runner --random-count 100 --random-no-capture
```

### 2. As CLI Tool

Run `random_runner.py` directly:

```bash
# Run 100 random tests from directory
python random_runner.py tests/ --count 100

# Run 50 tests from single file
python random_runner.py tests/test_file.py --count 50

# Specify test method and set seed
python random_runner.py tests/test_file.py::test_name --count 20 --seed 42

# Continue on failure, verbose output
python random_runner.py tests/ --count 100 --continue-on-fail -v

# Show test output (similar to pytest -s)
python random_runner.py tests/ --count 100 -s
```

## Parameter Reference

### pytest Plugin Parameters

| Parameter | Description |
|-----------|-------------|
| `--random-runner` | Enable random test run mode |
| `--random-count` | Number of test runs (required) |
| `--random-seed` | Random seed (auto-generated 10-digit number by default) |
| `--random-continue-on-fail` | Continue execution on failure |
| `--random-no-capture` | Disable output capture, show test output |

### CLI Parameters

| Parameter | Description |
|-----------|-------------|
| `test_spec` | Test target (file/class/method/directory path) |
| `--count` | Number of test runs (required) |
| `--seed` | Random seed (auto-generated 10-digit number by default) |
| `--continue-on-fail` | Continue execution on failure |
| `--report-dir` | Report save directory (default ./reports) |
| `-v, --verbose` | Verbose output mode |
| `-s, --no-capture` | Disable output capture |

## Test Reports

Two reports are automatically generated after each run:

- **JSON Report**: `reports/report.json`
- **HTML Report**: `reports/report.html`

Reports include:
- Random seed
- Total runs, pass/fail statistics
- Detailed results for each test (name, duration, error message)
- Run timestamp

## Reproducing Tests

Random seed is printed during run, for example:

```
Random seed: 1234567890
```

Use the same seed to reproduce the same test order:

```bash
python random_runner.py tests/ --count 100 --seed 1234567890
```

## Test Selection Syntax

Supports pytest standard selection syntax:

- File: `tests/test_xxx.py`
- Class: `tests/test_xxx.py::TestClass`
- Method: `tests/test_xxx.py::TestClass::test_method`
- Directory: `tests/`

## Development

### Project Structure

```
pytest-monkey/
├── runner/
│   ├── core.py       # Core runner
│   ├── collector.py  # Test collector
│   ├── selector.py   # Random selector
│   ├── executor.py   # Test executor
│   ├── reporter.py   # Report generator
│   └── models.py     # Data models
├── pytest_random_runner.py  # pytest plugin entry
├── random_runner.py         # CLI entry
└── tests/                   # Test files
```

### Running Tests

```bash
pytest tests/
```

## License

MIT License