import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file into a pandas DataFrame
df = pd.read_csv("negotiate_agent_remove_100.csv")

# Getting unique runs for color mapping
runs = df["Experiment Run"].unique()
colormap = plt.cm.get_cmap("viridis", len(runs) + 1)

plt.figure(figsize=(10, 6))

for run in runs:
    # Filter the DataFrame for each experiment run
    run_data = df[df["Experiment Run"] == run]

    # Plotting
    plt.plot(run_data["Number of Conflicts"], run_data["Number of Colours"], marker="o", markersize=3, linestyle="-", linewidth="0.5",
             color=colormap(run))

#plt.xlim(max(df["Number of Conflicts"]), 0)  # Used to flip axis for better readability
plt.title("Agents Negotiate, 30 Experiments. Iteratively Removing Colours.")
plt.xlabel("Number of Conflicts")
plt.ylabel("Number of Colours")
plt.legend()
plt.grid(True)


# Dynamically adjust ticks based on data range
conflict_ticks = np.linspace(df["Number of Conflicts"].min(), df["Number of Conflicts"].max(), num=10, dtype=int)
color_ticks = np.arange(df["Number of Colours"].min(), df["Number of Colours"].max() + 1)

plt.xticks(conflict_ticks)
plt.yticks(color_ticks)
plt.show()
