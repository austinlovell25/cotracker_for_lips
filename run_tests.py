import argparse
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("-v1", "--vid1", help="Video 1")
parser.add_argument("-v2", "--vid2", help="Video 2")
parser.add_argument("-t", "--title", help="Experiment Name")
parser.add_argument("-d", "--save_dir", help="Directory to save output to")
args = parser.parse_args()

vid1 = args.vid1
vid2 = args.vid2
title = args.title
save_dir = args.save_dir

Path(f"{save_dir}").mkdir(parents=True, exist_ok=True)

configs = {
    "Gl": "global.json",
    "GlLp": "global_lip.json",
    "GlSp": "global_spiga.json",
    "Sp": "spiga.json",
    "Lp": "lip_contour.json"
}

for key, value in configs.items():
    str = f"bash spiga_pipeline.sh {vid1} {vid2} {title}_{key} {value} {save_dir}"
    print(str)
    subprocess.run(str, shell=True)
