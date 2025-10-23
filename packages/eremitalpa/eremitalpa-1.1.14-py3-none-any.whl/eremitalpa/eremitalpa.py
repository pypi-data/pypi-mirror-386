from collections import namedtuple, Counter, defaultdict
from operator import attrgetter, itemgetter
from typing import (
    Optional,
    Generator,
    Iterable,
    Union,
    Literal,
    Any,
    Mapping,
    Callable,
)
import itertools
import logging
import random
import warnings

from Bio import SeqIO, Align
from Bio.SeqRecord import SeqRecord
import dendropy as dp
import matplotlib as mp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .bio import amino_acid_colors, sloppy_translate, find_substitutions
import heapq

# MARKERS
_DEFAULT_MARKER_KWDS = dict(
    color="black", s=0, marker="o", edgecolor="white", lw=0.1, clip_on=False
)
DEFAULT_LEAF_KWDS = dict(zorder=15, **_DEFAULT_MARKER_KWDS)
DEFAULT_INTERNAL_KWDS = dict(zorder=12, **_DEFAULT_MARKER_KWDS)

# EDGES
DEFAULT_EDGE_KWDS = dict(
    color="black", linewidth=0.5, clip_on=False, capstyle="round", zorder=10
)

# LABELS
DEFAULT_LABEL_KWDS = dict(
    horizontalalignment="left",
    verticalalignment="center",
    fontsize=8,
    zorder=15,
)


class Tree(dp.Tree):
    def plot_tree_msa(
        self,
        msa_plot_kwds: Optional[dict] = None,
        axes: Optional[tuple[mp.axes.Axes, mp.axes.Axes]] = None,
    ) -> tuple[mp.axes.Axes, mp.axes.Axes]:
        """Plots the tree and multiple sequence alignment.

        Args:
            msa_plot_kwds (dict, optional): Keyword arguments passed to the
                multiple sequence alignment plot function. Defaults to None.
            axes (tuple[mp.axes.Axes, mp.axes.Axes], optional): A tuple of two
                matplotlib axes to plot on. If None, new axes are created.
                Defaults to None.

        Returns:
            tuple[mp.axes.Axes, mp.axes.Axes]: The matplotlib axes used for
                plotting.
        """
        msa_plot_kwds = {} if msa_plot_kwds is None else msa_plot_kwds

        if axes is None:
            _, axes = plt.subplots(
                ncols=2, figsize=(12, 4), gridspec_kw=dict(wspace=0.7)
            )

        plot_tree(self, ax=axes[0], fill_dotted_lines=True)

        self.multiple_sequence_alignment.plot(
            variable_sites_kwds=msa_plot_kwds.pop(
                "variable_sites_kwds", dict(min_2nd_most_freq=2)
            ),
            rotate_xtick_labels=msa_plot_kwds.pop("rotate_xtick_labels", True),
            **msa_plot_kwds,
            ax=axes[1],
        )

        # Make the ylim of the tree align with the MSA plot
        tree_ylim = axes[0].get_ylim()
        axes[0].set_ylim(tree_ylim[0] + 0.5, tree_ylim[1] - 0.5)

        axes[1].invert_yaxis()

        return axes

    @property
    def multiple_sequence_alignment(self):
        """Generates a MultipleSequenceAlignment object from the tree.

        Leaf nodes on the tree must have 'sequence' attributes and taxon
        labels.

        Returns:
            MultipleSequenceAlignment: The generated alignment object.
        """
        return MultipleSequenceAlignment(
            [
                SeqRecord(node.sequence, description=node.taxon.label)
                for node in self.leaf_nodes()
            ]
        )

    @classmethod
    def from_disk(
        cls,
        path: str,
        schema: str = "newick",
        preserve_underscores: bool = True,
        outgroup: Optional[str] = None,
        msa_path: Optional[str] = None,
        get_kwds: Optional[dict] = None,
        **kwds,
    ) -> "Tree":
        """Loads a tree from a file.

        Args:
            path (str): Path to the file containing the tree.
            schema (str): The schema of the tree file (e.g., "newick").
                See dendropy.Tree.get for options.
            preserve_underscores (bool): If True, preserve underscores in
                taxon labels.
            outgroup (str, optional): The name of the taxon to use as the
                outgroup. Defaults to None.
            msa_path (str, optional): Path to a FASTA file containing leaf
                sequences. Defaults to None.
            get_kwds (dict, optional): Keyword arguments passed to
                dendropy.Tree.get. Defaults to None.
            **kwds: Additional keyword arguments passed to
                add_sequences_to_tree.

        Returns:
            Tree: The loaded tree object.
        """
        get_kwds = {} if get_kwds is None else get_kwds

        get_kwds["preserve_underscores"] = preserve_underscores

        tree = cls.get(path=path, schema=schema, **get_kwds)

        if msa_path:
            add_sequences_to_tree(tree, path=msa_path, **kwds)

        if outgroup is not None:
            og = tree.find_node_with_taxon_label(outgroup)
            tree.reroot_at_edge(og.edge)

        try:
            tree.ladderize(default_order=True)
        except TypeError:
            tree.ladderize()

        return tree

    def clade_bbox(self, taxon_labels: list[str]) -> dict[str, float]:
        """Calculates the bounding box of a clade.

        The bounding box is determined by finding the most recent common
        ancestor (MRCA) of the specified taxa and then calculating the
        minimum and maximum x and y coordinates of its child nodes.

        Args:
            taxon_labels (list[str]): A list of taxon labels that define the
                clade.

        Returns:
            dict[str, float]: A dictionary containing the coordinates of the
                bounding box with keys: 'min_x', 'max_x', 'min_y', 'max_y'.
        """
        mrca = self.mrca(taxon_labels=taxon_labels)
        return {
            "max_x": max(node._x for node in mrca.leaf_iter()),
            "min_x": mrca._x,
            "max_y": max(node._y for node in mrca.leaf_iter()),
            "min_y": min(node._y for node in mrca.leaf_iter()),
        }

    def plot_clade_bbox(
        self,
        taxon_labels: list[str],
        ax: Optional[mp.axes.Axes] = None,
        extend_right: float = 0.0,
        extend_down: float = 0.0,
        label: Optional[str] = None,
        label_kwds: Optional[dict] = None,
        **kwds,
    ):
        """Plots a rectangle around the bounding box of a clade.

        Args:
            taxon_labels (list[str]): A list of taxon labels that define the
                clade.
            ax (mp.axes.Axes, optional): The matplotlib axes to plot on.
                Defaults to None.
            extend_right (float): Amount to extend the box to the right, in
                axes coordinates.
            extend_down (float): Amount to extend the box down, in axes
                coordinates.
            label (str, optional): A label to apply to the box. Defaults to
                None.
            label_kwds (dict, optional): Keyword arguments passed to
                matplotlib.axes.Axes.text. Defaults to None.
            **kwds: Additional keyword arguments passed to
                matplotlib.patches.Rectangle.

        Returns:
            matplotlib.patches.Rectangle: The rectangle patch added to the
                axes.
        """
        ax = ax or plt.gca()
        bbox = self.clade_bbox(taxon_labels)

        if extend_right != 0 or extend_down != 0:
            ax_to_data = ax.transAxes + ax.transData.inverted()
            origin = ax_to_data.transform([0, 0])

            data_extend = ax_to_data.transform([extend_right, extend_down]) - origin

            bbox["max_x"] += data_extend[0]

            # plot_tree calls invert_yaxis, up is down, hence '-='
            bbox["max_y"] -= data_extend[1]

        default_rect_kwds = dict(
            edgecolor="black",
            facecolor="#b3e2cd",
            linewidth=1.5,
            linestyle="-",
            zorder=5,
        )

        rect_kwds = {**default_rect_kwds, **kwds}

        rect = mp.patches.Rectangle(
            xy=(bbox["min_x"], bbox["min_y"]),
            width=bbox["max_x"] - bbox["min_x"],
            height=bbox["max_y"] - bbox["min_y"],
            **rect_kwds,
        )
        ax.add_patch(rect)

        if label is not None:
            default_label_kwds = dict(zorder=6, fontsize=10, va="bottom")
            label_kwds = {**default_label_kwds, **(label_kwds or {})}
            ax.text(bbox["min_x"], bbox["max_y"], label, **label_kwds)

        return rect

    def node_to_root_path(self, taxon: str | dp.Node) -> Generator[dp.Node, None, None]:
        """Nodes from a taxon to the root node.

        Args:
            taxon (str or dendropy.Node): The taxon label of the starting node,
                or the node object.

        Yields:
            dp.Node: The nodes from the taxon to the root.
        """

        def f(node):
            yield node
            if parent := node.parent_node:
                yield from f(parent)

        if isinstance(taxon, str):
            start = self.find_node_with_taxon_label(taxon)
            if start is None:
                raise ValueError(f"{taxon} not in tree")
        else:
            start = taxon

        yield from f(start)

    @staticmethod
    def find_closest_leaf_node(node: dp.Node) -> dp.Node:
        """
        Find the leaf node that has the shortest path length to the given node.

        Args:
            node: The node of interest.

        Returns:
            The leaf node closest to the node of interest.
        """
        if node.is_leaf():
            return node

        # Dijkstra's algorithm
        # Priority queue of (distance, count, node) tuples
        # (count is used as a tie-breaker)
        count = itertools.count()
        pq = [(0.0, next(count), node)]
        visited = {node}

        while pq:
            distance, _, node = heapq.heappop(pq)

            if node.is_leaf():
                return node

            neighbors = node.child_nodes()
            if node.parent_node:
                neighbors.append(node.parent_node)

            for neighbor in neighbors:
                if neighbor not in visited:
                    if neighbor.parent_node == node:
                        # neighbor is a child
                        edge_length = neighbor.edge.length or 0.0

                    else:
                        # neighbor is the parent
                        edge_length = node.edge.length or 0.0

                    heapq.heappush(pq, (distance + edge_length, next(count), neighbor))
                    visited.add(neighbor)

        # this should never happen!
        raise ValueError("no leaf node found in the tree")

    def internal_node_mrca(self, node1: dp.Node, node2: dp.Node) -> dp.Node:
        """Finds the MRCA of two nodes.

        Note:
            dendropy.tree.mrca only works on leaf nodes (or nodes with taxon labels).

        Args:
            node1 (dp.Node): The first node.
            node2 (dp.Node): The second node.

        Returns:
            dp.Node: The MRCA of the two nodes.
        """
        # The MRCA is the shared node with the maximum distance from the root
        node1_path = set(self.node_to_root_path(node1))
        node2_path = set(self.node_to_root_path(node2))
        return max(node1_path & node2_path, key=lambda x: x.distance_from_root())

    def distance_between(self, node1: dp.Node, node2: dp.Node) -> float:
        """Calculates the distance between two nodes.

        The distance is calculated as the sum of the branch lengths along
        the path connecting the two nodes.

        Args:
            node1 (dp.Node): The first node.
            node2 (dp.Node): The second node.

        Returns:
            float: The distance between the two nodes.
        """
        mrca = self.internal_node_mrca(node1, node2)

        def path_length(node: dp.Node, stop_node: dp.Node) -> float:
            length = 0.0
            while node != stop_node:
                length += node.edge.length
                node = node.parent_node
            return length

        return path_length(node1, mrca) + path_length(node2, mrca)


