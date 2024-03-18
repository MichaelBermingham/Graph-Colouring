import random
import networkx as nx
import matplotlib.pyplot as plt
import copy
import csv

import numpy as np


class ColourAgent:
    """ Represents an agent responsible for selecting a colour for a node in a graph.
    This agent is designed to be used in a graph coloring problem, where each node of
    the graph is assigned a colour such that no two adjacent nodes share the same colour.
    The agent chooses its initial colour randomly from an incrementing provided range and
    has the capability to perceive the colours of adjacent nodes and decide on a new colour to
    resolve conflicts.

    Attributes:
    node_id (int): The unique identifier for the node this agent represents.
    colour (int): The current colour assigned to this agent"s node.
    colours_range (list of int): A list of possible colours the agent can choose from.
    """

    def __init__(self, node_id, initial_colour, colours_range):
        self.node_id = node_id
        self.colours_range = colours_range
        if initial_colour not in colours_range:
            self.colour = None
        else:
            self.colour = initial_colour
        # self.colour = initial_colour  # Setting colour from GraphML file

    def perceive_environment(self, graph):
        """ Perceive the environment by identifying the colours of neighbouring nodes.
        :param graph: (networkx.Graph) The graph object representing the network where agents reside.
        :return: (neighbours_colours) A list of colours of the neighbouring nodes.
        """
        # Get a list of nodes that are neighbours of the current node.
        neighbours = list(graph.neighbors(self.node_id))
        # For each neighbour, retrieve their colour by accessing the "colour" attribute of their associated agent.
        neighbours_colours = [graph.nodes[n]["agent"].colour for n in neighbours]
        return neighbours_colours

    def decide_new_colour(self, neighbours_colours):
        """ Decide on a new colour different from all neighbours.
        :param neighbours_colours: (list) A list of colours currently used by neighbouring nodes.
        :return: None.
        """
        # Subtracting current colour and the set of neighbours colours
        # from the set of all possible colours the agent can choose from.
        available_colours = set(self.colours_range) - set(neighbours_colours) - {self.colour}

        # Randomly select one and assign it as the agents new colour.
        if self.colour in neighbours_colours or self.colour is None:
            if not available_colours:
                return False
            else:
                self.colour = random.choice(list(available_colours))
                return True
        else:
            return True


def read_saved_graph(path):
    graph = nx.read_graphml(path)
    colours_range = list(range(14))
    for node in graph.nodes():
        # colour is stored as a string in the GraphML file
        initial_colour = int(graph.nodes[node]['colour'])  # Convert to int
        # Initialise the agent with the colour
        graph.nodes[node]['agent'] = ColourAgent(node, initial_colour, colours_range)
    return graph


def simulate_colouring(graph, colours_range):
    """ Simulate the agent-based colouring process.

    This function initialises each node in the graph with a ColourAgent, which then
    iteratively perceives its environment (the colours of its neighbours) and decides
    on a new colour for itself based on this perception. The goal is to minimise colour
    conflicts among neighbouring nodes over several iterations.

    :param graph: (networkx.Graph) The graph object representing the network of nodes.
    :param colours_range: (list) A list of possible colours that agents can choose from.
    :return: None.
    """
    # Initialise each node in the graph with a ColourAgent. Each agent is given
    # a unique node identifier (node_id) and the range of possible colours it can choose from.
    for node in graph.nodes():
        initial_colour = int(graph.nodes[node]['colour'])
        if initial_colour not in colours_range:
            initial_colour = None
        graph.nodes[node]["agent"] = ColourAgent(node, initial_colour, colours_range)
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
    """ Count the number of conflicting edges in the graph where connected nodes have the same colour.
    This function iterates through each node in the graph, examining the colours of its neighbours to
    determine if there are any conflicts. A conflict occurs when a node and its neighbour share the
    same colour. The function counts the total number of conflicts in the graph. Since each conflict
    is identified from the perspective of both nodes involved, the final count is divided by 2 to avoid duplication.

    :param graph: (networkx.Graph) The graph object where nodes represent agents, and edges
                                represent connections between agents. Each agent (node) has
                                a "colour" attribute assigned.
    :return int: (conflicts) The total number of unique conflicting edges in the graph, where connected
                            nodes (agents) have been assigned the same colour.
    """
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
    conflicts_list = []
    colours_len_list = []
    baseline_results = []

    for experiment_run in range(1, 50):
        # Deep copy of graph
        netx_graph = copy.deepcopy(netx_graph_original)
        conflicts = count_conflicts(netx_graph)
        colours_range = list(range(14))
        removed_colours = []
        inner_count = 0

        while len(colours_range) > 5:
            if conflicts == 0:
                # print(f"Run {experiment_run}")
                break
            if inner_count == 10:
                print(f"Inner Counter: Experiment {experiment_run}, Colours Used: {len(colours_range)}, Conflicts: {conflicts}")
                break
            while conflicts > 0:
                if inner_count == 10:
                    break
                experiment_terminated_early = False

                # Apply agent-based coloring
                while not experiment_terminated_early:
                    if inner_count == 10:
                        break

                    inner_count += 1

                    if len(colours_range) > 5:
                        removing = random.choice(colours_range)
                        removed_colours.append(removing)
                        colours_range.remove(removing)

                    experiment_terminated_early = not simulate_colouring(netx_graph, colours_range)
                    conflicts = count_conflicts(netx_graph)
                    conflicts_list.append(conflicts)
                    colours_len_list.append(len(colours_range))
                    baseline_results.append((experiment_run, len(colours_range), conflicts))

                    if len(colours_range) == 5:
                        if conflicts == 0:
                            break
                        else:
                            continue

                    # print(f"Run: {experiment_run}, Colours Used: {len(colours_range)}, Conflicts: {conflicts}")

                    if experiment_terminated_early:
                        # print(
                        #     f"Experiment Number: {experiment_run}, Breaking with Conflicts: {conflicts}, Colour Range: {len(colours_range)}, Removed Colours: {removed_colours}")
                        conflicts_list.append(conflicts)
                        colours_len_list.append(len(colours_range))
                        break

        print(f"Experiment: {experiment_run}, Colours: {len(colours_range)}, Conflicts: {conflicts}")
    # with open("no_negotiate_agent_remove_random_50.csv", "w", newline="") as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(["Experiment Run", "Number of Colours", "Number of Conflicts"])
    #     for result in baseline_results:
    #         writer.writerow(result)

    # min_con = np.min(conflicts_list)
    # max_con = np.max(conflicts_list)
    # mean_con = np.mean(conflicts_list)
    # std_dev_con = np.std(conflicts_list)
    # min_cl = np.min(colours_len_list)
    # max_cl = np.max(colours_len_list)
    # mean_cl = np.mean(colours_len_list)
    # std_dev_cl = np.std(colours_len_list)
    #
    # print("- Conflicts -")
    # print("min value:", min_con, "\nmax value:", max_con,  "\nmean value:", mean_con, "\nst dev:", std_dev_con)
    # print("\n- Colours Range -")
    # print("min value:", min_cl, "\nmax value:", max_cl, "\nmean value:", mean_cl, "\nst dev:", std_dev_cl)


if __name__ == "__main__":
    main()
