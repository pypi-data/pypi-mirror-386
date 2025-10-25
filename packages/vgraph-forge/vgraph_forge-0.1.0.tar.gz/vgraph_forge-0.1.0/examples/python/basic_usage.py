"""Minimal Python demo for the visibility_graphs bindings."""

from __future__ import annotations

from visibility_graphs import build_visibility_graph, indices_are_visible


def main() -> None:
    # Example scalar time series: x-axis is the sample index, y-axis the value.
    series = [1.0, 3.2, 2.5, 4.0, 1.7]

    graph = build_visibility_graph(series)
    print("vertices:", graph.vertices)
    print("edges:", graph.edges)

    i, j = 1, 3
    print(f"indices {i} and {j} visible?", indices_are_visible(series, i, j))

if __name__ == "__main__":
    main()