def compute_tree_layout(
    tree: dp.Tree,
    has_brlens: bool = True,
    copy: bool = False,
    round_brlens: Optional[int] = None,
) -> dp.Tree:
    """Computes layout parameters for a tree.

    Each node gets _x and _y values. The tree gets _xlim and _ylim values
    (tuples).

    Args:
        tree (dp.Tree): The tree to lay out.
        has_brlens (bool): Whether the tree has branch lengths.
        copy (bool): If True, a fresh copy of the tree is made.
        round_brlens (int, optional): The number of digits to round branch
            lengths to. Defaults to None.

    Returns:
        dp.Tree: The tree with layout parameters.
    """
    if copy:
        tree = dp.Tree(tree)

    # Add branch lengths if necessary
    if not has_brlens:
        for node in tree.preorder_node_iter():
            node.edge.length = 1

    # Compute x for nodes
    for node in tree.preorder_node_iter():
        if node.parent_node is None:
            node._x = 0
        else:
            length = (
                round(node.edge.length, round_brlens)
                if round_brlens is not None
                else node.edge.length
            )
            node._x = length + node.parent_node._x

    # Compute y for leaf nodes
    for _y, node in enumerate(tree.leaf_node_iter()):
        node._y = _y

    # Compute y for internal nodes
    for node in tree.postorder_node_iter():
        if not hasattr(node, "_y"):
            child_y = tuple(child._y for child in node.child_node_iter())
            node._y = sum(child_y) / len(child_y)

    # X and Y limits
    tree._xlim = 0, max(node._x for node in tree.leaf_nodes())
    tree._ylim = 0, max(node._y for node in tree.leaf_nodes())

    return tree


