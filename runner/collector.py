"""TestCollector - pytest test item collector"""
import sys
from io import StringIO
from pathlib import Path
from typing import List, Optional

import pytest


class TestCollector:
    """Collect pytest test items from various test specifications"""

    def __init__(self, root_dir: Optional[str] = None):
        """
        Initialize TestCollector.

        Args:
            root_dir: Root directory for test collection. Defaults to current working directory.
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()

    def _validate_path(self, test_spec: str) -> Path:
        """
        Check if the test specification path exists.

        Args:
            test_spec: Test specification string (file/class/method/directory path)

        Returns:
            Path object if valid

        Raises:
            ValueError: If path does not exist
        """
        # Extract the file/directory path from the test spec
        # Handle pytest selection syntax: path::Class::method
        path_part = test_spec.split("::")[0]

        # Resolve path relative to root_dir
        full_path = self.root_dir / path_part

        if not full_path.exists():
            raise ValueError(f"Path does not exist: {path_part}")

        return full_path

    def collect(self, test_spec: str) -> List[pytest.Item]:
        """
        Collect pytest test items from a test specification.

        Supports pytest selection syntax:
        - File: tests/test_xxx.py
        - Class: tests/test_xxx.py::TestClass
        - Method: tests/test_xxx.py::TestClass::test_method
        - Directory: tests/

        Args:
            test_spec: Test specification string

        Returns:
            List of pytest.Item objects

        Raises:
            ValueError: If path does not exist or no tests found
        """
        # Validate path first
        self._validate_path(test_spec)

        # Create pytest config with --collect-only
        args = ["--collect-only", "-q", "--no-header", test_spec]

        # Suppress output during collection
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_cout = sys.cout if hasattr(sys, 'cout') else None
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        collected_items: List[pytest.Item] = []

        class CollectionPlugin:
            """Plugin to capture collected items"""
            def pytest_collection_modifyitems(self, _config, items):
                collected_items.extend(items)

        try:
            # Run pytest with our plugin to capture items
            pytest.main(
                args,
                plugins=[CollectionPlugin()]
            )

            if len(collected_items) == 0:
                raise ValueError(f"No tests found for: {test_spec}")

            return collected_items

        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            if old_cout:
                sys.cout = old_cout

    def get_item_names(self, items: List[pytest.Item]) -> List[str]:
        """
        Get list of test node IDs from collected items.

        Args:
            items: List of pytest.Item objects

        Returns:
            List of test nodeid strings
        """
        return [item.nodeid for item in items]