#!/usr/bin/env python3

import unittest

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

import eremitalpa as ere


class TestMultipleSequenceAlignmentVariableSites(unittest.TestCase):
    """
    Tests for eremitalpa.MultipleSequenceAlignment.variable_sites
    """

    def test_no_variable_sites(self):
        """
        If there are no variable sites in a multiple sequence alignment, variable_sites
        should return an empty generator.
        """
        msa = ere.MultipleSequenceAlignment([SeqRecord(Seq("atcg")) for _ in range(5)])
        self.assertEqual((), tuple(msa.variable_sites()))

    def test_one_variable_site(self):
        """
        Test a single variable site.
        """
        msa = ere.MultipleSequenceAlignment(
            [
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcc")),
            ]
        )
        vs = tuple(msa.variable_sites())
        self.assertEqual(1, len(vs))

    def test_variable_sites_contain_Column_instances(self):
        """
        Variable sites should be Column instances.
        """
        msa = ere.MultipleSequenceAlignment(
            [
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcc")),
            ]
        )
        column = next(msa.variable_sites())
        self.assertIsInstance(column, ere.eremitalpa.Column)

    def test_column_site(self):
        """
        Site should be 1-indexed.
        """
        msa = ere.MultipleSequenceAlignment(
            [
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcc")),
            ]
        )
        column = next(msa.variable_sites())
        self.assertEqual(4, column.site)

    def test_min_2nd_most_freq_2_casea(self):
        """
        In this test case, passing min_2nd_most_freq=2 should exclude all columns.
        """
        msa = ere.MultipleSequenceAlignment(
            [
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcg")),
                SeqRecord(Seq("atcc")),
            ]
        )
        vs = tuple(msa.variable_sites(min_2nd_most_freq=2))
        self.assertEqual(0, len(vs))

    def test_min_2nd_most_freq_2_caseb(self):
        """
        Here, passing min_2nd_most_freq=2 should yield only a single column.
        """
        msa = ere.MultipleSequenceAlignment(
            [
                SeqRecord(Seq("atcga")),
                SeqRecord(Seq("atcga")),
                SeqRecord(Seq("atcgt")),
                SeqRecord(Seq("atcct")),
            ]
        )
        vs = tuple(msa.variable_sites(min_2nd_most_freq=2))
        self.assertEqual(1, len(vs))


class TestTreeDistanceBetween(unittest.TestCase):
    """
    Tests for eremitalpa.Tree.distance_between

    Test tree, (A:2,(B:1,C:2):0.5):0;:

    ------------------2------------------- A
    +
    |        ----------1-------- B
    ----0.5--+
             ---------------------2----------------- C

    """

    def setUp(self):
        self.tree_string = "(A:2,(B:1,C:2):0.5):0;"
        self.tree = ere.Tree.get(data=self.tree_string, schema="newick")
        self.a_node = self.tree.find_node_with_taxon_label("A")
        self.b_node = self.tree.find_node_with_taxon_label("B")
        self.c_node = self.tree.find_node_with_taxon_label("C")
        self.root, self.internal = self.tree.internal_nodes()

    def test_distance_between_parent_and_child(self):
        """
        Test distance calculation between parent and child nodes
        """
        distance = self.tree.distance_between(self.root, self.a_node)
        self.assertEqual(distance, 2.0)

    def test_distance_between_b_c(self):
        """
        Test distance calculation between b and c.
        """
        distance = self.tree.distance_between(self.b_node, self.c_node)
        self.assertEqual(distance, 3)

    def test_distance_between_a_c(self):
        """
        Test distance calculation between a and c.
        """
        distance = self.tree.distance_between(self.a_node, self.c_node)
        self.assertEqual(distance, 4.5)

    def test_distance_to_self(self):
        """
        Test that distance to self is zero
        """
        distance = self.tree.distance_between(self.a_node, self.a_node)
        self.assertEqual(distance, 0.0)

    def test_distance_symmetry(self):
        """
        Test that distance is symmetric
        """
        distance_ab = self.tree.distance_between(self.a_node, self.b_node)
        distance_ba = self.tree.distance_between(self.b_node, self.a_node)
        self.assertEqual(distance_ab, distance_ba)

    def test_distance_between_internal_nodes(self):
        """
        Test distance calculation between internal nodes
        """
        distance = self.tree.distance_between(self.root, self.internal)
        self.assertEqual(distance, 0.5)