def plot_tree(
    tree: dp.Tree | Tree,
    has_brlens: bool = True,
    edge_kwds: dict = DEFAULT_EDGE_KWDS,
    leaf_kwds: dict = DEFAULT_LEAF_KWDS,
    internal_kwds: dict = DEFAULT_INTERNAL_KWDS,
    ax: mp.axes.Axes = None,
    labels: Optional[Union[Iterable[str], Literal["all"]]] = None,
    label_kwds: dict = DEFAULT_LABEL_KWDS,
    label_x_offset: float = 0.0,
    compute_layout: bool = True,
    fill_dotted_lines: bool = False,
    round_brlens: Optional[int] = None,
    color_leaves_by_site_aa: Optional[int] = None,
    hide_aa: Optional[str] = None,
    color_internal_nodes_by_site_aa: Optional[int] = None,
    aa_size: Optional[dict] = None,
    sequences: Optional[dict[str, str]] = None,
    jitter_x: Optional[float | str] = None,
    scale_bar: Optional[bool] = True,
    scale_bar_x_start: float = 0.0,
) -> mp.axes.Axes:
    """Plots a dendropy tree object.

    Tree nodes are plotted in their current order. To ladderize, call
    tree.ladderize() before plotting.

    Args:
        tree (dp.Tree | Tree): The tree to plot.
        has_brlens (bool): If False, all branch lengths are plotted as 1.
        edge_kwds (dict): Keyword arguments for edges, passed to
            matplotlib.collections.LineCollection.
        leaf_kwds (dict): Keyword arguments for leaves, passed to ax.scatter.
        label_kwds (dict): Keyword arguments passed to plt.text.
        internal_kwds (dict): Keyword arguments for internal nodes, passed to
            ax.scatter.
        ax (mp.axes.Axes, optional): The matplotlib axes to plot on. Defaults
            to None.
        labels (Optional[Union[Iterable[str], Literal["all"]]]): Taxon labels
            to annotate, or "all".
        label_kwds (dict): Keyword arguments passed to plt.text.
        leaf_label_x_offset (float): Amount to offset leaf labels in the x
            direction.
        compute_layout (bool): If True, compute the layout. If False, assumes
            the tree nodes already have _x and _y attributes.
        fill_dotted_lines (bool): If True, show dotted lines from leaves to
            the right-hand edge of the tree.
        round_brlens (int, optional): The number of decimal places to round
            branch lengths to. Passed to `compute_tree_layout`.
        color_leaves_by_site_aa (int, optional): Color leaves by the amino
            acid at this site (1-based). Overwrites 'c' in `leaf_kwds`.
            Requires `sequences`.
        hide_aa (str, optional): A string of amino acids to hide when
            coloring by site.
        color_internal_nodes_by_site_aa (int, optional): Same as
            `color_leaves_by_site_aa` but for internal nodes.
        sequences (dict[str, str], optional): A mapping of taxon labels to
            sequences. Required for `color_leaves_by_site_aa` and
            `color_internal_nodes_by_site_aa`.
        aa_size: For `color_leaves_by_site_aa` and `color_internal_nodes_by_site_aa`,
            this dictionary sets the marker size depending on the amino acid.
        jitter_x (float | str, optional): Amount of noise to add to the x
            value of leaves to avoid overplotting. Can be a float or 'auto'.
        scale_bar (bool): If True, show a scale bar.
        scale_bar_x_start (float): The leftmost x position of the scale bar.

    Returns:
        mp.axes.Axes: The matplotlib axes with the plotted tree. The tree
            object is returned with added attributes: _xlim, _ylim, and _x, _y
            on each node.
    """
    ax = ax or plt.gca()

    if labels == "all":
        labels = [node.taxon.label for node in tree.leaf_nodes()]

    elif labels is None:
        labels = []

    label_kwds = {**DEFAULT_LABEL_KWDS, **label_kwds}
    leaf_kwds = {**DEFAULT_LEAF_KWDS, **leaf_kwds}
    edge_kwds = {**DEFAULT_EDGE_KWDS, **edge_kwds}
    internal_kwds = {**DEFAULT_INTERNAL_KWDS, **internal_kwds}

    tree = (
        compute_tree_layout(tree, has_brlens, round_brlens=round_brlens)
        if compute_layout
        else tree
    )

    # Draw edges
    edges = []
    for node in tree.preorder_node_iter():
        # Horizontal
        if node.parent_node:
            edges.append(((node._x, node._y), (node.parent_node._x, node._y)))

        # Vertical
        if node.child_nodes():
            max_y = max(node._y for node in node.child_node_iter())
            min_y = min(node._y for node in node.child_node_iter())
            edges.append(((node._x, max_y), (node._x, min_y)))

    ax.add_artist(mp.collections.LineCollection(segments=edges, **edge_kwds))

    # Dotted lines from the leaves to the right hand edge of the tree
    if fill_dotted_lines:
        max_x = max(node._x for node in tree.leaf_nodes())
        dotted_edges = [
            ((node._x, node._y), (max_x, node._y)) for node in tree.leaf_nodes()
        ]
        ax.add_artist(
            mp.collections.LineCollection(
                segments=dotted_edges,
                ls=(2, (1, 10)),
                color="black",
                linewidth=0.5,
            )
        )

    # Infer suitable jitter_x value if need be
    if jitter_x == "auto":
        jitter_x = estimate_unit_branch_length(
            [edge.length for edge in tree.edges() if edge.length is not None]
        )
        logging.info(f"Auto jitter_x: {jitter_x}")

    # Draw leaves
    hide_aa = set(hide_aa or "")

    if color_leaves_by_site_aa is not None:
        # Group leaves by amino acid at site so that each group can be colored and a label passed
        # for the legend.

        def _get_aa(node):
            """
            Temporary helper function to get the amino acid at the site. Passed to sorted and
            itertools.groupby to group leaves regardless of input order.
            """
            return sequences[node.taxon.label][color_leaves_by_site_aa - 1]

        # Make groups of nodes that all have a particular amino acid at the site
        sorted_nodes = sorted(tree.leaf_node_iter(), key=_get_aa)
        aa_groups = {
            aa: list(nodes)
            for aa, nodes in itertools.groupby(sorted_nodes, key=_get_aa)
            if aa not in hide_aa
        }

        # Order the groups by size so that the smallest groups are plotted last
        # to make them more visible. Put unknown amino acids at the back
        for aa in reversed(
            sorted(
                aa_groups,
                key=lambda aa: len(aa_groups[aa]) if aa != "X" else 0,
            )
        ):
            nodes = aa_groups[aa]
            leaf_kwds["color"] = amino_acid_colors[aa]
            if aa_size:
                leaf_kwds["s"] = aa_size[aa]
            x, y = node_x_y(nodes, jitter_x=jitter_x)
            ax.scatter(x, y, **leaf_kwds, label=aa if aa != "X" else None)

    else:
        x, y = node_x_y(tree.leaf_node_iter(), jitter_x=jitter_x)
        ax.scatter(x, y, **leaf_kwds)

    # Draw internal nodes
    if color_internal_nodes_by_site_aa is not None:
        internal_kwds["color"] = [
            amino_acid_colors[
                sequences[node.label][color_internal_nodes_by_site_aa - 1]
            ]
            for node in tree.internal_nodes()
        ]

    if internal_kwds:
        x, y = node_x_y(tree.internal_nodes())
        ax.scatter(x, y, **internal_kwds)

    # Labels

    # If labels is True but not iterable, simply label all leaf nodes
    if not isinstance(labels, Iterable) and labels:
        for node in tree.leaf_node_iter():
            ax.text(
                node._x + label_x_offset,
                node._y,
                node.taxon.label,
                **label_kwds,
            )

    # If labels is a mapping then look up the label for each node
    elif isinstance(labels, (Mapping, pd.Series)):
        for node in tree.leaf_node_iter():
            if label := labels.get(node.taxon.label):
                ax.text(node._x + label_x_offset, node._y, label, **label_kwds)

    # If all nodes are passed, plot all their labels
    elif all(isinstance(item, dp.Node) for item in labels):
        for node in labels:
            ax.text(
                node._x + label_x_offset,
                node._y,
                node.taxon.label,
                **label_kwds,
            )

    elif all(isinstance(item, str) for item in labels):
        # If all strings are passed, and there is one per leaf, plot each on a leaf
        if len(labels) == len(tree.leaf_nodes()):
            for node, label in zip(tree.leaf_node_iter(), labels):
                ax.text(node._x + label_x_offset, node._y, label, **label_kwds)

        # If all strings are passed, and there are fewer than one per leaf, find
        # the nodes that have these taxon labels and label them
        elif len(labels) < len(tree.leaf_nodes()):
            for node in tree.find_nodes(lambda n: taxon_in_node_labels(labels, n)):
                ax.text(
                    node._x + label_x_offset,
                    node._y,
                    node.taxon.label,
                    **label_kwds,
                )

        else:
            raise ValueError("passed more labels than number of leaf nodes")

    else:
        raise ValueError("couldn't process labels")

    if scale_bar:
        length = tree._xlim[1] / 10
        length = float(f"{length:.1g}")  # round length to 1 significant figure
        bottom = tree._ylim[1]
        ax.plot(
            (scale_bar_x_start, scale_bar_x_start + length),
            (bottom, bottom),
            c="black",
            lw=1,
            clip_on=False,
        )
        ax.text(
            scale_bar_x_start + (length / 2),
            bottom,
            str(length),
            ha="center",
            va="bottom",
            clip_on=False,
        )

    # Finalise
    ax.set_xlim(tree._xlim)
    ax.set_ylim(tree._ylim)
    ax.axis("off")
    ax.set_yticks([])
    ax.invert_yaxis()

    return tree, ax


