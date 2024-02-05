import numpy as np
import matplotlib.pyplot as plt

trial = "F"
file_name = f"many_vs_one/{trial}/compare100.png"

onept = np.genfromtxt(f"videos/many_vs_one/{trial}/oneUpper.csv", delimiter=",")
manypt = np.genfromtxt(f"videos/many_vs_one/{trial}/manyUpper.csv", delimiter=",")

x = np.arange(np.size(manypt[0]))
fig, ax = plt.subplots()
ax.plot(x[0:100], onept[1][0:100], linewidth=2.0, c='r', label="one pt")
ax.plot(x[0:100], manypt[1][0:100], linewidth=2.0, c='b', label="many pts")
ax.set_xlabel('frames')
ax.set_ylabel('y values')
# ax.set_title('y values of point on upper lip')
plt.legend(loc='lower right')
plt.savefig(f"/home/kwangkim/Projects/cotracker_new/videos/{file_name}")
print(f"{file_name}")