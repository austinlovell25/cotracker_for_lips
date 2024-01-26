import numpy as np
import matplotlib.pyplot as plt

trial = "D"
file_name = f"many_vs_one/{trial}/compare.png"

onept = np.genfromtxt(f"videos/many_vs_one/{trial}/oneUpperY.csv", delimiter=",")
manypt = np.genfromtxt(f"videos/many_vs_one/{trial}/manyUpperY.csv", delimiter=",")

x = np.arange(0, np.size(manypt), 1)
fig, ax = plt.subplots()
ax.plot(x[0:100], onept[0:100], linewidth=2.0, c='r', label="one pt")
ax.plot(x[0:100], manypt[0:100], linewidth=2.0, c='b', label="many pts")
ax.set_xlabel('frames')
ax.set_ylabel('y values')
# ax.set_title('y values of point on upper lip')
plt.legend(loc='lower right')
plt.savefig(f"/home/kwangkim/Projects/cotracker/videos/{file_name}")
print(f"{file_name}")