def plot_path_to_taxon(
    tree: dp.Tree | Tree,
    taxon_label: str,
    ax: Optional[mp.axes.Axes] = None,
    label_taxon: bool = True,
    label_kwds: Optional[dict] = None,
    **kwds,
) -> mp.collections.LineCollection:
    """Plots the path from the root to a given taxon.

    Args:
        tree (dp.Tree | Tree): The tree to plot.
        taxon_label (str): The taxon label of the node to plot the path to.
        ax (mp.axes.Axes, optional): The matplotlib axes to plot on.
        label_taxon (bool): If True, label the taxon at the end of the path.
        label_kwds (dict, optional): Keyword arguments passed to plt.text.

    Returns:
        mp.collections.LineCollection
    """
    ax = ax or plt.gca()

    edge_kwds = {
        "linewidths": 2,
        "color": "red",
        "zorder": 20,
        **DEFAULT_EDGE_KWDS,
        **kwds,
    }

    if not hasattr(next(tree.leaf_node_iter()), "_x"):
        tree = compute_tree_layout(tree)

    nodes = tuple(tree.node_to_root_path(taxon_label))

    if label_taxon:
        label_kwds = {**DEFAULT_LABEL_KWDS, **(label_kwds or {})}
        taxon_node = nodes[0]
        ax.text(taxon_node._x, taxon_node._y, taxon_node.taxon.label, **label_kwds)

    edges = []
    for child, parent in itertools.pairwise(nodes):
        edges.append(((parent._x, parent._y), (parent._x, child._y)))  # vertical
        edges.append(((parent._x, child._y), (child._x, child._y)))  # horizontal

    return ax.add_artist(mp.collections.LineCollection(segments=edges, **edge_kwds))


def node_x_y(
    nodes: Iterable[dp.Node], jitter_x: Optional[float] = None
) -> tuple[tuple, tuple]:
    """Gets the x and y coordinates of nodes.

    Args:
        nodes (Iterable[dp.Node]): An iterable of dendropy Node objects.
        jitter_x (float, optional): The amount of jitter to add to the x
            coordinates. X is jittered by a quarter of this value in both
            directions. Defaults to None.

    Returns:
        tuple[tuple, tuple]: A tuple containing two tuples: one for x
            coordinates and one for y coordinates.
    """
    if jitter_x is None:
        return zip(*((node._x, node._y) for node in nodes))
    else:
        random.seed(42)
        lo = -jitter_x / 4
        hi = jitter_x / 4
        return zip(*((node._x + random.uniform(lo, hi), node._y) for node in nodes))


def node_x_y_from_taxon_label(tree: Tree, taxon_label: str) -> tuple[float, float]:
    """Finds the x and y attributes of a node from its taxon label.

    Args:
        tree (Tree): The tree to search in.
        taxon_label (str): The taxon label of the node.

    Returns:
        tuple[float, float]: The x and y coordinates of the node.
    """
    node = tree.find_node_with_taxon_label(taxon_label)
    return node._x, node._y


def plot_leaves_with_labels(
    tree: dp.Tree, labels: list[str], ax: mp.axes.Axes = None, **kwds
):
    """Plots leaves that have taxon labels in a given list.

    Args:
        tree (dp.Tree): The tree to plot.
        labels (list[str]): A list of taxon labels to plot.
        ax (mp.axes.Axes, optional): The matplotlib axes to plot on.
            Defaults to None.
        **kwds: Additional keyword arguments passed to plt.scatter.
    """
    ax = ax or plt.gca()
    s = kwds.pop("s", 20)
    c = kwds.pop("c", "red")
    zorder = kwds.pop("zorder", 19)
    linewidth = kwds.pop("linewidth", 0.5)
    edgecolor = kwds.pop("edgecolor", "white")
    nodes = tree.find_nodes(lambda n: taxon_in_node_labels(labels, n))

    if not nodes:
        raise ValueError("No node with taxon labels in labels found in tree.")

    try:
        x = [node._x for node in nodes]
    except AttributeError as err:
        print("Node(s) do not have _x attribute. Run compute_tree_layout.")
        raise (err)

    try:
        y = [node._y for node in nodes]
    except AttributeError as err:
        print("Node(s) do not have _y attribute. Run compute_tree_layout.")
        raise (err)

    ax.scatter(
        x,
        y,
        s=s,
        c=c,
        zorder=zorder,
        linewidth=linewidth,
        edgecolor=edgecolor,
        **kwds,
    )


