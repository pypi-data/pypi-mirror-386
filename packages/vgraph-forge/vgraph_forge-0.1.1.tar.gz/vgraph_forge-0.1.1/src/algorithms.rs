// This file contains implementations of algorithms related to visibility graphs.

use crate::graph::{HorizontalVisibilityGraph, VisibilityGraph};

/// Options for building a visibility graph.
#[derive(Clone, Copy, Debug)]
pub struct BuildOptions {
    pub skip_adjacent: bool,
    pub use_horizontal: bool,
}

/// Errors that can occur while computing motif scores for sliding windows.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MotifError {
    WindowSizeZero,
    WindowSizeExceedsSeries,
}

impl Default for BuildOptions {
    fn default() -> Self {
        Self {
            skip_adjacent: false,
            use_horizontal: false,
        }
    }
}

fn normalize_indices(len: usize, i: usize, j: usize) -> Option<(usize, usize)> {
    if i >= len || j >= len {
        return None;
    }
    if i <= j {
        Some((i, j))
    } else {
        Some((j, i))
    }
}

/// Builds the Natural Visibility Graph (NVG) for the provided scalar time series.
/// Each sample is mapped to `(index as f64, value)` and connected if every
/// intermediate point lies strictly below the connecting line segment.
pub fn build_visibility_graph(time_series: &[f64]) -> VisibilityGraph {
    build_visibility_graph_with_options(time_series, BuildOptions::default())
}

/// Builds the Horizontal Visibility Graph (HVG) for the provided scalar time series.
pub fn build_horizontal_visibility_graph(time_series: &[f64]) -> HorizontalVisibilityGraph {
    build_horizontal_visibility_graph_with_options(
        time_series,
        BuildOptions {
            skip_adjacent: false,
            use_horizontal: true,
        },
    )
}

/// Same as [`build_horizontal_visibility_graph`] but allows custom options.
pub fn build_horizontal_visibility_graph_with_options(
    time_series: &[f64],
    mut options: BuildOptions,
) -> HorizontalVisibilityGraph {
    options.use_horizontal = true;
    let graph = build_visibility_graph_with_options(time_series, options);
    HorizontalVisibilityGraph::from_visibility_graph(graph)
}

/// Same as [`build_visibility_graph`] but allows customising builder behaviour.
pub fn build_visibility_graph_with_options(
    time_series: &[f64],
    options: BuildOptions,
) -> VisibilityGraph {
    let mut graph = VisibilityGraph::new();

    for (idx, &value) in time_series.iter().enumerate() {
        graph.add_vertex_internal(idx as f64, value);
    }

    for i in 0..time_series.len() {
        for j in (i + 1)..time_series.len() {
            if options.skip_adjacent && j == i + 1 {
                continue;
            }

            let visible = if options.use_horizontal {
                indices_are_horizontally_visible(time_series, i, j)
            } else {
                indices_are_visible(time_series, i, j)
            };

            if visible {
                graph.add_edge_internal(i, j);
            }
        }
    }

    graph
}

/// Returns the values strictly between the two indices in the provided series.
pub fn subseries_between(time_series: &[f64], i: usize, j: usize) -> Option<Vec<f64>> {
    let len = time_series.len();
    let (start, end) = normalize_indices(len, i, j)?;

    if end <= start + 1 {
        return Some(Vec::new());
    }

    Some(time_series[start + 1..end].to_vec())
}

/// Builds a visibility graph restricted to the samples between the two indices (inclusive).
pub fn build_subgraph_between(
    time_series: &[f64],
    i: usize,
    j: usize,
    options: BuildOptions,
) -> Option<VisibilityGraph> {
    let len = time_series.len();
    let (start, end) = normalize_indices(len, i, j)?;

    if start == end {
        let mut graph = VisibilityGraph::new();
        graph.add_vertex_internal(start as f64, time_series[start]);
        return Some(graph);
    }

    let mut graph = VisibilityGraph::new();

    for idx in start..=end {
        graph.add_vertex_internal(idx as f64, time_series[idx]);
    }

    for left in start..=end {
        for right in (left + 1)..=end {
            if options.skip_adjacent && right == left + 1 {
                continue;
            }

            let visible = if options.use_horizontal {
                indices_are_horizontally_visible(time_series, left, right)
            } else {
                indices_are_visible(time_series, left, right)
            };

            if visible {
                graph.add_edge_internal(left - start, right - start);
            }
        }
    }

    Some(graph)
}

/// Builds the horizontal visibility subgraph restricted to the span (inclusive) between indices.
pub fn build_horizontal_subgraph_between(
    time_series: &[f64],
    i: usize,
    j: usize,
    mut options: BuildOptions,
) -> Option<HorizontalVisibilityGraph> {
    options.use_horizontal = true;
    build_subgraph_between(time_series, i, j, options)
        .map(HorizontalVisibilityGraph::from_visibility_graph)
}

