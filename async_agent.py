import asyncio
import copy
import csv
import random
import networkx as nx
import logging
from edge_rewiring import rewire_edges

# Creating an event for synchronisation.
sync_event = asyncio.Event()


#logging.basicConfig(level=# logging.info, format="%(asctime)s - %(levelname)s - %(message)s")


class ColourAgent:
    def __init__(self, node_id, initial_colour, colours_range, graph, colour_score):
        # logging.info(f"Initialising agent {node_id}")
        self.node_id = node_id
        self.graph = graph
        self.colours_range = colours_range
        self.colour_scores = colour_score
        self.intended_colour = None  # USed to store the intended color change
        if initial_colour not in colours_range:
            self.colour = None
        else:
            self.colour = initial_colour

    async def broadcast_intent(self):
        # Gather coroutines for broadcasting intents to all neighbors concurrently.
        negotiation_coroutines = [
            self.graph.nodes[neighbour]["agent"].negotiate_intent(self.node_id, self.intended_colour, self.graph)
            for neighbour in self.graph.neighbors(self.node_id)
        ]
        # Await all negotiation intents to complete.
        await asyncio.gather(*negotiation_coroutines)

    async def negotiate_intent(self, neighbour_id, neighbour_intended_colour, graph):
        # Negotiating if there's a conflict in intended colours.
        if neighbour_intended_colour == self.intended_colour:
            # Get degrees of both agents. Will be needed for perturbation.
            my_degree = len(list(graph.neighbors(self.node_id)))
            neighbour_degree = len(list(graph.neighbors(neighbour_id)))

            # Getting colour scores of both agents.
            my_score = self.colour_scores[self.intended_colour]
            neighbour_score = graph.nodes[neighbour_id]["agent"].colour_scores[neighbour_intended_colour]

            # Winner based on degree, then colour score, then node ID.
            if (my_degree > neighbour_degree or
                    (my_degree == neighbour_degree and my_score > neighbour_score) or
                    (my_degree == neighbour_degree and my_score == neighbour_score and self.node_id > neighbour_id)):
                # Current agent wins, neighbour changes intent.
                await graph.nodes[neighbour_id]["agent"].change_intent(graph)
            else:
                # Neighbour wins, current agent changes intent.
                await self.change_intent(graph)

    async def change_intent(self, graph):
        # Recalculate available colours excl current conflicted colour.
        neighbours_colours = await self.perceive_environment(graph)
        available_colours = set(self.colours_range) - set(neighbours_colours)  # - {self.colour}
        # Exclude current intended colour from available options.
        if self.intended_colour in available_colours:
            available_colours.remove(self.intended_colour)
        # Recalculating the best colour based on (if any) remaining available options.
        if available_colours:
            self.intended_colour = max(available_colours, key=lambda c: self.colour_scores.get(c, 0))
            # Log debugging
            logging.info(f"Agent {self.node_id} changed intent to {self.intended_colour} after negotiation")
        elif not available_colours:
            self.intended_colour = max(neighbours_colours, key=lambda c: self.colour_scores.get(c, 0))
            logging.info(f"Agent {self.node_id} using {neighbours_colours} changed intent to {self.intended_colour} after negotiation")
        else:
            # No available colours remain.
            logging.warning(f"Agent {self.node_id} found no alternative colours available after negotiation :(")

    async def decide_new_colour(self, neighbours_colours, graph):
        # logging.info(f"Agent {self.node_id} deciding on new colour.")
        # Synchronisation event.
        await sync_event.wait()
        # logging.info(f"Agent {self.node_id} allowed to decide on new colour.")
        available_colours = set(self.colours_range) - set(neighbours_colours) # - {self.colour}
        # If available, choose based on highest score.
        if available_colours:
            best_colours = sorted(available_colours, key=lambda c: self.colour_scores[c], reverse=True)
        else:
            best_colours = sorted(neighbours_colours, key=lambda c: self.colour_scores[c], reverse=True)

        self.intended_colour = best_colours[0]
        if self.intended_colour != self.colour:
            self.colour = self.intended_colour
            self.update_colour_score(self.intended_colour, graph)
            # logging.info(f"Agent {self.node_id} chose colour {self.intended_colour}")

    async def decide_and_broadcast(self):
        # logging.info(f"Agent {self.node_id} deciding and broadcasting.")
        neighbours_colours = await self.perceive_environment(self.graph)
        # logging.info(f"Agent {self.node_id} has perceived environment: {neighbours_colours}")
        # logging.info(f"Agent {self.node_id} is about to decide on a new colour.")
        await self.decide_new_colour(neighbours_colours, self.graph)
        # logging.info(f"Agent {self.node_id} decided on new colour: {self.intended_colour}")
        # logging.info(f"Agent {self.node_id} is about to broadcast intent.")
        await self.broadcast_intent()
        # logging.info(f"Agent {self.node_id} has broadcasted intent.")
        # Initiate negotiations with neighbours if there's a conflict in the intended colours.
        await self.negotiate_with_neighbours()

    async def negotiate_with_neighbours(self):
        for neighbour_id in self.graph.neighbors(self.node_id):
            neighbour_agent = self.graph.nodes[neighbour_id]["agent"]
            await self.negotiate_intent(neighbour_id, neighbour_agent.intended_colour, self.graph)

    async def perceive_environment(self, graph):
        neighbours = list(graph.neighbors(self.node_id))
        neighbours_colours = [graph.nodes[n]["agent"].colour for n in neighbours]
        return neighbours_colours

    def update_colour_score(self, chosen_colour, graph):
        # Simple reward/penalty system: increase score if no conflicts, else decrease
        for neighbour in graph.neighbors(self.node_id):
            if graph.nodes[neighbour]["agent"].colour == chosen_colour:
                self.colour_scores[chosen_colour] -= 5  # Penalty for conflict
                return
        self.colour_scores[chosen_colour] += 5  # Reward for no conflict