def plot_subs_on_tree(
    tree: dp.Tree,
    sequences: dict[str, str],
    exclude_leaves: bool = True,
    on_path_to_taxon: Optional[str] = None,
    site_offset: int = 0,
    ignore_chars: str = "X-",
    arrow_length: float = 40,
    arrow_facecolor: str = "black",
    fontsize: float = 6,
    xytext_transform: tuple[float, float] = (1.0, 1.0),
    **kwds,
) -> Counter:
    """Plots substitutions on a tree.

    This function plots substitutions on the tree by finding substitutions
    between each node and its parent node. The substitutions are then plotted
    at the midpoint of the edge between the node and its parent.

    Args:
        tree (dp.Tree): The tree to annotate.
        sequences (dict[str, str]): A mapping of node labels to sequences.
        exclude_leaves (bool): If True, exclude leaves from substitution
            plotting.
        on_path_to_taxon (str, optional): If provided, only plot substitutions
            on the path from the root to this taxon. Defaults to None.
        site_offset (int): Value to add to substitution site numbers.
        ignore_chars (str): Substitutions involving these characters will not
            be shown.
        arrow_length (float): The length of the arrow pointing to the
            mutation.
        arrow_facecolor (str): The face color of the arrow.
        fontsize (float): The font size of the text.
        xytext_transform (tuple[float, float]): Multipliers for the xytext
            offsets.
        **kwds: Other keyword arguments passed to plt.annotate.

    Returns:
        Counter: A counter of the number of times each substitution appears
            in the tree.
    """
    ignore = set(ignore_chars)

    sub_counts = Counter()

    if not hasattr(next(tree.leaf_node_iter()), "_x"):
        tree = compute_tree_layout(tree)

    xytext = (
        -arrow_length * xytext_transform[0],
        arrow_length * xytext_transform[1],
    )

    if on_path_to_taxon is not None:
        path = set(tree.taxon_to_root(on_path_to_taxon))

    for node in tree.nodes():
        if (
            (parent := node.parent_node)
            and not (exclude_leaves and node.is_leaf())
            and (on_path_to_taxon is None or (parent in path and node in path))
        ):
            parent_seq = sequences[get_label(parent)]
            this_seq = sequences[get_label(node)]

            if parent_seq is None or this_seq is None:
                continue

            subs = [
                sub
                for sub in find_substitutions(parent_seq, this_seq, offset=site_offset)
                if all(char not in sub for char in ignore)
            ]

            if len(subs) == 0:
                continue

            sub_counts.update(subs)

            x = (node._x + parent._x) / 2

            plt.annotate(
                "\n".join(map(str, subs)),
                (x, node._y),
                xytext=xytext,
                va="bottom",
                ha="right",
                textcoords="offset pixels",
                arrowprops=dict(
                    facecolor=arrow_facecolor,
                    shrink=0,
                    linewidth=0,
                    width=0.3,
                    headwidth=2,
                    headlength=2,
                ),
                fontsize=fontsize,
                **kwds,
            )

    return sub_counts


def get_label(node: dp.Node):
    """Gets the label of a node.

    If the node itself has a label, that is returned. Otherwise, the label
    of the node's taxon is returned.

    Args:
        node (dp.Node): The node to get the label from.

    Returns:
        str: The label of the node.
    """
    if node.label is not None:
        return node.label
    else:
        return node.taxon.label


def taxon_in_node_labels(labels, node):
    """Checks if a node's taxon label is in a set of labels.

    Args:
        labels (iterable): A collection of labels to check against.
        node (dp.Node): The node to check.

    Returns:
        bool: True if the node's taxon label is in the labels, False
            otherwise.
    """
    try:
        return node.taxon.label in labels
    except AttributeError:
        return False


def taxon_in_node_label(label, node):
    """Checks if a node has a matching taxon label.

    Args:
        label (str): The label to check for.
        node (dp.Node): The node to check.

    Returns:
        bool: True if the node's taxon label matches, False otherwise.
    """
    try:
        return node.taxon.label == label
    except AttributeError:
        return False


def get_trunk(tree, attr="_x"):
    """
    Ordered nodes in tree, from deepest leaf to root.

    Args:
        tree (dendropy Tree)
        attr (str)

    Returns:
        tuple containing dendropy Nodes
    """
    node = deepest_leaf(tree, attr)
    trunk = []
    while hasattr(node, "parent_node"):
        trunk.append(node)
        node = node.parent_node
    return tuple(trunk)


def deepest_leaf(tree, attr="_x"):
    """
    Find the deepest leaf node in the tree.

    Args:
        tree (dendropy Tree)
        attr (str): Either _x or _y. Gets node with max attribute.

    Returns:
        dendropy Node
    """
    try:
        return max(tree.leaf_node_iter(), key=attrgetter(attr))

    except AttributeError:
        tree = compute_tree_layout(tree)
        return max(tree.leaf_node_iter(), key=attrgetter(attr))


def read_iqtree_ancestral_states(
    state_file,
    partition_names: Optional[list[str]] = None,
    translate_nt: bool = False,
) -> dict[str : dict[str, str]] | dict[str:str]:
    """
    Read an ancestral state file generated by IQ-TREE. If the file contains multiple partitions
    (i.e. a 'Part' column is present), then return a dict of dicts containing sequences accessed by
    [partition][node]. Otherwise return a dict of sequences accessed by node.

    Args:
        state_file: Path to .state file generated by iqtree --ancestral
        partition_names: Partitions are numbered from 1 in the .state file. Pass names for each
            segment (i.e. the order that partition_names appear in the partitions). Only takes
            effect if multiple partitions are present.
        translate_nt: If ancestral states are nucleotide sequences then translate them.

    Returns:
        dict of dicts that maps [node][partition] -> sequence, or dict that maps node -> sequence.
    """
    df = pd.read_table(state_file, comment="#")

    if "Part" in df:
        seqs = defaultdict(dict)
        for (node_name, part), sub_df in df.groupby(["Node", "Part"], sort=False):
            part_key = (
                partition_names[part - 1] if partition_names is not None else part
            )
            seq = "".join(sub_df["State"])
            seqs[part_key][node_name] = sloppy_translate(seq) if translate_nt else seq

    else:
        seqs = {}
        for node_name, sub_df in df.groupby("Node", sort=False):
            seq = "".join(sub_df["State"])
            seqs[node_name] = sloppy_translate(seq) if translate_nt else seq

    return seqs


def read_raxml_ancestral_sequences(
    tree, node_labelled_tree, ancestral_seqs, leaf_seqs=None
):
    """
    Read a tree and ancestral sequences estimated by RAxML.

    RAxML can estimate marginal ancestral sequences for internal nodes on a
    tree using a call like:

        raxmlHPC -f A -t {treeFile} -s {sequenceFile} -m {model} -n {name}

    The analysis outputs several files:

    - RAxML_nodeLabelledRootedTree.{name} contains a copy of the input tree
        where all internal nodes have a unique identifier {id}.
    - RAxML_marginalAncestralStates.{name} contains the ancestral sequence for
        each internal node. The format of each line is '{id} {sequence}'
    - RAxML_marginalAncestralProbabilities.{name} contains probabilities of
        each base at each site for each internal node. (Not used by this
        function.)

    Notes:
        Developed with output from RAxML version 8.2.12.

    Args:
        tree (str): Path to original input tree ({treeFile}).
        node_labelled_tree (str): Path to the tree with node labels.
            (RAxML_nodeLabelledRootedTree.{name})
        ancestral_seqs (str): Path to file containing the ancestral sequences.
            (RAxML_marginalAncestralStates.{name})
        leaf_seqs (str): (Optional) path to fasta file containing leaf
            sequences. ({sequenceFile}). If this is provided, also attach
            sequences to leaf nodes.

    Returns:
        (dendropy Tree) with sequences attached to nodes. Sequences are
            attached as 'sequence' attributes on Nodes.
    """
    tree = dp.Tree.get(path=tree, schema="newick", preserve_underscores=True)
    labelled_tree = dp.Tree.get(
        path=node_labelled_tree, schema="newick", preserve_underscores=True
    )

    # Dict mapping leaf labels -> node label
    leaves_to_labelled_node = {
        sorted_leaf_labels(node): node.label for node in labelled_tree.nodes()
    }

    internal_sequences = {}
    with open(ancestral_seqs, "r") as handle:
        for i, line in enumerate(handle.readlines()):
            try:
                key, sequence = line.strip().split()
            except ValueError as err:
                print(
                    f"Problem reading sequence on line {i + 1} in " f"{ancestral_seqs}."
                )
                raise err
            internal_sequences[key] = sequence

    for node in tree.internal_nodes():
        leaves = sorted_leaf_labels(node)
        key = leaves_to_labelled_node[leaves]
        node.sequence = internal_sequences[key]

    if leaf_seqs:
        add_sequences_to_tree(tree, leaf_seqs)

    return tree


