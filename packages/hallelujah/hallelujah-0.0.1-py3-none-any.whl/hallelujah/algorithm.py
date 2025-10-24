# Created on 26/07/2025
# Author: Frank Vega

import itertools
from . import utils

import networkx as nx
import math

def find_vertex_cover(graph):
    """
    Compute a near-optimal vertex cover for an undirected graph with an approximation ratio under 2.

    A vertex cover is a set of vertices such that every edge in the graph is incident
    to at least one vertex in the set. This function finds an approximate solution
    using a polynomial-time reduction approach.

    Args:
        graph (nx.Graph): Input undirected graph.

    Returns:
       set: A set of vertex indices representing the approximate vertex cover set.
             Returns an empty set if the graph is empty or has no edges.

    Raises:
        ValueError: If input is not a NetworkX Graph object.
    """
    def min_weighted_vertex_cover_max_degree_1(G, weight = 'weight'):
        """
        Find the minimum weighted vertex cover for a graph with maximum degree 1.

        In such graphs, each connected component is either:
        - An isolated vertex (degree 0): not needed in vertex cover (no edges to cover)
        - An edge (two vertices of degree 1): choose the one with minimum weight

        Args:
            G: NetworkX undirected graph with maximum degree 1
            weight: Name of the weight attribute (default: 'weight')

        Returns:
            Set of vertices forming the minimum weighted vertex cover
        """
        vertex_cover = set()
        visited = set()

        for node in G.nodes():
            if node in visited:
                continue

            degree = G.degree(node)

            if degree == 0:
                # Isolated vertex - no edges to cover, skip
                visited.add(node)

            elif degree == 1:
                # Part of an edge - choose the vertex with minimum weight
                neighbor = list(G.neighbors(node))[0]

                if neighbor not in visited:
                    # Get weights (default to 1 if not specified)
                    node_weight = G.nodes[node].get(weight, 1)
                    neighbor_weight = G.nodes[neighbor].get(weight, 1)

                    # Choose the vertex with minimum weight
                    # In case of tie, choose lexicographically smaller (for determinism)
                    if (node_weight < neighbor_weight or
                        (node_weight == neighbor_weight and node < neighbor)):
                        vertex_cover.add(node)
                    else:
                        vertex_cover.add(neighbor)

                    visited.add(node)
                    visited.add(neighbor)

        return vertex_cover

    def covering_via_reduction_max_degree_1(graph):
        """
        Internal helper function that reduces the vertex cover problem to maximum degree 1 case.

        This function implements a polynomial-time reduction technique:
        1. For each vertex u with degree k, replace it with k auxiliary vertices
        2. Each auxiliary vertex connects to one of u's original neighbors with weight 1/sqrt(k)
        3. Solve the resulting max-degree-1 problem optimally using a greedy algorithm
        
        Args:
            graph (nx.Graph): Connected component subgraph to process

        Returns:
            set: Vertices in the approximate vertex cover for this component
        """
        # Create a working copy to avoid modifying the original graph
        G = graph.copy()
        weights = {}

        # Reduction step: Replace each vertex with auxiliary vertices
        # This transforms the problem into a maximum degree 1 case
        for u in list(graph.nodes()):  # Use list to avoid modification during iteration
            neighbors = list(G.neighbors(u))  # Get neighbors before removing node
            G.remove_node(u)  # Remove original vertex
            k = len(neighbors)  # Degree of original vertex

            # Create auxiliary vertices and connect each to one neighbor
            for i, v in enumerate(neighbors):
                aux_vertex = (u, i)  # Auxiliary vertex naming: (original_vertex, index)
                G.add_edge(aux_vertex, v)
                # Weight 1/sqrt(k) balances Cauchy-Schwarz bounds for <2 approximation
                weights[aux_vertex] = 1 / math.sqrt(k)  # k >= 1 post-isolate removal

        # Set node weights for the weighted vertex cover algorithm
        nx.set_node_attributes(G, weights, 'weight')

        # Apply greedy algorithm for minimum weighted vertex cover (optimal)
        vertex_cover = min_weighted_vertex_cover_max_degree_1(G)
        # Extract original vertices from auxiliary vertex pairs
        greedy_solution = {u for u, _ in vertex_cover}

        return greedy_solution

    if not isinstance(graph, nx.Graph):
        raise ValueError("Input must be an undirected NetworkX Graph.")

    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        return set()

    working_graph = graph.copy()
    working_graph.remove_edges_from(list(nx.selfloop_edges(working_graph)))
    working_graph.remove_nodes_from(list(nx.isolates(working_graph)))

    if working_graph.number_of_nodes() == 0:
        return set()

    approximate_vertex_cover = set()

    for component in nx.connected_components(working_graph):
        component_subgraph = working_graph.subgraph(component).copy()

        # Reduction-based solution
        solution = covering_via_reduction_max_degree_1(component_subgraph)
        
        approximate_vertex_cover.update(solution)

    return approximate_vertex_cover

def find_vertex_cover_brute_force(graph):
    """
    Computes an exact minimum vertex cover in exponential time.

    Args:
        graph: A NetworkX Graph.

    Returns:
        A set of vertex indices representing the exact vertex cover, or None if the graph is empty.
    """

    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        return None

    n_vertices = len(graph.nodes())

    for k in range(1, n_vertices + 1): # Iterate through all possible sizes of the cover
        for candidate in itertools.combinations(graph.nodes(), k):
            cover_candidate = set(candidate)
            if utils.is_vertex_cover(graph, cover_candidate):
                return cover_candidate
                
    return None



def find_vertex_cover_approximation(graph):
    """
    Computes an approximate vertex cover in polynomial time with an approximation ratio of at most 2 for undirected graphs.

    Args:
        graph: A NetworkX Graph.

    Returns:
        A set of vertex indices representing the approximate vertex cover, or None if the graph is empty.
    """

    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        return None

    #networkx doesn't have a guaranteed minimum vertex cover function, so we use approximation
    vertex_cover = nx.approximation.min_weighted_vertex_cover(graph)
    return vertex_cover