class TestFindClosestLeafNode(unittest.TestCase):
    """
    Tests for eremitalpa.Tree.find_closest_leaf_node

    Test tree, (A:2,(B:1,C:2):0.5):0;:

    ------------------2------------------- A
    +
    |        ----------1-------- B
    ----0.5--+
             ---------------------2----------------- C
    """

    def setUp(self):
        self.tree_string = "(A:2,(B:1,C:2):0.5):0;"
        self.tree = ere.Tree.get(data=self.tree_string, schema="newick")

    def test_find_closest_leaf_node_from_root(self):
        """
        Test finding closest leaf node from root. In this tree, B is closest to
        root.
        """
        root = self.tree.seed_node
        closest = self.tree.find_closest_leaf_node(root)
        self.assertEqual(closest.taxon.label, "B")

    def test_find_closest_leaf_node_from_internal(self):
        """
        Test finding closest leaf node from internal node.
        """
        internal_node = self.tree.internal_nodes()[1]  # first internal is the seed node
        closest = self.tree.find_closest_leaf_node(internal_node)
        self.assertEqual(closest.taxon.label, "B")

    def test_find_closest_leaf_node_from_leaf(self):
        """
        Test finding closest leaf node when starting from a leaf node. Should
        return itself.
        """
        leaf_node = self.tree.find_node_with_taxon_label("A")
        closest = self.tree.find_closest_leaf_node(leaf_node)
        self.assertEqual(closest, leaf_node)

    def test_find_closest_leaf_node_equidistant(self):
        """
        Test with a tree where leaves are equidistant from an internal node.
        Should return one of the equidistant leaves.
        """
        equidistant_tree = ere.Tree.get(data="(A:1,B:1,C:1):0;", schema="newick")
        root = equidistant_tree.seed_node
        closest = equidistant_tree.find_closest_leaf_node(root)
        self.assertIn(closest.taxon.label, ["A", "B", "C"])

    def test_case_where_closest_node_is_from_ancestor(self):
        """
        In this case the closest leaf is 'behind' the internal node.

        ---- A
        +
        |   -------------------------------------------- B
        ----+
            -------------------------------------------- C
        """
        tree = ere.Tree.get(data="(A:0.1,(B:1,C:1):0.1):0;", schema="newick")
        _, internal_node = tree.internal_nodes()
        assert not internal_node == tree.seed_node
        closest = tree.find_closest_leaf_node(internal_node)
        self.assertEqual(closest.taxon.label, "A")

    def test_tree_with_one_node(self):
        """
        Test with a tree that only has one node
        """
        tree = ere.Tree.get(data="A;", schema="newick")
        root = tree.seed_node
        closest = tree.find_closest_leaf_node(root)
        self.assertEqual(closest.taxon.label, "A")

    def test_tree_with_zero_branch_lengths(self):
        """
        Test with a tree that has zero branch lengths
        """
        tree = ere.Tree.get(data="(A:0,(B:0,C:0):0);", schema="newick")
        root = tree.seed_node
        closest = tree.find_closest_leaf_node(root)
        self.assertIn(closest.taxon.label, ["A", "B", "C"])

    def test_bigger_tree(self):
        """
        Test with a bigger tree.

                   -- A
        -----------+E
        |          ----- B
        +
        |                 ------- C
        ------------------+H
                          |               --------- D
                          ----------------+G
                                          -------------- F
        """
        tree = ere.Tree.get(
            data="((A:0.1,B:0.2)E:0.5,(C:0.3,(D:0.4,F:0.6)G:0.7)H:0.8);",
            schema="newick",
        )
        g_node = tree.find_node_with_label("G")
        closest = tree.find_closest_leaf_node(g_node)
        self.assertEqual(closest.taxon.label, "D")


if __name__ == "__main__":
    unittest.main()