def add_sequences_to_tree(
    tree: dp.Tree,
    path: str,
    labeller: Optional[callable] = None,
    seq_formatter: Optional[callable] = None,
) -> None:
    """
    Add sequences to leaves inplace.

    Args:
        tree: Dendropy tree.
        path: Path to multiple sequence alignment. Taxon labels in tree must match the
            fasta description.
        labeller: Function that takes a FASTA description and returns the name of
            associated taxon in the tree. For instance, a full fasta description might
            look like:

                >cdsUUB77424 A/Maryland/12786/2022 2022/04/07 HA

            RAxML would call this taxon just 'cdsUUB77424'. So the callable would have to
            be something like: lambda x: x.split()[0]
        seq_formatter
    """
    seqs = {}
    with open(path, "r") as handle:
        for r in SeqIO.parse(handle, format="fasta"):
            key = labeller(r.description) if labeller is not None else r.description
            seq = seq_formatter(r.seq) if seq_formatter is not None else r.seq
            seqs[key] = seq

    for node in tree.leaf_node_iter():
        node.sequence = seqs[node.taxon.label]


def sorted_leaf_labels(node):
    """Tuple containing the sorted leaf labels of a node."""
    return tuple(sorted(leaf.taxon.label for leaf in node.leaf_nodes()))


def compare_trees(
    left,
    right,
    gap=0.1,
    x0=0,
    connect_kwds=dict(),
    extend_kwds=dict(),
    extend_every=10,
    left_kwds=dict(),
    right_kwds=dict(),
    connect_colors=dict(),
    extend_colors=dict(),
):
    """Plot two phylogenies side by side, and join the same taxa in each tree.

    Args:
        left (dendropy Tree)
        right (dendropy Tree)
        gap (float): Space between the two trees.
        x0 (float): The x coordinate of the root of the left hand tree.
        connect_kwds (dict): Keywords passed to matplotlib LineCollection.
            These are used for the lines that connect matching taxa.
        extend_kwds (dict): Keywords passed to matplotlib LineCollection.
            These are used for lines that connect taxa to the connection lines.
        extend_every (n): Draw branch extension lines every n leaves.
        left_kwds (dict): Passed to plot_tree for the left tree.
        right_kwds (dict): Passed to plot_tree for the right tree.
        connect_colors (dict or Callable): Maps taxon labels to colors. Ignored if
            'colors' is used in connect_kwds.
        extend_colors (dict or Callable): Maps taxon labels to colors. Ignored if
            'colors' is used in extend_kwds.

    Returns:
        (2-tuple) containing dendropy Trees with _x and _y plot locations on
            nodes.
    """
    left = compute_tree_layout(left)
    right = compute_tree_layout(right)

    # Reflect the right tree
    constant = left._xlim[1] + right._xlim[1] + gap + x0
    for node in right.nodes():
        node._x *= -1
        node._x += constant

    # # Move the left tree by x0
    for node in left.nodes():
        node._x += x0

    # Criss-crossing lines that connect matching taxa in left and right
    if connect_kwds:
        segments = []
        colors = [] if "colors" not in connect_kwds and connect_colors else None

        for node in left.leaf_node_iter():
            other = right.find_node_with_taxon_label(node.taxon.label)

            if other:
                segments.append(
                    (
                        (left._xlim[1] + x0, node._y),
                        (left._xlim[1] + x0 + gap, other._y),
                    )
                )

                if colors is not None:
                    try:
                        c = connect_colors[node.taxon.label]
                    except TypeError:
                        c = connect_colors(node.taxon.label)
                    colors.append(c)

        if colors is not None:
            connect_kwds["colors"] = colors

        plt.gca().add_artist(mp.collections.LineCollection(segments, **connect_kwds))

    # Extend branches horizontally from the left and right trees to meet the
    # criss-crossing lines
    if extend_kwds:
        segments = []
        colors = [] if "colors" not in extend_kwds and extend_colors else None
        key = attrgetter("_y")

        for node in sorted(left.leaf_node_iter(), key=key)[::extend_every]:
            segments.append(((node._x, node._y), (left._xlim[1] + x0, node._y)))

            if colors is not None:
                try:
                    c = extend_colors[node.taxon.label]
                except TypeError:
                    c = extend_colors(node.taxon.label)
                colors.append(c)

        for node in sorted(right.leaf_node_iter(), key=key)[::extend_every]:
            segments.append(((left._xlim[1] + x0 + gap, node._y), (node._x, node._y)))

            if colors is not None:
                try:
                    c = extend_colors[node.taxon.label]
                except TypeError:
                    c = extend_colors(node.taxon.label)
                colors.append(c)

        if colors is not None:
            extend_kwds["colors"] = colors

        plt.gca().add_artist(mp.collections.LineCollection(segments, **extend_kwds))

    plot_tree(left, compute_layout=False, **left_kwds)
    plot_tree(right, compute_layout=False, **right_kwds)

    # plt.xlim(0, constant)

    return left, right


def prune_nodes_with_labels(tree, labels):
    """
    Prune nodes from tree that have a taxon label in labels.

    Args:
        tree (dendropy Tree)
        labels (iterable containing str)

    Returns:
        (dendropy Tree)
    """
    nodes = []
    not_found = []
    for label in labels:
        node = tree.find_node_with_taxon_label(label)
        if node is None:
            not_found.append(node)
        else:
            nodes.append(node)

    if not_found and len(nodes) == 0:
        raise ValueError("No taxa found with any of these labels.")
    elif not_found:
        warnings.warn(f"Couldn't find:\n{''.join(not_found)}")

    tree.prune_nodes(nodes)
    tree.prune_leaves_without_taxa(recursive=True)
    return tree


Column = namedtuple("Column", ["site", "aas"])


