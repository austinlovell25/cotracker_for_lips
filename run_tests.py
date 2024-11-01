import argparse
import csv
import subprocess
import sys
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--is_multiple", default="False")
parser.add_argument("-f", "--csv_file", default="None")
parser.add_argument("-v1", "--vid1", help="Video 1")
parser.add_argument("-v2", "--vid2", help="Video 2")
parser.add_argument("-t", "--title", help="Experiment Name")
parser.add_argument("-d", "--save_dir", help="Directory to save output to")
parser.add_argument("-c", "--cam_config_dir", help="Directory with camera config files", default=None)

args = parser.parse_args()

is_mult = args.is_multiple
csv_file = args.csv_file
vid1 = args.vid1
vid2 = args.vid2
title = args.title
save_dir = args.save_dir
cam_config_dir = args.cam_config_dir

configs = {
    # "Gl": "global.json",
    "GlLp": "global_lip.json",
    # "GlSp": "global_spiga.json",
    # "Sp": "spiga.json",
    # "No": "none.json",
    # "Lp": "lip_contour.json"
}

if is_mult == "False":
    Path(f"{save_dir}").mkdir(parents=True, exist_ok=True)
    for key, value in configs.items():
        str = f"bash spiga_pipeline.sh {vid1} {vid2} {title}_{key} {value} {save_dir} {cam_config_dir}"
        print(str)
        subprocess.run(str, shell=True)

elif is_mult == "True" or is_mult == "T" or is_mult == "true" or is_mult == "t":
    file_path = csv_file
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        # Loop over the rows in the CSV file
        for row in csv_reader:
            if len(row) < 5:
                print(f"Skipping invalid row: {row}")
                continue
            # Assuming the CSV columns are ordered: vid1, vid2, title, save_dir
            vid1 = row[0]
            vid2 = row[1]
            title = row[2]
            save_dir = row[3]
            cam_config_dir = row[4]
            if not os.path.isdir(cam_config_dir):
                print(f"ERROR: CONFIG PATH {cam_config_dir} DOES NOT EXIST")
                exit(1)

            Path(f"{save_dir}").mkdir(parents=True, exist_ok=True)
            for key, value in configs.items():
                str = f"bash spiga_pipeline.sh {vid1} {vid2} {title}_{key} {value} {save_dir} {cam_config_dir}"
                print(str)
                subprocess.run(str, shell=True)

else:
    print("Invalid --is_multiple option\nExiting...")
