import csv
import random
import statistics

import networkx as nx
import copy
import numpy as np
from edge_rewiring import rewire_edges


class ColourAgent:
    """ Represents an agent responsible for selecting a colour for a node in a graph.
    This agent is designed to be used in a graph coloring problem, where each node of
    the graph is assigned a colour such that no two adjacent nodes share the same colour.
    The agent chooses its initial colour randomly from an incrementing provided range and
    has the capability to perceive the colours of adjacent nodes and decide on a new colour to
    resolve conflicts.
    """

    def __init__(self, node_id, initial_colour, colours_range, graph, colour_score):
        self.intended_colour = None
        self.graph = graph
        self.colour_scores = colour_score
        self.node_id = node_id
        self.colours_range = colours_range
        if initial_colour not in colours_range:
            self.colour = None
        else:
            self.colour = initial_colour

    def perceive_environment(self, graph):
        # Get a list of nodes that are neighbours of the current node.
        neighbours = list(graph.neighbors(self.node_id))
        # For each neighbour, retrieve their colour by accessing the "colour" attribute of their associated agent.
        neighbours_colours = [graph.nodes[n]["agent"].colour for n in neighbours]
        return neighbours_colours

    def decide_new_colour(self, neighbours_colours):

        available_colours = set(self.colours_range) - set(neighbours_colours) - {self.colour}
        if not available_colours:
            self.colour = self.colour_negotiation(neighbours_colours)
            return True

        if self.colour in neighbours_colours or self.colour is None:
            # print("Self Colour:", self.colour)
            self.intended_colour = self.colour_negotiation(available_colours)
            # print("Intended Colour:",self.intended_colour)

            if self.intended_colour is None or True:
                self.colour = self.intended_colour
                self.update_colour_score()
                return True
            else:
                return False
        else:
            return True

    def colour_negotiation(self, colour_choices):
        optimal_colour = random.choice(list(colour_choices))
        max_score = -float("inf")
        for colour in colour_choices:
            score = self.assess_colour(colour)
            if score > max_score:
                max_score = score
                optimal_colour = colour
        return optimal_colour

    def update_colour_score(self):
        for neighbour in self.graph.neighbors(self.node_id):
            if self.graph.nodes[neighbour]["agent"].colour == self.colour:
                self.colour_scores[self.colour] -= 10
                break
        else:
            self.colour_scores[self.colour] += 10

    def assess_colour(self, colour):
        my_degree = len(list(self.graph.neighbors(self.node_id)))
        my_score = self.colour_scores.get(colour, 0)

        for neighbour_id in self.graph.neighbors(self.node_id):
            neighbour_agent = self.graph.nodes[neighbour_id]["agent"]
            neighbour_degree = len(list(self.graph.neighbors(neighbour_id)))
            neighbour_score = neighbour_agent.colour_scores.get(colour, 0)

            if my_degree < neighbour_degree or (my_degree == neighbour_degree and my_score < neighbour_score):
                my_score -= 1
            elif my_degree == neighbour_degree and my_score == neighbour_score and self.node_id < neighbour_id:
                my_score -= 1
            else:
                my_score += 1
        return my_score


def read_saved_graph(path):
    graph = nx.read_graphml(path)
    colours_range = list(range(14))
    for node in graph.nodes():
        # colour is stored as a string in the GraphML file
        initial_colour = int(graph.nodes[node]['colour'])  # Convert to int
        # Initialise the agent with the colour
        graph.nodes[node]['agent'] = ColourAgent(node, initial_colour, colours_range, graph, None)
    return graph


def simulate_colouring(graph, colours_range, colour_score):
    # Initialise each node in the graph with a ColourAgent. Each agent is given
    # a unique node identifier (node_id) and the range of possible colours it can choose from.
    for node in graph.nodes():
        initial_colour = int(graph.nodes[node]['colour'])
        graph.nodes[node]["agent"] = ColourAgent(node, initial_colour, colours_range, graph, colour_score)
    # Run the simulation in each iteration, every agent will:
    # 1. Perceive its environment by looking at the colours of its neighbours.
    # 2. Decide on a new colour that does not conflict with its neighbours" colours.
    for node in graph.nodes():
        agent = graph.nodes[node]["agent"]
        neighbours_colours = agent.perceive_environment(graph)
        if not agent.decide_new_colour(neighbours_colours):
            return False
    return True


def count_conflicts(graph):
    conflicts = 0
    # Iterate over all nodes in the graph retrieving colour.
    for node in graph.nodes():
        node_colour = graph.nodes[node]["agent"].colour
        # Iterate over all neighbours of current node retrieving colour.
        for neighbour in graph.neighbors(node):
            neighbour_colour = graph.nodes[neighbour]["agent"].colour
            # Increment the conflict counter if the colours match.
            if node_colour == neighbour_colour:
                conflicts += 1
    return conflicts // 2


def main():
    netx_graph = None
    # Path to saved GraphML file
    graph_path = "baseline_graph.graphml"
    # Read the saved graph
    netx_graph_original = read_saved_graph(graph_path)
    # List to store results
    num_of_conflict_free = 0
    conflicts_list = []
    baseline_results = []
    cal_conflicts = []

    for experiment_run in range(1, 101):
        # Deep copy of graph
        netx_graph = copy.deepcopy(netx_graph_original)
        conflicts = count_conflicts(netx_graph)
        colours_range = list(range(14))
        colour_score = {colour: random.randint(0, 10) for colour in colours_range}
        experiment_terminated_early = False
        inner_counter = 0

        # Apply agent-based coloring
        while not experiment_terminated_early:
            inner_counter += 1
            if inner_counter == 10:
                # print(f"Inner Counter: Experiment: {experiment_run}, Colours Used: {len(colours_range)}, Conflicts: {conflicts}")
                break
            if len(colours_range) > 0:
                colours_range.remove(random.choice(colours_range))
            if len(colours_range) == 8:
                rewire_edges(netx_graph, 0.1)
            experiment_terminated_early = not simulate_colouring(netx_graph, colours_range, colour_score)

            conflicts = count_conflicts(netx_graph)
            baseline_results.append((experiment_run, len(colours_range), conflicts))
            cal_conflicts.append(conflicts)

        if conflicts == 0:
            num_of_conflict_free += 1
        else:
            conflicts_list.append(conflicts)

        print(f"Run: {experiment_run}, Colours used: {len(colours_range)} Conflicts: {conflicts}")

    print("Max number of conflicts found on over all experiments: ", np.max(conflicts_list))
    percentage = num_of_conflict_free / 100
    print("Percentage of conflict free resolutions: ", percentage)
    with open("negotiate_agent_remove_100_perturbation_10_8.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Experiment Run", "Number of Colours", "Number of Conflicts"])
        for result in baseline_results:
            writer.writerow(result)
    # Calculate statistics
    min_val = min(cal_conflicts)
    max_val = max(cal_conflicts)
    mean_val = statistics.mean(cal_conflicts)
    std_dev = statistics.stdev(cal_conflicts)

    # Output the results
    print(f"Minimum: {min_val}")
    print(f"Maximum: {max_val}")
    print(f"Mean: {mean_val}")
    print(f"Standard Deviation: {std_dev}")


if __name__ == "__main__":
    main()
