"""Check invalid values for all CLI settings."""

from contextlib import redirect_stderr
from io import StringIO
import unittest

from src.cli import parse_args

BASE = [
    "--package", "is-odd",
    "--repository", "https://registry.npmjs.org",
    "--version", "3.0.1",
]


class CliTests(unittest.TestCase):
    """Exercise configuration parsing."""

    def test_defaults(self):
        options = parse_args(BASE)
        self.assertEqual(options.version, "3.0.1")
        self.assertIsNone(options.max_depth)

    def test_invalid_settings(self):
        invalid = [
            ["--package", "../odd"],
            ["--repository", "file:///tmp/index"],
            ["--test=false"],
            ["--test"],
            ["--version", "^3.0.1"],
            ["--ascii=false"],
            ["--max-depth", "-1"],
            ["--exclude", " "],
        ]
        for flags in invalid:
            with self.subTest(flags=flags), redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as error:
                    parse_args(BASE + flags)
                self.assertEqual(error.exception.code, 2)
