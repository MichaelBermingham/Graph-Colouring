import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("async_perturbation_50.csv")

# Group the data by "Experiment Run"
grouped = df.groupby("Experiment Run")

plt.figure(figsize=(15, 10))

for name, group in grouped:
    plt.plot(group.index, group["Number of Conflicts"], marker="o", linestyle="-", label=f"Run {name}")

plt.title("Agent-based System using perturbation of 50%")
plt.xlabel("Individual Iterations 50 Experiments")
plt.ylabel("Number of Conflicts")
# plt.legend()
plt.grid(True)

# Display the plot
plt.show()
