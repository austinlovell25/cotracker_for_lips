import csv
import sys
import pandas as pd
import numpy as np
import config
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

# Points for cropping
if sys.argv[3] == "reduce":
    f1_x1_mean_incrop = df1["x1"].mean() - f1_x1_mean_offset
    f1_y1_mean_incrop = df1["y1"].mean() - f1_y1_mean_offset
    f1_x2_mean_incrop = df1["x2"].mean() - f1_x1_mean_offset
    f1_y2_mean_incrop = df1["y2"].mean() - f1_y1_mean_offset
    f1_x3_mean_incrop = df1["x3"].mean() - f1_x1_mean_offset
    f1_y3_mean_incrop = df1["y3"].mean() - f1_y1_mean_offset
    f1_x4_mean_incrop = df1["x4"].mean() - f1_x1_mean_offset
    f1_y4_mean_incrop = df1["y4"].mean() - f1_y1_mean_offset
    f1_x5_mean_incrop = df1["x5"].mean() - f1_x1_mean_offset
    f1_y5_mean_incrop = df1["y5"].mean() - f1_y1_mean_offset
    f1_x6_mean_incrop = df1["x6"].mean() - f1_x1_mean_offset
    f1_y6_mean_incrop = df1["y6"].mean() - f1_y1_mean_offset
    f1_x7_mean_incrop = df1["x7"].mean() - f1_x1_mean_offset
    f1_y7_mean_incrop = df1["y7"].mean() - f1_y1_mean_offset
    f1_x8_mean_incrop = df1["x8"].mean() - f1_x1_mean_offset
    f1_y8_mean_incrop = df1["y8"].mean() - f1_y1_mean_offset
    f1_x9_mean_incrop = df1["x9"].mean() - f1_x1_mean_offset
    f1_y9_mean_incrop = df1["y9"].mean() - f1_y1_mean_offset
    f1_x10_mean_incrop = df1["x10"].mean() - f1_x1_mean_offset
    f1_y10_mean_incrop = df1["y10"].mean() - f1_y1_mean_offset

    f2_x1_mean_incrop = df2["x1"].mean() - f2_x1_mean_offset
    f2_y1_mean_incrop = df2["y1"].mean() - f2_y1_mean_offset
    f2_x2_mean_incrop = df2["x2"].mean() - f2_x1_mean_offset
    f2_y2_mean_incrop = df2["y2"].mean() - f2_y1_mean_offset
    f2_x3_mean_incrop = df2["x3"].mean() - f2_x1_mean_offset
    f2_y3_mean_incrop = df2["y3"].mean() - f2_y1_mean_offset
    f2_x4_mean_incrop = df2["x4"].mean() - f2_x1_mean_offset
    f2_y4_mean_incrop = df2["y4"].mean() - f2_y1_mean_offset
    f2_x5_mean_incrop = df2["x5"].mean() - f2_x1_mean_offset
    f2_y5_mean_incrop = df2["y5"].mean() - f2_y1_mean_offset
    f2_x6_mean_incrop = df2["x6"].mean() - f2_x1_mean_offset
    f2_y6_mean_incrop = df2["y6"].mean() - f2_y1_mean_offset
    f2_x7_mean_incrop = df2["x7"].mean() - f2_x1_mean_offset
    f2_y7_mean_incrop = df2["y7"].mean() - f2_y1_mean_offset
    f2_x8_mean_incrop = df2["x8"].mean() - f2_x1_mean_offset
    f2_y8_mean_incrop = df2["y8"].mean() - f2_y1_mean_offset
    f2_x9_mean_incrop = df2["x9"].mean() - f2_x1_mean_offset
    f2_y9_mean_incrop = df2["y9"].mean() - f2_y1_mean_offset
    f2_x10_mean_incrop = df2["x10"].mean() - f2_x1_mean_offset
    f2_y10_mean_incrop = df2["y10"].mean() - f2_y1_mean_offset

    pt_array = [f1_x1_mean_offset, f1_y1_mean_offset,
                f2_x1_mean_offset, f2_y1_mean_offset]
    print(pt_array)

    out_df = pd.DataFrame(
        {'x1_mean_incrop': [f1_x1_mean_incrop, f2_x1_mean_incrop],
         'y1_mean_incrop': [f1_y1_mean_incrop, f2_y1_mean_incrop],
         'x2_mean_incrop': [f1_x2_mean_incrop, f2_x2_mean_incrop],
         'y2_mean_incrop': [f1_y2_mean_incrop, f2_y2_mean_incrop],
         'x3_mean_incrop': [f1_x3_mean_incrop, f2_x3_mean_incrop],
         'y3_mean_incrop': [f1_y3_mean_incrop, f2_y3_mean_incrop],
         'x4_mean_incrop': [f1_x4_mean_incrop, f2_x4_mean_incrop],
         'y4_mean_incrop': [f1_y4_mean_incrop, f2_y4_mean_incrop],
         'x5_mean_incrop': [f1_x5_mean_incrop, f2_x5_mean_incrop],
         'y5_mean_incrop': [f1_y5_mean_incrop, f2_y5_mean_incrop],
         'x6_mean_incrop': [f1_x6_mean_incrop, f2_x6_mean_incrop],
         'y6_mean_incrop': [f1_y6_mean_incrop, f2_y6_mean_incrop],
         'x7_mean_incrop': [f1_x7_mean_incrop, f2_x7_mean_incrop],
         'y7_mean_incrop': [f1_y7_mean_incrop, f2_y7_mean_incrop],
         'x8_mean_incrop': [f1_x8_mean_incrop, f2_x8_mean_incrop],
         'y8_mean_incrop': [f1_y8_mean_incrop, f2_y8_mean_incrop],
         'x9_mean_incrop': [f1_x9_mean_incrop, f2_x9_mean_incrop],
         'y9_mean_incrop': [f1_y9_mean_incrop, f2_y9_mean_incrop],
         'x10_mean_incrop': [f1_x10_mean_incrop, f2_x10_mean_incrop],
         'y10_mean_incrop': [f1_y10_mean_incrop, f2_y10_mean_incrop]
         }
    )

    # print(out_df)
    out_df.to_csv("first_5_avg.csv")

    new_support_spiga = []
    fname = "tmp/spiga_support_L.csv"
    with open(fname) as f:
        reader_obj = csv.reader(f)
        for row in reader_obj:
            new_support_spiga.append([0., float(row[1]) - f1_x1_mean_offset, float(row[2]) - f1_y1_mean_offset])
    np.savetxt("tmp/spiga_support_L.csv", np.asarray(new_support_spiga), delimiter=",")

    new_support_spiga = []
    fname = "tmp/spiga_support_R.csv"
    with open(fname) as f:
        reader_obj = csv.reader(f)
        for row in reader_obj:
            new_support_spiga.append([0., float(row[1]) - f2_x1_mean_offset, float(row[2]) - f2_y1_mean_offset])
    np.savetxt("tmp/spiga_support_R.csv", np.asarray(new_support_spiga), delimiter=",")


