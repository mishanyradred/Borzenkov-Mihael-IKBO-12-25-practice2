"""Check version selection without using npm libraries."""

import unittest

from src.version import select_version


class VersionTests(unittest.TestCase):
    """Cover supported npm range forms."""

    def test_ranges(self):
        versions = ["0.1.2", "0.2.0", "1.2.0", "1.3.0", "2.0.0-beta"]
        cases = {
            "^0.1.0": "0.1.2",
            "~1.2": "1.2.0",
            "1.x": "1.3.0",
            "0.1 - 0.2": "0.2.0",
            ">= 1.2 < 2": "1.3.0",
            "0.1.2 || >=2.0.0-beta": "2.0.0-beta",
            "*": "1.3.0",
        }
        for expression, expected in cases.items():
            with self.subTest(expression=expression):
                self.assertEqual(select_version(versions, expression), expected)
