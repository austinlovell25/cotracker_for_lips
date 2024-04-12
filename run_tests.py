import subprocess
import sys

vid1 = "/home/kwangkim/Projects/kids/L2045/Left_Camera/left308-314.mp4"
vid2 = "/home/kwangkim/Projects/kids/L2045/Right_Camera/sright308-314.mp4"
title = "head3_startlater"

configs = {
    "Sp": "spiga.json",
    "Gl": "global.json",
    "GlLp": "global_lip.json",
    "GlLc": "global_and_local.json"
}

for key, value in configs.items():
    str = f"bash spiga_pipeline.sh {vid1} {vid2} {title}_{key} {value}"
    print(str)
    subprocess.run(str, shell=True)
