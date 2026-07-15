"""Tests for the pytest-monkey CLI."""
from unittest.mock import patch

import random_runner


def test_main_enables_verbose_visible_output_by_default(monkeypatch):
    """The CLI should show pytest output and run details without extra flags."""
    monkeypatch.setattr(
        "sys.argv",
        ["pytest-monkey", "tests/", "--count", "1"],
    )

    with patch("random_runner.RunnerCore") as runner_core:
        runner_core.return_value.run.return_value = 0

        assert random_runner.main() == 0

    assert runner_core.call_args.kwargs["verbose"] is True
    assert runner_core.call_args.kwargs["capture_output"] is False
