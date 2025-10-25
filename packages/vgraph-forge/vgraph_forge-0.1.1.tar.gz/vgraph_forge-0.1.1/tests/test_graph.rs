// This file contains unit tests for the graph module, ensuring that the graph-related functionalities work as expected.

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_graph_creation() {
        let graph = Graph::new();
        assert_eq!(graph.nodes.len(), 0);
        assert_eq!(graph.edges.len(), 0);
    }

    #[test]
    fn test_add_node() {
        let mut graph = Graph::new();
        graph.add_node(1);
        assert_eq!(graph.nodes.len(), 1);
        assert!(graph.nodes.contains(&1));
    }

    #[test]
    fn test_add_edge() {
        let mut graph = Graph::new();
        graph.add_node(1);
        graph.add_node(2);
        graph.add_edge(1, 2);
        assert_eq!(graph.edges.len(), 1);
        assert!(graph.edges.contains(&(1, 2)));
    }

    #[test]
    fn test_remove_node() {
        let mut graph = Graph::new();
        graph.add_node(1);
        graph.remove_node(1);
        assert_eq!(graph.nodes.len(), 0);
    }

    #[test]
    fn test_remove_edge() {
        let mut graph = Graph::new();
        graph.add_node(1);
        graph.add_node(2);
        graph.add_edge(1, 2);
        graph.remove_edge(1, 2);
        assert_eq!(graph.edges.len(), 0);
    }
}