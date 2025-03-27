import cv2
import argparse
import random
import os
import subprocess
import string
import shutil


def move_old_frames(calib_dir):
    random_dir = ''.join(random.choices(string.ascii_uppercase, k=10))
    print("-----------------------------------------------------------------------------")
    print("-----------------------------------------------------------------------------")
    print(f"Removing previous D2, J2, and synced folders")
    print("-----------------------------------------------------------------------------")
    print("-----------------------------------------------------------------------------")

    # os.mkdir(f"{calib_dir}/configs/scraps/{random_dir}")
    shutil.rmtree(f"{calib_dir}/D2")
    shutil.rmtree(f"{calib_dir}/J2")
    shutil.rmtree(f"{calib_dir}/synced")
    # str = f"mv {calib_dir}/D2 {calib_dir}/configs/scraps/{random_dir}"
    # subprocess.run(str, shell=True)
    # str = f"mv {calib_dir}/J2 {calib_dir}/configs/scraps/{random_dir}"
    # subprocess.run(str, shell=True)
    # str = f"mv {calib_dir}/synced {calib_dir}/configs/scraps/{random_dir}"
    # subprocess.run(str, shell=True)

def get_frames(cap, folder, l_or_r):
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

    str = f"cp {folder}/{l_or_r}_grid_frames/* {folder}/{letter}2"
    subprocess.run(str, shell=True)
    str = f"cp {folder}/{l_or_r}_grid_frames/* {folder}/synced"
    subprocess.run(str, shell=True)

if __name__ == "__main__":
    print("hello")
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--left_video", help="First frame grid fully appears on")
    parser.add_argument("-r", "--right_video", help="Last frame grid fully appears on")
    parser.add_argument("-s", "--start_frame", type=int, help="First frame grid fully appears on")
    parser.add_argument("-e", "--end_frame", type=int, help="Last frame grid fully appears on")
    args = parser.parse_args()
    if not os.path.exists(args.left_video):
        print(f"File {args.left_video} could not be found.")
        exit(1)
    if not os.path.exists(args.right_video):
        print(f"File {args.right_video} could not be found.")
        exit(1)

    frames = [random.randint(args.start_frame, args.end_frame) for a in range(50)]
    print(frames)
    print("Running...")

    parent_folder = os.path.dirname(args.right_video)
    os.makedirs(f"{parent_folder}/synced", exist_ok=True)
    os.makedirs(f"{parent_folder}/D2", exist_ok=True)
    os.makedirs(f"{parent_folder}/J2", exist_ok=True)


    cap = cv2.VideoCapture(args.left_video)
    os.makedirs(f"{parent_folder}/left_grid_frames", exist_ok=True)
    get_frames(cap, parent_folder, "left")



    cap = cv2.VideoCapture(args.right_video)
    os.makedirs(f"{parent_folder}/right_grid_frames", exist_ok=True)
    get_frames(cap, parent_folder, "right")

    print("Finished running grid_frames.py")
