// This file demonstrates basic usage of the visibility graphs library in Rust.
// It shows how to create a visibility graph and perform operations on it.

fn main() {
    // Example of creating a visibility graph
    let points = vec![(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)];
    let visibility_graph = VisibilityGraph::new(points);

    // Display the visibility graph
    println!("Visibility Graph: {:?}", visibility_graph);

    // Example of performing an operation, such as finding visible points
    let visible_points = visibility_graph.find_visible_points((1.0, 0.5));
    println!("Visible Points from (1.0, 0.5): {:?}", visible_points);
}