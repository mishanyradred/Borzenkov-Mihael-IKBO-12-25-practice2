"""Verify D2 edges and cycle-aware ASCII output."""

import unittest

from src.render import ascii_tree, d2_source


class RenderTests(unittest.TestCase):
    """Exercise visualization source generation."""

    def test_cycle(self):
        a, b = ("A", None), ("B", None)
        graph = {a: (b,), b: (a,)}
        self.assertEqual(ascii_tree(graph), "A\n`-- B\n    `-- A [seen]")
        self.assertEqual(
            d2_source(graph),
            'direction: right\np0: "A"\np1: "B"\np0 -> p1\np1 -> p0\n',
        )

    def test_empty(self):
        self.assertEqual(ascii_tree({}), "(empty graph)")
        self.assertEqual(d2_source({}), "direction: right\n")
