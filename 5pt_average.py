import sys
import pandas as pd

fname1 = sys.argv[1]
fname2 = sys.argv[2]
df1 = pd.read_csv(fname1, header=0)
df2 = pd.read_csv(fname2, header=0)

crop_left = 300
crop_up = 270

f1_x1_mean_offset = df1["x1"].mean() - crop_left
f1_y1_mean_offset = df1["y1"].mean() - crop_up
f2_x1_mean_offset = df2["x1"].mean() - crop_left
f2_y1_mean_offset = df2["y1"].mean() - crop_up


f1_x1_mean_incrop = df1["x2"].mean() - f1_x1_mean_offset
f1_y1_mean_incrop = df1["y2"].mean() - f1_y1_mean_offset
f1_x2_mean_incrop = df2["x2"].mean() - f1_y1_mean_offset
f1_y2_mean_incrop = df2["y2"].mean() - f1_x1_mean_offset

f2_x1_mean_incrop = df1["x2"].mean() - f2_x1_mean_offset
f2_y1_mean_incrop = df1["y2"].mean() - f2_y1_mean_offset
f2_x2_mean_incrop = df2["x2"].mean() - f2_y1_mean_offset
f2_y2_mean_incrop = df2["y2"].mean() - f2_x1_mean_offset

pt_array = [f1_x1_mean_offset, f1_y1_mean_offset,
            f2_x1_mean_offset, f2_y1_mean_offset]
print(pt_array)

out_df = pd.DataFrame(
    {'x1_mean_incrop': [f1_x1_mean_incrop, f2_x1_mean_incrop],
     'y1_mean_incrop': [f1_y1_mean_incrop, f2_y1_mean_incrop],
     'x2_mean_incrop': [f1_x2_mean_incrop, f2_x2_mean_incrop],
     'y2_mean_incrop': [f1_y2_mean_incrop, f2_y2_mean_incrop]}
)

# print(out_df)
out_df.to_csv("first_5_avg.csv")
