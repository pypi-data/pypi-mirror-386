import os
import sys
import unittest

from nextpipe.graph import check_cycle

# Add the parent directory to the sys.path to allow imports from the main package. This
# is meant to help VS Code testing features.
sys.path.append(os.path.dirname(sys.path[0]))


class TestGraph(unittest.TestCase):
    def test_check_cycle(self):
        # Test for a simple DAG with no cycles
        node_successors = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": ["E"],
            "E": [],
        }
        has_cycle, faulty_nodes = check_cycle(node_successors)
        self.assertFalse(has_cycle)
        self.assertIsNone(faulty_nodes)

        # Test for a simple DAG with a cycle
        node_successors = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
        }
        has_cycle, faulty_nodes = check_cycle(node_successors)
        self.assertTrue(has_cycle)
        self.assertCountEqual(faulty_nodes, ["A", "B", "C"])

        # Test
        node_successors = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": ["E"],
            "E": ["A"],
        }
        has_cycle, faulty_nodes = check_cycle(node_successors)
        self.assertTrue(has_cycle)
        self.assertCountEqual(faulty_nodes, ["A", "B", "C", "D", "E"])
