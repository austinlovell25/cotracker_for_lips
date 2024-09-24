import subprocess
import sys

vid1 = "/home/kwangkim/Desktop/2-09_3s/left_synced_final.mp4"
vid2 = "/home/kwangkim/Desktop/2-09_3s/right_synced_final.mp4"
title = "2-09_3s"
save_dir = "/home/kwangkim/Desktop/2-09_3s"

configs = {
    "Gl": "global.json",
    "GlLp": "global_lip.json",
    "GlSp": "global_spiga.json",
    "Sp": "spiga.json",
    "GlDn": "global_and_dense_local.json",
    "DnLc": "dense_local.json",
    "Lp": "lip_contour.json"
}

for key, value in configs.items():
    str = f"bash spiga_pipeline.sh {vid1} {vid2} {title}_{key} {value} {save_dir}"
    print(str)
    subprocess.run(str, shell=True)
