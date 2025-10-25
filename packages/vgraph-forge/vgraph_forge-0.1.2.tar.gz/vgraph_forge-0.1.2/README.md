# vgraph-forge

This project provides a Rust-powered library for creating and manipulating visibility graphs, with first-class Python bindings generated via [PyO3](https://pyo3.rs/) and [maturin](https://github.com/PyO3/maturin). It currently implements both the Natural Visibility Graph (NVG) and the Horizontal Visibility Graph (HVG), exposing the same data structures to Rust and Python callers.

## Features

- Efficient storage for visibility graphs, including helper methods to inspect vertices and edges.
- Natural and horizontal visibility graph builders for scalar time-series data.
- Optional adjacency filtering and subgraph extraction utilities.
- Easy integration with Python via a compiled extension module.

## Installation

Once published on PyPI, the package can be installed with `pip`:

```bash
pip install vgraph-forge
```

During development (or before publishing), build a local wheel with `maturin build --release` and install the resulting artifact from `target/wheels/` in your downstream project via `pip install <wheel>`. Only contributors building from source need Rust and maturin; consumers installing the wheel do not.

## Usage

Below is a compact Python example that constructs both NVG and HVG representations from a simple time series:

```python
from vgraph_forge import (
	build_visibility_graph,
	build_horizontal_visibility_graph,
)

series = [1.0, 3.2, 2.5, 4.0, 1.7]

# Natural visibility graph (NVG)
nvg = build_visibility_graph(series)
print("NVG vertices:", nvg.vertices)
print("NVG edges:", nvg.edges)

# Horizontal visibility graph (HVG) with adjacent-edge filtering
hvg = build_horizontal_visibility_graph(series, skip_adjacent=True)
print("HVG edges (skip adjacent):", hvg.edges)

print("NVG edge count:", nvg.edge_count())
print("HVG node count:", hvg.node_count())
```

See `examples/python/plot_visibility_graph.py` for a Matplotlib visualization helper and `examples/python/visibility_from_csv.py` for a CSV-to-edge-list CLI.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.