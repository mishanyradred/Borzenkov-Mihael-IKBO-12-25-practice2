"""Check exact-version lookup against representative npm metadata."""

import unittest
from unittest.mock import patch

from src.registry import NpmRegistry


class RegistryTests(unittest.TestCase):
    """Exercise direct dependency extraction and caching."""

    def test_exact_version(self):
        registry = NpmRegistry("https://registry.npmjs.org")
        document = {"versions": {
            "1.0.0": {"dependencies": {"left": "^1.0.0"}},
            "2.0.0": {
                "dependencies": {"right": "~2.0.0"},
                "optionalDependencies": {"right": "~3.0.0"},
            },
        }}
        with patch.object(registry, "fetch", return_value=document) as fetch:
            self.assertEqual(
                registry.dependencies(("example", "1.0.0")),
                {"left": "^1.0.0"},
            )
            self.assertEqual(
                registry.dependencies(("example", "2.0.0")),
                {"right": "~3.0.0"},
            )
            with self.assertRaisesRegex(ValueError, "version not found"):
                registry.dependencies(("example", "3.0.0"))
        fetch.assert_called_once_with("example")
