"""Python facade for the Rust-backed visibility_graphs extension."""

from typing import Optional

from .visibility_graphs import (
    HorizontalVisibilityGraph,
    VisibilityGraph,
    horizontal_window_motif_scores,
    build_horizontal_subgraph_between,
    build_horizontal_visibility_graph,
    build_visibility_graph,
    build_subgraph_between,
    indices_are_horizontally_visible,
    indices_are_visible,
    subseries_between,
    segment_is_visible,
)


def to_networkx_graph(
    graph: "VisibilityGraph | HorizontalVisibilityGraph",
    create_using: Optional[object] = None,
):
    """Return a NetworkX graph populated with the current vertices and edges."""

    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover - defer import error to caller
        raise ImportError("Installing networkx is required to export graphs") from exc

    if create_using is None:
        target = nx.Graph()
    elif isinstance(create_using, type):
        target = create_using()
    else:
        target = create_using
        target.clear()

    # Preserve the original series coordinate and value on each node for downstream use.
    target.add_nodes_from(
        (idx, {"x": coords[0], "y": coords[1], "value": coords[1]})
        for idx, coords in enumerate(graph.vertices)
    )
    target.add_edges_from(graph.edges)
    return target


__all__ = [
    "HorizontalVisibilityGraph",
    "VisibilityGraph",
    "horizontal_window_motif_scores",
    "build_horizontal_subgraph_between",
    "build_horizontal_visibility_graph",
    "build_visibility_graph",
    "build_subgraph_between",
    "indices_are_horizontally_visible",
    "indices_are_visible",
    "subseries_between",
    "segment_is_visible",
    "to_networkx_graph",
]