class MultipleSequenceAlignment(Align.MultipleSeqAlignment):
    def variable_sites(
        self, min_2nd_most_freq: int = 1
    ) -> Generator[Column, None, None]:
        """
        Generator for variable sites in the alignment.

        Args:
            min_2nd_most_freq: Used to filter out sites that have low variability. For
                instance if min_2nd_most_freq is 2 a column containing 'AAAAT' should be
                excluded because the second most frequent character (T) has a frequency
                of 1.
        """
        for i in range(self.get_alignment_length()):
            site = i + 1
            aas = self[:, i]
            if len(set(aas)) != 1:
                # Frequency of the second most common
                _, count = Counter(aas).most_common()[1]
                if count >= min_2nd_most_freq:
                    yield Column(site, aas)

    def plot(
        self,
        ax: Optional[mp.axes.Axes] = None,
        fontsize: int = 6,
        variable_sites_kwds: Optional[dict] = None,
        rotate_xtick_labels: bool = False,
        sites: Optional[Iterable[int]] = None,
    ) -> mp.axes.Axes:
        """
        Plot variable sites in the alignment.

        Args:
            ax: Matplotlib ax.
            fontsize: Fontsize of the character labels.
            variable_sites_kwds: Passed to MultipleSequenceAlignment.variable_sites.
            rotate_xtick_labels: Rotate the xtick labels 90 degrees.
            sites: Only plot these sites. (Note: Only variable sites are plotted, so if a
                site is passed in this argument but it is not variable it will not be
                displayed.)
        """
        ax = ax or plt.gca()
        variable_sites_kwds = {} if variable_sites_kwds is None else variable_sites_kwds

        variable_sites = tuple(self.variable_sites(**variable_sites_kwds))

        if len(variable_sites) == 0:
            raise ValueError("No variable sites in alignment")

        if sites is not None:
            sites = set(sites)
            variable_sites = tuple(
                column for column in variable_sites if column.site in sites
            )

        for x, site in enumerate(variable_sites):
            for y, aa in enumerate(site.aas):
                rect = mp.patches.Rectangle(
                    (x, y), width=1, height=1, facecolor=amino_acid_colors[aa]
                )
                ax.add_artist(rect)
                ax.text(
                    x + 0.5,
                    y + 0.5,
                    aa,
                    ha="center",
                    va="center",
                    fontsize=fontsize,
                    color="black" if aa.upper() in "M" else "white",
                )

        max_x = rect.xy[0]

        ax.set(
            xlim=(0, max_x + 1),
            ylim=(0, len(self)),
            yticks=np.arange(0.5, len(self) + 0.5),
            yticklabels=[record.description for record in self],
            xticks=np.arange(0.5, max_x + 1.5),
            xticklabels=[column.site for column in variable_sites],
        )

        if rotate_xtick_labels:
            ax.set_xticks(ax.get_xticks(), ax.get_xticklabels(), rotation=90)

        for spine in "top", "bottom", "left", "right":
            ax.spines[spine].set_visible(False)

        return ax


def color_stack(
    tree: Tree,
    values: dict[str, Any],
    color_dict: dict[str, str],
    default_color: Optional[str] = None,
    x: float = 0,
    ax: Optional[mp.axes.Axes] = None,
    leg_kwds: Optional[dict] = None,
) -> tuple[mp.axes.Axes, mp.legend.Legend]:
    """
    A stack of colored patches that can be plotted adjacent to a tree to show how values
    vary on the tree leaves.

    Must have called eremitalpa.compute_layout on the tree in order to know y values for
    leaves (done anyway by eremitalpa.plot_tree).

    Args:
        tree: The tree to be plotted next to.
        values: Maps taxon labels to values to be plotted.
        color_dict: Maps values to colors.
        default_color: Color to use for values missing from color_dict.
        x: The x value to plot the stack at.
        ax: Matplotlib ax
    """
    ax = ax or plt.gca()
    leg_kwds = leg_kwds or dict()

    labels = [leaf.taxon.label for leaf in tree.leaf_nodes()]

    leaf_ys = [leaf._y for leaf in tree.leaf_nodes()]

    colors = [color_dict.get(values[label], default_color) for label in labels]

    # Group color and leaf y values by batches of the same color in order to make a
    # single larger patch if consecutive patches would be the same color.
    for _, grouped in itertools.groupby(zip(colors, leaf_ys), key=itemgetter(0)):
        # color will all be the same (it is what is being grouped by)
        # leaf_y will be the y values of each leaf in this group
        color, leaf_y = zip(*grouped)

        ax.add_patch(
            mp.patches.Rectangle(
                (
                    x,
                    leaf_y[0] - 0.5,
                ),  # bottom of the patch is the first y value
                width=1,
                height=len(color),  # height of the patch is just the size of the group
                color=color[0],
                linewidth=0,
            )
        )

    # Patches off the ax for easy legend
    handles_labels = [(mp.patches.Patch(color=v), k) for k, v in color_dict.items()]
    handles, labels = zip(*handles_labels)
    leg = ax.legend(handles, labels, **leg_kwds)
    ax.add_artist(leg)
    ax.axis(False)
    return ax, leg


def estimate_unit_branch_length(
    branch_lengths: list[float], min_diff: float = 1e-6, round_to: int = 6
) -> float:
    """
    Estimates the fundamental unit length in a set of phylogenetic branch lengths. Assumes that
    branch lengths occur in approximate integer multiples of a small unit. Algorithm:

        1. Compute all pairwise absolute differences between branch lengths.
        2. Construct a histogram of these differences with an adaptive bin size.
        3. Identify the most common small difference (mode of the histogram),
        which represents the estimated unit length.

    Args:
        branch_lengths (list or np.array): A list of branch lengths.
        min_diff (float): Minimum difference between branch lengths to consider. Branch length
            differences smaller than this value are considered to be zero.
        round_to (int): Round branch_lengths to this many decimal places.

    Returns:
        float: Estimated fundamental unit length.
    """
    branch_lengths = np.array([round(edge, round_to) for edge in branch_lengths])

    # Compute pairwise absolute differences
    diffs = np.abs(np.subtract.outer(branch_lengths, branch_lengths))
    diffs = diffs[np.triu_indices_from(diffs, k=1)]  # Extract unique values
    diffs = diffs[diffs > min_diff]  # Remove near-zero values

    # Define bin width adaptively based on small quantile
    bin_width = np.percentile(diffs, 1)
    hist, bin_edges = np.histogram(diffs, bins=np.arange(0, np.max(diffs), bin_width))

    # Find bin with the highest count (mode) and return it
    return bin_edges[np.argmax(hist)]