def read_saved_graph(path):
    """Read and return a graph from a saved GraphML file."""
    return nx.read_graphml(path)


async def simulate_colouring(graph, colours_range, colour_score, iterations=50):
    # logging.info("Starting simulation")
    for node in graph.nodes():
        initial_colour = int(graph.nodes[node]['colour'])
        graph.nodes[node]["agent"] = ColourAgent(node, initial_colour, colours_range, graph, colour_score)

    for iteration in range(iterations):
        results = []
        # logging.info(f"Starting iteration {iteration}")
        # print("Colour range before: ", len(colours_range))
        if len(colours_range) > 5:  # Number of colours to remove.
            removed_color = random.choice(colours_range)
            # print(f"Removed colour: {removed_color}, Length: {len(colours_range)}")
            colours_range.remove(removed_color)
            # print(f"Colour range after: ", len(colours_range))

            # Update colour range
            for node in graph.nodes():
                graph.nodes[node]["agent"].colours_range = colours_range

        if len(colours_range) == 6:
            rewire_edges(graph, 0.2)

        # Creating tasks for each agent to decide and broadcast.
        tasks = [agent.decide_and_broadcast() for node in graph.nodes() for agent in [graph.nodes[node]["agent"]]]

        # Clear the event - all agents are waiting.
        sync_event.clear()
        # logging.info(f"Event cleared for iteration {iteration}")

        # Set the event - all agents now proceed with decision-making.
        sync_event.set()
        # logging.info(f"Event set for iteration {iteration}")

        # All agents ready to go, using gather to run them.
        await asyncio.gather(*[asyncio.create_task(task) for task in tasks])
        # logging.info(f"Completed tasks for iteration {iteration}")

        # Short delay
        await asyncio.sleep(0.1)
        sync_event.clear()
        conflicts = count_conflicts(graph)
        print(f"Conflicts after iteration {iteration}, is now {conflicts}, colour range is {len(colours_range)}")
        results.append((iteration, len(colours_range), conflicts))
        with open("async_perturbation_20.csv", "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for r in results:
                writer.writerow(r)


def count_conflicts(graph):
    conflicts = 0
    for node in graph.nodes():
        node_colour = graph.nodes[node]["agent"].colour
        for neighbour in graph.neighbors(node):
            neighbour_colour = graph.nodes[neighbour]["agent"].colour
            if node_colour == neighbour_colour:
                conflicts += 1
    return conflicts // 2


async def main():
    # logging.info("Main start")
    # Setup and initialisation steps
    sync_event.set()
    graph_path = "baseline_graph.graphml"
    netx_graph_original = read_saved_graph(graph_path)
    # logging.info(f"Graph loaded from {graph_path}")

    for experiment_run in range(1, 2):
        # Deep copy of graph
        netx_graph = copy.deepcopy(netx_graph_original)
        colours_range = list(range(14))
        colour_score = {colour: 0 for colour in colours_range}

        # Apply agent-based coloring
        colours_range.remove(random.choice(colours_range))
        await simulate_colouring(netx_graph, colours_range, colour_score)


if __name__ == "__main__":
    asyncio.run(main())
