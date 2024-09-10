import subprocess
import sys

vid1 = "/home/kwangkim/Projects/kids/L2045/Left_Camera/left805-807.mp4"
vid2 = "/home/kwangkim/Projects/kids/L2045/Right_Camera/sright805-807.mp4"
title = "L2045_805-807"

configs = {
    "Gl": "global.json",
    "GlLp": "global_lip.json",
    "GlSp": "global_spiga.json",
}

for key, value in configs.items():
    str = f"bash spiga_pipeline.sh {vid1} {vid2} {title}_{key} {value}"
    print(str)
    subprocess.run(str, shell=True)
