import sys
import pandas as pd

fname1 = sys.argv[1]
fname2 = sys.argv[2]
df1 = pd.read_csv(fname1, header=0)
df2 = pd.read_csv(fname2, header=0)

crop_left = 400
crop_up = 550

f1_x1_mean = df1["x1"].mean() - crop_left
f1_y1_mean = df1["y1"].mean() - crop_up
f1_x2_mean = df1["x2"].mean() - crop_left
f1_y2_mean = df1["y2"].mean() - crop_up

f2_x1_mean = df2["x1"].mean() - crop_left
f2_y1_mean = df2["y1"].mean() - crop_up
f2_x2_mean = df2["x2"].mean() - crop_left
f2_y2_mean = df2["y2"].mean() - crop_up

pt_array = [f1_x1_mean, f1_y1_mean,
            f2_x1_mean, f2_y1_mean]
print(pt_array)

out_df = pd.DataFrame(
    {'x1_mean': [f1_x1_mean, f2_x1_mean],
     'y1_mean': [f1_y1_mean, f2_y1_mean],
     'x2_mean': [f1_x2_mean, f2_x2_mean],
     'y2_mean': [f1_y2_mean, f2_y2_mean]}
)

# print(out_df)
out_df.to_csv("first_5_avg.csv")