/// Checks whether two samples are mutually visible in the Natural Visibility Graph sense.
pub fn indices_are_visible(time_series: &[f64], i: usize, j: usize) -> bool {
    if i == j || i >= time_series.len() || j >= time_series.len() {
        return false;
    }

    let (left, right) = if i < j { (i, j) } else { (j, i) };
    let y_left = time_series[left];
    let y_right = time_series[right];
    let span = (right - left) as f64;

    for intermediate in (left + 1)..right {
        let t = (intermediate - left) as f64 / span;
        let y_interp = y_left + (y_right - y_left) * t;
        if time_series[intermediate] >= y_interp {
            return false;
        }
    }

    true
}

/// Checks visibility under the Horizontal Visibility Graph (HVG) definition.
pub fn indices_are_horizontally_visible(time_series: &[f64], i: usize, j: usize) -> bool {
    if i == j || i >= time_series.len() || j >= time_series.len() {
        return false;
    }

    let (left, right) = if i < j { (i, j) } else { (j, i) };
    let threshold = time_series[left].min(time_series[right]);

    for intermediate in (left + 1)..right {
        if time_series[intermediate] >= threshold {
            return false;
        }
    }

    true
}

/// Segment visibility helper that allows supplying explicit coordinates and obstacles.
pub fn segment_is_visible(
    p1: (f64, f64),
    p2: (f64, f64),
    obstacles: &[( (f64, f64), (f64, f64) )],
) -> bool {
    !obstacles.iter().any(|&(start, end)| intersects(p1, p2, start, end))
}

/// Computes motif scores for sliding windows over the provided time series.
///
/// The motif score is defined as `(edges_in_window - window_size + 1)` for each
/// contiguous window of length `window_size`.
pub fn window_motif_scores(
    time_series: &[f64],
    window_size: usize,
    options: BuildOptions,
) -> Result<Vec<i32>, MotifError> {
    let (n, window_count) = validate_window_params(time_series.len(), window_size)?;

    if window_count == 0 {
        return Ok(Vec::new());
    }

    let mut diff = vec![0i64; window_count + 1];

    for i in 0..n {
        for j in (i + 1)..n {
            if options.skip_adjacent && j == i + 1 {
                continue;
            }

            let visible = if options.use_horizontal {
                indices_are_horizontally_visible(time_series, i, j)
            } else {
                indices_are_visible(time_series, i, j)
            };

            if visible {
                record_visible_edge(&mut diff, window_size, window_count, i, j);
            }
        }
    }

    Ok(finalize_motif_counts(diff, window_count, window_size))
}

fn validate_window_params(series_len: usize, window_size: usize) -> Result<(usize, usize), MotifError> {
    if window_size == 0 {
        return Err(MotifError::WindowSizeZero);
    }
    if window_size > series_len {
        return Err(MotifError::WindowSizeExceedsSeries);
    }

    let window_count = series_len.saturating_sub(window_size) + 1;
    Ok((series_len, window_count))
}

fn record_visible_edge(
    diff: &mut [i64],
    window_size: usize,
    window_count: usize,
    i: usize,
    j: usize,
) {
    let start_min = if j + 1 >= window_size {
        j + 1 - window_size
    } else {
        0
    };
    if start_min > i {
        return;
    }

    let start_max = i.min(window_count - 1);
    if start_min > start_max {
        return;
    }

    diff[start_min] += 1;
    diff[start_max + 1] -= 1;
}

fn finalize_motif_counts(diff: Vec<i64>, window_count: usize, window_size: usize) -> Vec<i32> {
    let mut counts = Vec::with_capacity(window_count);
    let mut current = 0i64;

    for idx in 0..window_count {
        current += diff[idx];
        counts.push(current as i32);
    }

    let adjustment = window_size as i32 - 1;
    for count in &mut counts {
        *count -= adjustment;
    }

    counts
}

fn intersects(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64), p4: (f64, f64)) -> bool {
    let d1 = direction(p3, p4, p1);
    let d2 = direction(p3, p4, p2);
    let d3 = direction(p1, p2, p3);
    let d4 = direction(p1, p2, p4);

    if d1 != d2 && d3 != d4 {
        return true;
    }

    (d1 == 0 && on_segment(p3, p4, p1))
        || (d2 == 0 && on_segment(p3, p4, p2))
        || (d3 == 0 && on_segment(p1, p2, p3))
        || (d4 == 0 && on_segment(p1, p2, p4))
}

fn direction(p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) -> i32 {
    let val = (p2.1 - p1.1) * (p3.0 - p2.0) - (p2.0 - p1.0) * (p3.1 - p2.1);
    if val > 0.0 {
        1
    } else if val < 0.0 {
        -1
    } else {
        0
    }
}

fn on_segment(p1: (f64, f64), p2: (f64, f64), p: (f64, f64)) -> bool {
    p.0 <= p1.0.max(p2.0)
        && p.0 >= p1.0.min(p2.0)
        && p.1 <= p1.1.max(p2.1)
        && p.1 >= p1.1.min(p2.1)
}