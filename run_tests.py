import argparse
import csv
import subprocess
import sys
import os
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--is_multiple", default="Final")
parser.add_argument("-f", "--file", default="None")
parser.add_argument("-v1", "--vid1", help="Video 1")
parser.add_argument("-v2", "--vid2", help="Video 2")
parser.add_argument("-t", "--title", help="Experiment Name")
parser.add_argument("-d", "--save_dir", help="Directory to save output to")
parser.add_argument("-c", "--cam_config_dir", help="Directory with camera config files", default=None)

args = parser.parse_args()

is_mult = args.is_multiple
file_path = args.file
vid1 = args.vid1
vid2 = args.vid2
title = args.title
save_dir = args.save_dir
cam_config_dir = args.cam_config_dir

configs = {
    # "Gl": "global.json",
    "GlLp": "global_lip.json",
    #"GlSp": "global_spiga.json",
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

elif is_mult == "Final":
    with open(file_path, 'r') as file:
        data = json.load(file)
        exp_name = data["experiment_name"]
        video_dir = data["source_directory"]
        times = data["times"]
        for time in times:
            vid1 = f"{video_dir}/samples/left_{time}.mp4"
            vid2 = f"{video_dir}/samples/right_{time}.mp4"

            for key, value in configs.items():
                str = f"bash spiga_pipeline.sh {vid1} {vid2} {exp_name}_{time}_{key} {value} {video_dir} {video_dir} false"
                print(str)
                subprocess.run(str, shell=True)


elif is_mult == "True" or is_mult == "T" or is_mult == "true" or is_mult == "t":
    exp_name = None
    video_dir = None
    save_dir = None
    video_name_type = None
    video_start_name = None
    cam_config_dir = None

    if os.path.splitext(file_path)[1] == ".json":
        with open(file_path, 'r') as file:
            data = json.load(file)
            exp_name = data["experiment_name"]
            video_dir = data["source_data_directory"]
            save_dir = data["save_directory"]
            cam_config_dir = data["cam_config_directory"]
            video_name_type = data["trimmed_or_overlay"]
            is_snap = data["is_use_snap"]
            times = data["times"]
            for time in times:
                vid1 = f"{video_dir}{time}/{exp_name}_left_sync_{time}_{video_name_type}.mp4"
                vid2 = f"{video_dir}{time}/{exp_name}_right_sync_{time}_{video_name_type}.mp4"

                for key, value in configs.items():
                    str = f"bash spiga_pipeline.sh {vid1} {vid2} {exp_name}_{time}_{key} {value} {save_dir} {cam_config_dir} {is_snap}"
                    print(str)
                    subprocess.run(str, shell=True)

    else:
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            # Loop over the rows in the CSV file
            for idx, row in enumerate(csv_reader):
                print(idx)
                if idx == 0:
                    video_start_name = row[0]
                elif idx == 1:
                    video_dir = row[0]
                    if video_dir[-1] != '/':
                        print("Video directory name must end in /. \nEnding program...")
                        exit(1)
                elif idx == 2:
                    save_dir = row[0]
                    Path(f"{save_dir}").mkdir(parents=True, exist_ok=True)
                elif idx == 3:
                    cam_config_dir = row[0]
                    if not os.path.isdir(cam_config_dir):
                        print(f"ERROR: CONFIG PATH {cam_config_dir} DOES NOT EXIST")
                        exit(1)
                elif idx == 4:
                    video_name_type = row[0]
                    if video_name_type != 'overlay' and video_name_type != 'trimmed':
                        print("Invalid video name type. \nEnding program...")
                        exit(1)
                elif idx == 5:
                    is_snap = row[1]
                    if is_snap != 'True' and is_snap != 'False':
                        print("Invalid snapping (edge_correction) option. \nUse True or False \nEnding program...")
                        exit(1)
                else:
                    # Assuming the CSV columns are ordered: vid1, vid2, title, save_dir
                    time = row[0]

                    vid1 = f"{video_dir}{time}/{video_start_name}_left_sync_{time}_{video_name_type}.mp4"
                    vid2 = f"{video_dir}{time}/{video_start_name}_right_sync_{time}_{video_name_type}.mp4"

                    for key, value in configs.items():
                        str = f"bash spiga_pipeline.sh {vid1} {vid2} {video_start_name}_{time}_{key} {value} {save_dir} {cam_config_dir} {is_snap}"
                        print(str)
                        subprocess.run(str, shell=True)

else:
    print("Invalid --is_multiple option\nExiting...")
