import random
import networkx as nx
import copy
import csv

import numpy as np


def read_saved_graph(path):
    return nx.read_graphml(path)


def assign_initial_colours(graph, colours_range):
    for node in graph.nodes():
        graph.nodes[node]["colour"] = random.choice(colours_range)


def update_node_colours(graph, colours_range):
    for node in graph.nodes():
        neighbours = list(graph.neighbors(node))
        neighbours_colours = [graph.nodes[n]["colour"] for n in neighbours]
        available_colours = set(colours_range) - set(neighbours_colours)
        if available_colours:
            graph.nodes[node]["colour"] = random.choice(list(available_colours))


def count_conflicts(graph):
    conflicts = 0
    for node in graph.nodes():
        node_colour = graph.nodes[node]["colour"]
        for neighbour in graph.neighbors(node):
            neighbour_colour = graph.nodes[neighbour]["colour"]
            if node_colour == neighbour_colour:
                conflicts += 1
    return conflicts // 2


def simulate_colouring(graph_path, experiment_runs=100):
    netx_graph_original = read_saved_graph(graph_path)
    baseline_results = []
    colour_amount = []

    for experiment_run in range(1, experiment_runs + 1):
        netx_graph = copy.deepcopy(netx_graph_original)
        num_colours = 0
        conflicts = 1

        while conflicts != 0:
            num_colours += 1
            colours_range = list(range(num_colours))

            assign_initial_colours(netx_graph, colours_range)
            update_node_colours(netx_graph, colours_range)

            conflicts = count_conflicts(netx_graph)
            baseline_results.append((experiment_run, num_colours, conflicts))

        print(f"Experiment run {experiment_run} completed. Final number of colours used: {num_colours}. Conflicts: {conflicts}")
        colour_amount.append(num_colours)

    print("Min number of colours used: ", np.min(colour_amount))
    print("Max number of colours used: ", np.max(colour_amount))

    # write to a CSV file
    with open("baseline_add_colours.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Experiment Run", "Number of Colours", "Number of Conflicts"])
        for result in baseline_results:
            writer.writerow(result)


if __name__ == "__main__":
    graph_path = "baseline_graph.graphml"
    simulate_colouring(graph_path)
