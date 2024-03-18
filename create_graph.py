import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


def create_regular_graph(size, degree):
    """Create a perfectly connected graph where each node has a specified degree."""
    # Generates a random regular graph where each node has the specified degree
    G = nx.random_regular_graph(degree, size)
    return nx.to_numpy_array(G)


def assign_colours(num_nodes, num_colours):
    """Assign a random colour to each node."""
    return np.random.choice(range(num_colours), size=num_nodes)


def count_conflicts(matrix, node_colors):
    conflicts = 0
    for i in range(len(matrix)):
        for j in range(i + 1, len(matrix)):
            if matrix[i, j] > 0 and node_colors[i] == node_colors[j]:
                conflicts += 1
    return conflicts


def read_saved_graph(path):
    # Read the saved graph
    netx_graph = nx.read_graphml(path)

    # Converting colours to integers
    node_colours = [int(netx_graph.nodes[node]["colour"]) for node in netx_graph.nodes()]

    colour_map = [f"C{colour}" for colour in node_colours]

    # Extract the matrix from the graph
    matrix = nx.to_numpy_array(netx_graph)

    # Calculate degrees
    node_degrees = np.sum(matrix, axis=1)

    # function to count conflicts.
    conflict_count = count_conflicts(matrix, node_colours)

    return colour_map, matrix, node_degrees, conflict_count


def main():
    # Creating a perfectly connected graph with 100 nodes, each having 6 degrees.
    matrix = create_regular_graph(100, 6)

    # Assigning colours.
    node_colours = assign_colours(100, 14)
    # Creating a NetworkX graph for visualisation.
    netx_graph = nx.from_numpy_array(matrix)

    # Assigning the colours to each node in the NetworkX graph and setting it as a node attribute.
    colour_map = [f"C{colour}" for colour in node_colours]
    for i, colour in enumerate(node_colours):
        netx_graph.nodes[i]["colour"] = str(colour)

    # Saving graph to file.
    nx.write_graphml(netx_graph, "baseline_graph.graphml")

    colour_map, matrix, node_degrees, conflict_count = read_saved_graph("baseline_graph.graphml")

    # Printing each node number and its degree
    print("Node Degrees:")
    for i, degree in enumerate(node_degrees):
        print(f"Node {i}: {degree} degrees")

    print("\nTotal Number of Conflicts:", conflict_count)

    # Visualise the graph
    plt.figure(figsize=(10, 10))
    nx.draw_networkx(netx_graph, node_color=colour_map, with_labels=True, node_size=500, font_size=10)
    plt.show()


if __name__ == "__main__":
    main()