elif sys.argv[3] == "revert":
    f1_lower_pts = np.genfromtxt(f"{config.pipeline_dir}/vid0/lower_pts.csv", delimiter=",")
    f1_upper_pts = np.genfromtxt(f"{config.pipeline_dir}/vid0/upper_pts.csv", delimiter=",")
    f2_lower_pts = np.genfromtxt(f"{config.pipeline_dir}/vid1/lower_pts.csv", delimiter=",")
    f2_upper_pts = np.genfromtxt(f"{config.pipeline_dir}/vid1/upper_pts.csv", delimiter=",")

    end_frame = np.shape(f1_upper_pts)[1]
    # print(f"{end_frame=}")

    out_df = pd.DataFrame(
        {"f1_lower_x": f1_lower_pts[0][0:end_frame] + f1_x1_mean_offset,
         "f1_lower_y": f1_lower_pts[1][0:end_frame] + f1_y1_mean_offset,
         "f1_upper_x": f1_upper_pts[0][0:end_frame] + f1_x1_mean_offset,
         "f1_upper_y": f1_upper_pts[1][0:end_frame] + f1_y1_mean_offset,
         "f2_lower_x": f2_lower_pts[0][0:end_frame] + f2_x1_mean_offset,
         "f2_lower_y": f2_lower_pts[1][0:end_frame] + f2_y1_mean_offset,
         "f2_upper_x": f2_upper_pts[0][0:end_frame] + f2_x1_mean_offset,
         "f2_upper_y": f2_upper_pts[1][0:end_frame] + f2_y1_mean_offset,

         "f1_lower_x2": f1_lower_pts[2][0:end_frame] + f1_x1_mean_offset,
         "f1_lower_y2": f1_lower_pts[3][0:end_frame] + f1_y1_mean_offset,
         "f1_upper_x2": f1_upper_pts[2][0:end_frame] + f1_x1_mean_offset,
         "f1_upper_y2": f1_upper_pts[3][0:end_frame] + f1_y1_mean_offset,
         "f2_lower_x2": f2_lower_pts[2][0:end_frame] + f2_x1_mean_offset,
         "f2_lower_y2": f2_lower_pts[3][0:end_frame] + f2_y1_mean_offset,
         "f2_upper_x2": f2_upper_pts[2][0:end_frame] + f2_x1_mean_offset,
         "f2_upper_y2": f2_upper_pts[3][0:end_frame] + f2_y1_mean_offset,

         "f1_lower_x3": f1_lower_pts[4][0:end_frame] + f1_x1_mean_offset,
         "f1_lower_y3": f1_lower_pts[5][0:end_frame] + f1_y1_mean_offset,
         "f1_upper_x3": f1_upper_pts[4][0:end_frame] + f1_x1_mean_offset,
         "f1_upper_y3": f1_upper_pts[5][0:end_frame] + f1_y1_mean_offset,
         "f2_lower_x3": f2_lower_pts[4][0:end_frame] + f2_x1_mean_offset,
         "f2_lower_y3": f2_lower_pts[5][0:end_frame] + f2_y1_mean_offset,
         "f2_upper_x3": f2_upper_pts[4][0:end_frame] + f2_x1_mean_offset,
         "f2_upper_y3": f2_upper_pts[5][0:end_frame] + f2_y1_mean_offset,

         "f1_lower_x4": f1_lower_pts[6][0:end_frame] + f1_x1_mean_offset,
         "f1_lower_y4": f1_lower_pts[7][0:end_frame] + f1_y1_mean_offset,
         "f1_upper_x4": f1_upper_pts[6][0:end_frame] + f1_x1_mean_offset,
         "f1_upper_y4": f1_upper_pts[7][0:end_frame] + f1_y1_mean_offset,
         "f2_lower_x4": f2_lower_pts[6][0:end_frame] + f2_x1_mean_offset,
         "f2_lower_y4": f2_lower_pts[7][0:end_frame] + f2_y1_mean_offset,
         "f2_upper_x4": f2_upper_pts[6][0:end_frame] + f2_x1_mean_offset,
         "f2_upper_y4": f2_upper_pts[7][0:end_frame] + f2_y1_mean_offset,

         "f1_lower_x5": f1_lower_pts[8][0:end_frame] + f1_x1_mean_offset,
         "f1_lower_y5": f1_lower_pts[9][0:end_frame] + f1_y1_mean_offset,
         "f1_upper_x5": f1_upper_pts[8][0:end_frame] + f1_x1_mean_offset,
         "f1_upper_y5": f1_upper_pts[9][0:end_frame] + f1_y1_mean_offset,
         "f2_lower_x5": f2_lower_pts[8][0:end_frame] + f2_x1_mean_offset,
         "f2_lower_y5": f2_lower_pts[9][0:end_frame] + f2_y1_mean_offset,
         "f2_upper_x5": f2_upper_pts[8][0:end_frame] + f2_x1_mean_offset,
         "f2_upper_y5": f2_upper_pts[9][0:end_frame] + f2_y1_mean_offset
         }
    )

    if len(sys.argv) > 4:
        out_df.to_csv(f"tmp/cotracker_pts_{sys.argv[4]}.csv")
    else:
        out_df.to_csv("cotracker_pts.csv")

elif sys.argv[3] == "from_cotracker":
    l_pts = pd.read_csv(f"{config.cotracker_new_path}/tmp/cotracker_end0.csv")
    r_pts = pd.read_csv(f"{config.cotracker_new_path}/tmp/cotracker_end1.csv")


    out_df = pd.DataFrame(
        {'x1_mean_incrop': [l_pts["x1"][0], r_pts["x1"][0]],
         'y1_mean_incrop': [l_pts["y1"][0], r_pts["y1"][0]],
         'x2_mean_incrop': [l_pts["x2"][0], r_pts["x2"][0]],
         'y2_mean_incrop': [l_pts["y2"][0], r_pts["y2"][0]]}
    )
    out_df.to_csv("first_5_avg.csv")
