# Claude Code Configuration

This project is a pytest random test runner plugin.

## Project Guide

For detailed development guidelines and project structure, see [AGENTS.md](AGENTS.md).

## Quick Commands

```bash
# Run tests
pytest tests/

# Run random tests (CLI)
python random_runner.py tests/ --count 10

# Run random tests (pytest plugin)
pytest tests/ --random-runner --random-count 10
```

## Key Files

- `runner/core.py` - Core runner
- `pytest_random_runner.py` - pytest plugin entry
- `random_runner.py` - CLI entry
- `tests/test_runner/` - Unit tests