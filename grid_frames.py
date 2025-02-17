import cv2
import argparse
import random
import os
import subprocess
import string
import shutil


def move_old_frames(calib_dir):s
    random_dir = ''.join(random.choices(string.ascii_uppercase, k=10))
    print("-----------------------------------------------------------------------------")
    print("-----------------------------------------------------------------------------")
    print(f"Removing previous D2, J2, and synched folders")
    print("-----------------------------------------------------------------------------")
    print("-----------------------------------------------------------------------------")

    os.mkdir(f"{calib_dir}/configs/scraps/{random_dir}")
    shutil.rmtree(f"{calib_dir}/D2")
    shutil.rmtree(f"{calib_dir}/J2")
    shutil.rmtree(f"{calib_dir}/synched")
    # str = f"mv {calib_dir}/D2 {calib_dir}/configs/scraps/{random_dir}"
    # subprocess.run(str, shell=True)
    # str = f"mv {calib_dir}/J2 {calib_dir}/configs/scraps/{random_dir}"
    # subprocess.run(str, shell=True)
    # str = f"mv {calib_dir}/synched {calib_dir}/configs/scraps/{random_dir}"
    # subprocess.run(str, shell=True)

def get_frames(cap, folder, path, l_or_r, calib_dir):
    if l_or_r == "left":
        cam_num = 1
        letter = "D"
    else:
        cam_num = 2
        letter = "J"
    count = 1
    index = 0
    success, image = cap.read()
    print(f"Getting {l_or_r} frames...")
    while success and index <= max(frames):
        if index in frames:
            # print(index)
            cv2.imwrite(f"{folder}/{l_or_r}_grid_frames/camera-{cam_num}-{count:02}.png", image, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            count += 1
        success, image = cap.read()
        index += 1

    str = f"cp {folder}/{l_or_r}_grid_frames/* {parent_folder}/{letter}2"
    subprocess.run(str, shell=True)
    str = f"cp -r {parent_folder}/{letter}2 {calib_dir}"
    subprocess.run(str, shell=True)
    str = f"cp {folder}/{l_or_r}_grid_frames/* {parent_folder}/synched"
    subprocess.run(str, shell=True)


parser = argparse.ArgumentParser()
parser.add_argument("-l", "--left_video", help="First frame grid fully appears on")
parser.add_argument("-r", "--right_video", help="Last frame grid fully appears on")
parser.add_argument("-s", "--start_frame", type=int, help="First frame grid fully appears on")
parser.add_argument("-e", "--end_frame", type=int, help="Last frame grid fully appears on")
args = parser.parse_args()

frames = [random.randint(args.start_frame, args.end_frame) for a in range(50)]
print(frames)
print("Running...")

parent_folder = os.path.dirname(args.right_video)
calib_dir = "/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration"
move_old_frames(calib_dir)

try:
    os.mkdir(f"{parent_folder}/synched")
    os.mkdir(f"{parent_folder}/D2")
    os.mkdir(f"{parent_folder}/J2")
    os.mkdir(f"{calib_dir}/synched")
    os.mkdir(f"{calib_dir}/D2")
    os.mkdir(f"{calib_dir}/J2")

except:
    print(f"Error: some folder already exists")
    print("It is likely that this program was already ran and finished for these videos")
    print("If you want to rerun this script, delete the D2, J2, and synched folder and retry")

cap = cv2.VideoCapture(args.left_video)
folder = os.path.dirname(args.left_video)
path = os.mkdir(f"{folder}/left_grid_frames")
get_frames(cap, folder, path, "left", calib_dir)

cap = cv2.VideoCapture(args.right_video)
folder = os.path.dirname(args.right_video)
path = os.mkdir(f"{folder}/right_grid_frames")
get_frames(cap, folder, path, "right", calib_dir)

str = f"cp -r {parent_folder}/synched {calib_dir}/"
subprocess.run(str, shell=True)

print("Finished")
