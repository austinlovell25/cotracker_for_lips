import csv
import json
import sys
import pandas as pd
import numpy as np
import config

if __name__ == "__main__":
    fname1 = sys.argv[1]
    fname2 = sys.argv[2]
    df1 = pd.read_csv(fname1, header=0)
    df2 = pd.read_csv(fname2, header=0)

    crop_left = 300
    crop_up = 270

    # Points for cropping
    if sys.argv[3] == "reduce":
        f1_x1_mean_offset = df1["x1"].mean() - crop_left
        f1_y1_mean_offset = df1["y1"].mean() - crop_up
        f2_x1_mean_offset = df2["x1"].mean() - crop_left
        f2_y1_mean_offset = df2["y1"].mean() - crop_up

        f1_mean_incrop_array = np.zeros(shape=(10, 2), dtype=np.float32)
        f2_mean_incrop_array = np.zeros(shape=(10, 2), dtype=np.float32)
        for i in range(0, 10):
            iplus = i + 1
            f1_mean_incrop_array[i][0] = df1[f"x{iplus}"].mean() - f1_x1_mean_offset
            f1_mean_incrop_array[i][1] = df1[f"y{iplus}"].mean() - f1_y1_mean_offset

            f2_mean_incrop_array[i][0] = df2[f"x{iplus}"].mean() - f2_x1_mean_offset
            f2_mean_incrop_array[i][1] = df2[f"y{iplus}"].mean() - f2_y1_mean_offset

        pt_array = [f1_x1_mean_offset, f1_y1_mean_offset,
                    f2_x1_mean_offset, f2_y1_mean_offset]
        # Print used for piping output to bash
        print(pt_array)
        np.savetxt("tmp/rerun_pt_array.csv", pt_array, delimiter=",", fmt="%.5f")

        # This is not how you are supposed to use a dataframe
        out_rows = []
        for i in range(0, 10):
            iplus = i + 1
            out_rows.append([f"x{iplus}_mean_incrop", f1_mean_incrop_array[i][0], f2_mean_incrop_array[i][0]])
            out_rows.append([f"y{iplus}_mean_incrop", f1_mean_incrop_array[i][1], f2_mean_incrop_array[i][1]])
        out_rows = list(zip(*out_rows))
        out_df = pd.DataFrame(out_rows[1:], columns=out_rows[0])
        out_df.to_csv("tmp/first_5_avg.csv")

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
        f1_x1_mean_offset = df1["x1"].mean() - crop_left
        f1_y1_mean_offset = df1["y1"].mean() - crop_up
        f2_x1_mean_offset = df2["x1"].mean() - crop_left
        f2_y1_mean_offset = df2["y1"].mean() - crop_up

        f1_lower_pts = np.genfromtxt(f"{config.upper_lower_tmp_csv_dir}/vid0/lower_pts.csv", delimiter=",")
        f1_upper_pts = np.genfromtxt(f"{config.upper_lower_tmp_csv_dir}/vid0/upper_pts.csv", delimiter=",")
        f2_lower_pts = np.genfromtxt(f"{config.upper_lower_tmp_csv_dir}/vid1/lower_pts.csv", delimiter=",")
        f2_upper_pts = np.genfromtxt(f"{config.upper_lower_tmp_csv_dir}/vid1/upper_pts.csv", delimiter=",")

        end_frame = np.shape(f1_upper_pts)[1]

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
            out_df.to_csv("tmp/cotracker_pts.csv")

    elif sys.argv[3] == "from_cotracker":
        l_pts = pd.read_csv(f"{config.project_directory}/tmp/cotracker_end0.csv")
        r_pts = pd.read_csv(f"{config.project_directory}/tmp/cotracker_end1.csv")


        out_df = pd.DataFrame(
            {'x1_mean_incrop': [l_pts["x1"][0], r_pts["x1"][0]],
             'y1_mean_incrop': [l_pts["y1"][0], r_pts["y1"][0]],
             'x2_mean_incrop': [l_pts["x2"][0], r_pts["x2"][0]],
             'y2_mean_incrop': [l_pts["y2"][0], r_pts["y2"][0]]}
        )
        out_df.to_csv("tmp/first_5_avg.csv")

    if sys.argv[3] == "rerun":
        pt_array = np.loadtxt("tmp/rerun_pt_array.csv", delimiter=",")
        f1_x1_mean_offset = pt_array[0]
        f1_y1_mean_offset = pt_array[1]
        f2_x1_mean_offset = pt_array[2]
        f2_y1_mean_offset = pt_array[3]

        f1_mean_incrop_array = np.zeros(shape=(10, 2), dtype=np.float32)
        f2_mean_incrop_array = np.zeros(shape=(10, 2), dtype=np.float32)

        with open("tmp/rerun_pts.json", "r") as f:
            rerun_dict = json.load(f)
        f1_mean_incrop_array[8][0] = rerun_dict["lower_left"][0]
        f1_mean_incrop_array[8][1] = rerun_dict["lower_left"][1]

        f1_mean_incrop_array[9][0] = rerun_dict["upper_left"][0]
        f1_mean_incrop_array[9][1] = rerun_dict["upper_left"][1]

        f2_mean_incrop_array[8][0] = rerun_dict["lower_right"][0]
        f2_mean_incrop_array[8][1] = rerun_dict["lower_right"][1]

        f2_mean_incrop_array[9][0] = rerun_dict["upper_right"][0]
        f2_mean_incrop_array[9][1] = rerun_dict["upper_right"][1]

        for i in range(0, 8):
            iplus = i + 1
            f1_mean_incrop_array[i][0] = df1[f"x{iplus}"].mean() - f1_x1_mean_offset
            f1_mean_incrop_array[i][1] = df1[f"y{iplus}"].mean() - f1_y1_mean_offset

            f2_mean_incrop_array[i][0] = df2[f"x{iplus}"].mean() - f2_x1_mean_offset
            f2_mean_incrop_array[i][1] = df2[f"y{iplus}"].mean() - f2_y1_mean_offset

        pt_array = [f1_x1_mean_offset, f1_y1_mean_offset,
                    f2_x1_mean_offset, f2_y1_mean_offset]
        # Print used for piping output to bash
        print(pt_array)

        # This is not how you are supposed to use a dataframe
        out_rows = []
        for i in range(0, 10):
            iplus = i + 1
            out_rows.append([f"x{iplus}_mean_incrop", f1_mean_incrop_array[i][0], f2_mean_incrop_array[i][0]])
            out_rows.append([f"y{iplus}_mean_incrop", f1_mean_incrop_array[i][1], f2_mean_incrop_array[i][1]])
        out_rows = list(zip(*out_rows))
        out_df = pd.DataFrame(out_rows[1:], columns=out_rows[0])
        out_df.to_csv("tmp/first_5_avg.csv")

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


    elif sys.argv[3] == "rerun_revert":
        pt_array = np.loadtxt("tmp/rerun_pt_array.csv", delimiter=",")
        f1_x1_mean_offset = pt_array[0]
        f1_y1_mean_offset = pt_array[1]
        f2_x1_mean_offset = pt_array[2]
        f2_y1_mean_offset = pt_array[3]

        f1_lower_pts = np.genfromtxt("tmp/vid0/lower_pts.csv", delimiter=",")
        f1_upper_pts = np.genfromtxt("tmp/vid0/upper_pts.csv", delimiter=",")
        f2_lower_pts = np.genfromtxt("tmp/vid1/lower_pts.csv", delimiter=",")
        f2_upper_pts = np.genfromtxt("tmp/vid1/upper_pts.csv", delimiter=",")

        end_frame = np.shape(f1_upper_pts)[1]

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
        out_df.to_csv("tmp/cotracker_pts.csv")

