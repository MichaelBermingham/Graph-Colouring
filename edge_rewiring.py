import random


def rewire_edges(graph, perturbation_level):
    num_edges = graph.number_of_edges()
    edges_to_rewire = int(num_edges * perturbation_level)
    edges = list(graph.edges())

    for _ in range(edges_to_rewire):
        edge1, edge2 = random.sample(edges, 2)
        new_edge1 = (edge1[0], edge2[1])
        new_edge2 = (edge2[0], edge1[1])

        # Remove old edges if not part of a multi-edge
        if not graph.has_edge(*new_edge1) and not graph.has_edge(*new_edge2):
            graph.remove_edge(*edge1)
            graph.remove_edge(*edge2)

            # Add new edges
            graph.add_edge(*new_edge1)
            graph.add_edge(*new_edge2)

            # Update the edge list
            edges.remove(edge1)
            edges.remove(edge2)
            edges.append(new_edge1)
            edges.append(new_edge2)
            