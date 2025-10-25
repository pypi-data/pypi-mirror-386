use pyo3::exceptions::{PyIndexError, PyValueError};
use pyo3::prelude::*;

mod algorithms;
mod graph;

pub use algorithms::{
	build_visibility_graph,
	build_visibility_graph_with_options,
	build_subgraph_between,
	build_horizontal_subgraph_between,
	build_horizontal_visibility_graph,
	build_horizontal_visibility_graph_with_options,
	indices_are_horizontally_visible,
	indices_are_visible,
	segment_is_visible,
	subseries_between,
	window_motif_scores,
	BuildOptions,
	MotifError,
};
pub use graph::{HorizontalVisibilityGraph, VisibilityGraph};

#[pyfunction(name = "build_visibility_graph")]
fn build_visibility_graph_py(
	time_series: Vec<f64>,
	skip_adjacent: Option<bool>,
) -> PyResult<VisibilityGraph> {
	let options = algorithms::BuildOptions {
		skip_adjacent: skip_adjacent.unwrap_or(false),
		..Default::default()
	};
	Ok(algorithms::build_visibility_graph_with_options(&time_series, options))
}

#[pyfunction(name = "build_horizontal_visibility_graph")]
fn build_horizontal_visibility_graph_py(
	time_series: Vec<f64>,
	skip_adjacent: Option<bool>,
) -> PyResult<HorizontalVisibilityGraph> {
	let options = algorithms::BuildOptions {
		skip_adjacent: skip_adjacent.unwrap_or(false),
		use_horizontal: true,
	};
	Ok(algorithms::build_horizontal_visibility_graph_with_options(
		&time_series,
		options,
	))
}

#[pyfunction(name = "indices_are_visible")]
fn indices_are_visible_py(time_series: Vec<f64>, i: usize, j: usize) -> bool {
	algorithms::indices_are_visible(&time_series, i, j)
}

#[pyfunction(name = "indices_are_horizontally_visible")]
fn indices_are_horizontally_visible_py(time_series: Vec<f64>, i: usize, j: usize) -> bool {
	algorithms::indices_are_horizontally_visible(&time_series, i, j)
}

#[pyfunction(name = "subseries_between")]
fn subseries_between_py(time_series: Vec<f64>, i: usize, j: usize) -> PyResult<Vec<f64>> {
	if i >= time_series.len() || j >= time_series.len() {
		return Err(PyIndexError::new_err("index out of bounds"));
	}

	Ok(
		algorithms::subseries_between(&time_series, i, j)
			.unwrap_or_else(|| Vec::new()),
	)
}

#[pyfunction(name = "build_subgraph_between")]
fn build_subgraph_between_py(
	time_series: Vec<f64>,
	i: usize,
	j: usize,
	skip_adjacent: Option<bool>,
) -> PyResult<VisibilityGraph> {
	if i >= time_series.len() || j >= time_series.len() {
		return Err(PyIndexError::new_err("index out of bounds"));
	}

	let options = algorithms::BuildOptions {
		skip_adjacent: skip_adjacent.unwrap_or(false),
		..Default::default()
	};

	algorithms::build_subgraph_between(&time_series, i, j, options)
		.ok_or_else(|| PyIndexError::new_err("index out of bounds"))
}

#[pyfunction(name = "build_horizontal_subgraph_between")]
fn build_horizontal_subgraph_between_py(
	time_series: Vec<f64>,
	i: usize,
	j: usize,
	skip_adjacent: Option<bool>,
) -> PyResult<HorizontalVisibilityGraph> {
	if i >= time_series.len() || j >= time_series.len() {
		return Err(PyIndexError::new_err("index out of bounds"));
	}

	let options = algorithms::BuildOptions {
		skip_adjacent: skip_adjacent.unwrap_or(false),
		use_horizontal: true,
	};

	algorithms::build_horizontal_subgraph_between(&time_series, i, j, options)
		.ok_or_else(|| PyIndexError::new_err("index out of bounds"))
}

#[pyfunction(name = "segment_is_visible")]
fn segment_is_visible_py(
	p1: (f64, f64),
	p2: (f64, f64),
	obstacles: Vec<((f64, f64), (f64, f64))>,
) -> bool {
	algorithms::segment_is_visible(p1, p2, &obstacles)
}

#[pyfunction(name = "horizontal_window_motif_scores")]
fn horizontal_window_motif_scores_py(
	time_series: Vec<f64>,
	window_size: usize,
	skip_adjacent: Option<bool>,
) -> PyResult<Vec<i32>> {
	let options = algorithms::BuildOptions {
		skip_adjacent: skip_adjacent.unwrap_or(false),
		use_horizontal: true,
	};

	match algorithms::window_motif_scores(&time_series, window_size, options) {
		Ok(scores) => Ok(scores),
		Err(MotifError::WindowSizeZero) => Err(PyValueError::new_err("window size must be greater than zero")),
		Err(MotifError::WindowSizeExceedsSeries) => Err(PyValueError::new_err(
			"window size must be less than or equal to len(time_series)",
		)),
	}
}

#[pymodule]
fn vgraph_forge(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
	m.add_class::<VisibilityGraph>()?;
	m.add_class::<HorizontalVisibilityGraph>()?;
	m.add_function(wrap_pyfunction!(build_visibility_graph_py, m)?)?;
	m.add_function(wrap_pyfunction!(build_horizontal_visibility_graph_py, m)?)?;
	m.add_function(wrap_pyfunction!(indices_are_visible_py, m)?)?;
	m.add_function(wrap_pyfunction!(indices_are_horizontally_visible_py, m)?)?;
	m.add_function(wrap_pyfunction!(subseries_between_py, m)?)?;
	m.add_function(wrap_pyfunction!(build_subgraph_between_py, m)?)?;
	m.add_function(wrap_pyfunction!(build_horizontal_subgraph_between_py, m)?)?;
	m.add_function(wrap_pyfunction!(segment_is_visible_py, m)?)?;
	m.add_function(wrap_pyfunction!(horizontal_window_motif_scores_py, m)?)?;
	Ok(())
}