def plot_tree_with_subplots(
    tree: Tree,
    aa_seqs: dict,
    site: int,
    subplot_taxa_shifts: dict[str, tuple[float, float]],
    fun: Callable,
    fun_kwds: Optional[dict] = None,
    subplot_width: float = 0.2,
    subplot_height: float = 0.1,
    figsize: tuple[float, float] = (8, 12),
    sharex: bool = True,
    sharey: bool = True,
    snap_x: Optional[float] = None,
    snap_y: Optional[float] = None,
    arrow_origins: Optional[dict[str, tuple[float, float]]] = None,
    **kwds,
) -> mp.axes.Axes:
    """
    Plot a phylogeny tree with subplots for specified taxa.

    This function draws a phylogeny based on a given tree and amino acid sequences.
    It colors leaves (and internal nodes) according to their amino acid at a specified site,
    and attaches additional subplots at user-defined nodes for further custom visualization.

    Args:
        tree: eremitalpa.Tree
            The phylogenetic tree to be plotted.
        aa_seqs: dict
            A dictionary containing amino acid sequences for each taxon.
            Keys should match the node names in the tree, and values should be the sequences.
        site: int
            The site (1-based) to color the tree's leaves and internal nodes.
        subplot_taxa_shifts: dict of str -> tuple of float
            A mapping from taxon names to tuples (dx, dy).
            These values control the position of the subplot axes relative to their respective nodes.
            Uses axes coordinates (i.e. a value of 1 would shift an entire ax worth of distance).
        fun: Callable
            A callable function to generate each subplot.
            Must accept the current taxon as the first argument and an axes object as the second argument.
        fun_kwds: dict
            A dictionary of additional keyword arguments passed to the subplot function ``fun``.
        subplot_width: float, optional
            The width of each subplot in figure coordinates, by default 0.2.
        subplot_height: float, optional
            The height of each subplot in figure coordinates, by default 0.1.
        figsize: tuple of float, optional
            The overall size of the figure, by default (8, 12).
        sharex: bool, Have the sub axes share x-axes.
        sharey: bool, Have the sub axes share y-axes.
        snap_x: float, Snap x position of the subplots to a grid. This argument
            sets the grid size.
        snap_y: float, Snap y position of the subplots to a grid. This argument
            sets the grid size.
        arrow_origins: dict of str -> tuple of float. Pass the axes coordinates of each subplot for where
            its arrow should originate. By default arrows originate from the center.
        **kwds: Passed to plot_tree.

    Returns:
        2-tuple containing:
            matplotlib.axes.Axes - the main axes.
            dict [str, matplotlib.axes.Axes] containing sub plots.
    """

    fig, main_ax = plt.subplots(figsize=figsize)
    plot_tree(
        tree,
        color_leaves_by_site_aa=site,
        color_internal_nodes_by_site_aa=site,
        sequences=aa_seqs,
        leaf_kwds=dict(s=8, zorder=15),
        internal_kwds=dict(s=4),
        edge_kwds=dict(lw=0.5, color="darkgrey"),
        ax=main_ax,
        **kwds,
    )
    main_ax.legend(
        markerscale=6,
        loc="lower left",
        fontsize=14,
        bbox_to_anchor=(-0.1, 0.025),
        frameon=True,
        framealpha=1,
        title=site,
        title_fontsize=14,
    )

    data_to_fig = (main_ax.transData + fig.transFigure.inverted()).transform
    first_sub_ax = None
    arrow_origins = arrow_origins or {}

    sub_plots = {}

    for taxon in subplot_taxa_shifts:
        x, y = node_x_y_from_taxon_label(tree, taxon)

        # Position of ax is the x,y position of the taxa plus a shift
        shift = subplot_taxa_shifts.get(taxon, (0.1, 0.1))
        subplot_left, subplot_bottom = data_to_fig((x, y)) + shift

        # Snapping
        if snap_x is not None:
            subplot_left = snap(subplot_left, grid_size=snap_x)

        if snap_y is not None:
            subplot_bottom = snap(subplot_bottom, grid_size=snap_y)

        # Add the sub axes
        position = subplot_left, subplot_bottom, subplot_width, subplot_height
        if first_sub_ax is None:
            sub_ax = plt.axes(position)
            first_sub_ax = sub_ax
        else:
            if sharex and sharey:
                sub_ax = plt.axes(position, sharex=first_sub_ax, sharey=first_sub_ax)
            elif sharex:
                sub_ax = plt.axes(position, sharex=first_sub_ax)
            elif sharey:
                sub_ax = plt.axes(position, sharey=first_sub_ax)
            else:
                sub_ax = plt.axes(position)

        sub_plots[taxon] = sub_ax

        # Plot the subplot
        fun(taxon, ax=sub_ax, **(fun_kwds or {}))

        # Arrow from the subplot to the relevant taxa in the tree
        # Want arrow to originate from the center of the subplots.
        # So, need a transform that goes from the center the subplot
        # axes coordinates to the main ax data coordinates
        transform = (sub_ax.transAxes + main_ax.transData.inverted()).transform
        origin = arrow_origins.get(taxon, (0.5, 0.5))
        main_ax.annotate(
            "",
            xy=(x, y),
            xytext=transform(origin),
            zorder=20,
            arrowprops=dict(
                width=1,
                headwidth=7,
                headlength=7,
                facecolor="black",
                linewidth=0.3,
                edgecolor="white",
                clip_on=False,
            ),
        )

    return main_ax, sub_plots


def snap(value: float, grid_size: float) -> float:
    """
    Find the closest point on a grid for a value.
    """
    return round(value / grid_size) * grid_size


def plot_tree_interactive(
    tree: dp.Tree,
    has_brlens: bool = True,
    leaf_colors: Optional[dict] = None,
    default_leaf_color: str = "black",
    leaf_sizes: Optional[dict] = None,
    default_leaf_size: int = 5,
):
    """Plots a dendropy tree object interactively using plotly.

    Args:
        tree (dp.Tree): The tree to plot.
        has_brlens (bool): If False, all branch lengths are plotted as 1.
        leaf_colors (dict, optional): A dictionary mapping taxon labels to colors.
        default_leaf_color (str): The default color for taxa not in `leaf_colors`.
        leaf_sizes (dict, optional): A dictionary mapping taxon labels to sizes.
        default_leaf_size (int): The default size for taxa not in `leaf_sizes`.
    """
    if not hasattr(next(tree.leaf_node_iter()), "_x"):
        compute_tree_layout(tree, has_brlens=has_brlens)

    fig = go.Figure()
    leaf_colors = leaf_colors or {}
    leaf_sizes = leaf_sizes or {}

    # Edges
    for node in tree.preorder_node_iter():
        if node.parent_node:
            fig.add_trace(
                go.Scatter(
                    x=[node.parent_node._x, node._x],
                    y=[node._y, node._y],
                    mode="lines",
                    line=dict(color="black", width=0.5),
                    hoverinfo="none",
                )
            )
        if node.child_nodes():
            max_y = max(child._y for child in node.child_nodes())
            min_y = min(child._y for child in node.child_nodes())
            fig.add_trace(
                go.Scatter(
                    x=[node._x, node._x],
                    y=[min_y, max_y],
                    mode="lines",
                    line=dict(color="black", width=0.5),
                    hoverinfo="none",
                )
            )

    # Nodes
    x = []
    y = []
    labels = []
    colors = []
    sizes = []

    for node in tree.leaf_node_iter():
        x.append(node._x)
        y.append(node._y)
        label = node.taxon.label
        labels.append(label)
        colors.append(leaf_colors.get(label, default_leaf_color))
        sizes.append(leaf_sizes.get(label, default_leaf_size))

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(color=colors, size=sizes),
            text=labels,
            hoverinfo="text",
        )
    )

    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="white",
        yaxis_autorange="reversed",
    )

    return fig
