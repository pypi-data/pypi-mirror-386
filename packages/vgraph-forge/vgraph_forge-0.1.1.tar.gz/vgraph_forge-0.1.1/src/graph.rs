use pyo3::exceptions::PyIndexError;
use pyo3::prelude::*;

/// Visibility graph with vertices and undirected edges.
#[pyclass]
#[derive(Clone, Debug)]
pub struct VisibilityGraph {
    pub(crate) vertices: Vec<(f64, f64)>,
    pub(crate) edges: Vec<(usize, usize)>,
}

impl VisibilityGraph {
    pub fn new() -> Self {
        Self {
            vertices: Vec::new(),
            edges: Vec::new(),
        }
    }

    pub fn add_vertex_internal(&mut self, x: f64, y: f64) -> usize {
        self.vertices.push((x, y));
        self.vertices.len() - 1
    }

    pub fn add_edge_internal(&mut self, v1: usize, v2: usize) {
        if v1 == v2 {
            return;
        }

        let (a, b) = if v1 < v2 { (v1, v2) } else { (v2, v1) };
        if a >= self.vertices.len() || b >= self.vertices.len() {
            return;
        }

        if !self.edges.iter().any(|&(x, y)| x == a && y == b) {
            self.edges.push((a, b));
        }
    }

    pub fn vertices_slice(&self) -> &[(f64, f64)] {
        &self.vertices
    }

    pub fn edges_slice(&self) -> &[(usize, usize)] {
        &self.edges
    }

    pub fn node_count(&self) -> usize {
        self.vertices.len()
    }

    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }

    pub fn remove_vertex_internal(&mut self, idx: usize) -> bool {
        if idx >= self.vertices.len() {
            return false;
        }

        self.vertices.remove(idx);
        self.edges.retain(|&(u, v)| u != idx && v != idx);
        for edge in &mut self.edges {
            if edge.0 > idx {
                edge.0 -= 1;
            }
            if edge.1 > idx {
                edge.1 -= 1;
            }
        }
        true
    }

    pub fn remove_edge_internal(&mut self, v1: usize, v2: usize) -> bool {
        if v1 == v2 {
            return false;
        }

        let (a, b) = if v1 < v2 { (v1, v2) } else { (v2, v1) };
        let original_len = self.edges.len();
        self.edges.retain(|&(x, y)| !(x == a && y == b));
        original_len != self.edges.len()
    }
}

#[pymethods]
impl VisibilityGraph {
    #[new]
    fn py_new() -> Self {
        Self::new()
    }

    fn add_vertex(&mut self, x: f64, y: f64) -> usize {
        self.add_vertex_internal(x, y)
    }

    fn add_edge(&mut self, v1: usize, v2: usize) -> PyResult<()> {
        if v1 >= self.vertices.len() || v2 >= self.vertices.len() {
            return Err(PyIndexError::new_err("vertex index out of bounds"));
        }
        self.add_edge_internal(v1, v2);
        Ok(())
    }

    fn remove_vertex(&mut self, index: usize) -> PyResult<()> {
        if self.remove_vertex_internal(index) {
            Ok(())
        } else {
            Err(PyIndexError::new_err("vertex index out of bounds"))
        }
    }

    fn remove_edge(&mut self, v1: usize, v2: usize) -> bool {
        self.remove_edge_internal(v1, v2)
    }

    #[getter(vertices)]
    fn vertices_py(&self) -> Vec<(f64, f64)> {
        self.vertices.clone()
    }

    #[getter(edges)]
    fn edges_py(&self) -> Vec<(usize, usize)> {
        self.edges.clone()
    }

    #[pyo3(name = "node_count")]
    fn node_count_py(&self) -> usize {
        self.node_count()
    }

    #[pyo3(name = "edge_count")]
    fn edge_count_py(&self) -> usize {
        self.edge_count()
    }
}

/// Horizontal visibility graph wrapper that reuses the core graph structure.
#[pyclass]
#[derive(Clone, Debug)]
pub struct HorizontalVisibilityGraph {
    pub(crate) graph: VisibilityGraph,
}

impl HorizontalVisibilityGraph {
    pub fn from_visibility_graph(graph: VisibilityGraph) -> Self {
        Self { graph }
    }

    pub fn vertices_slice(&self) -> &[(f64, f64)] {
        self.graph.vertices_slice()
    }

    pub fn edges_slice(&self) -> &[(usize, usize)] {
        self.graph.edges_slice()
    }

    pub fn node_count(&self) -> usize {
        self.graph.node_count()
    }

    pub fn edge_count(&self) -> usize {
        self.graph.edge_count()
    }
}

#[pymethods]
impl HorizontalVisibilityGraph {
    #[new]
    fn py_new() -> Self {
        Self {
            graph: VisibilityGraph::new(),
        }
    }

    fn add_vertex(&mut self, x: f64, y: f64) -> usize {
        self.graph.add_vertex_internal(x, y)
    }

    fn add_edge(&mut self, v1: usize, v2: usize) -> PyResult<()> {
        self.graph.add_edge(v1, v2)
    }

    fn remove_vertex(&mut self, index: usize) -> PyResult<()> {
        if self.graph.remove_vertex_internal(index) {
            Ok(())
        } else {
            Err(PyIndexError::new_err("vertex index out of bounds"))
        }
    }

    fn remove_edge(&mut self, v1: usize, v2: usize) -> bool {
        self.graph.remove_edge_internal(v1, v2)
    }

    #[getter(vertices)]
    fn vertices_py(&self) -> Vec<(f64, f64)> {
        self.graph.vertices.clone()
    }

    #[getter(edges)]
    fn edges_py(&self) -> Vec<(usize, usize)> {
        self.graph.edges.clone()
    }

    #[pyo3(name = "node_count")]
    fn node_count_py(&self) -> usize {
        self.node_count()
    }

    #[pyo3(name = "edge_count")]
    fn edge_count_py(&self) -> usize {
        self.edge_count()
    }
}