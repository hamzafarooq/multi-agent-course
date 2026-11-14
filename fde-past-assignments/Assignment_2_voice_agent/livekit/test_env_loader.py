"""Regression tests for LiveKit environment-file loading."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from env_loader import load_env_files, parse_env_value


class ParseEnvValueTests(unittest.TestCase):
    def test_inline_comment_is_not_part_of_api_key(self):
        self.assertEqual(
            parse_env_value("sk-proj-secret  # OpenAI API key"),
            "sk-proj-secret",
        )

    def test_hash_inside_quoted_value_is_preserved(self):
        self.assertEqual(parse_env_value("'say # aloud' # comment"), "say # aloud")

    def test_blank_value_remains_blank(self):
        self.assertEqual(parse_env_value("   # optional override"), "")


class LoadEnvFilesTests(unittest.TestCase):
    def test_exported_value_wins_over_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("WORKSHOP_TEST_KEY=file-value\n", encoding="utf-8")
            with patch.dict(os.environ, {"WORKSHOP_TEST_KEY": "shell-value"}):
                load_env_files([path])
                self.assertEqual(os.environ["WORKSHOP_TEST_KEY"], "shell-value")


if __name__ == "__main__":
    unittest.main()
