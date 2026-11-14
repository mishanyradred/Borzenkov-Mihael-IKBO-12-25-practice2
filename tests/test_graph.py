"""Check breadth-first discovery, cycles and pruning."""

from pathlib import Path
import unittest

from src.fixture import load_fixture
from src.graph import build_graph, label

FIXTURE = Path(__file__).parent / "fixtures" / "repository.json"


class GraphTests(unittest.TestCase):
    """Exercise graph operations using a versionless test repository."""

    def setUp(self):
        self.fixture = load_fixture(FIXTURE)
        self.root = ("A", None)

    def graph(self, depth=None, exclude=None):
        return build_graph(self.root, self.fixture.__getitem__, depth, exclude)

    def test_cycle_and_shared_node(self):
        graph = self.graph()
        self.assertEqual(list(map(label, graph)), list("ABCDE"))
        self.assertEqual(graph[("D", None)], (self.root,))

    def test_depth(self):
        self.assertEqual(list(map(label, self.graph(0))), ["A"])
        graph = self.graph(1)
        self.assertEqual(list(map(label, graph)), list("ABC"))
        self.assertEqual(graph[("C", None)], ())

    def test_filter_prunes_paths(self):
        self.assertEqual(list(map(label, self.graph(exclude="C"))), list("ABD"))
        self.assertEqual(self.graph(exclude="A"), {})

    def test_isolated_package(self):
        root = ("G", None)
        self.assertEqual(
            build_graph(root, self.fixture.__getitem__), {root: ()}
        )
