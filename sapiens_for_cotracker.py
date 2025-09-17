import json
import subprocess
import sys
import os
import cv2
from read_json_sapiens_cot import read_json
#from cropping_sapiens_cot_AUTO import adjusted_detect_face
#from cropping_sapiens_cot_AUTO import retinaface_cropping
import numpy as np
import shlex

#file_path = sys.argv[1]
left_vid = sys.argv[1]
right_vid = sys.argv[2]
pathcomp = left_vid.split('/')
intermediate_str = pathcomp[-2] + "/" + pathcomp[-1]
video_dir = left_vid.replace(intermediate_str, '')
exprfull = sys.argv[3]
exprcomp = exprfull.split('_')
expr = exprcomp[0]
time = exprcomp[1]

#print(expr)
#print(time)

## This is to get cropped XY coordinates and make cropped images
# #### This is for when we don't have raw images yet
raw_image_L = ['ffmpeg', '-i', left_vid, '-start_number', '0', f"{video_dir}{time}/raw_images/left_sync/image%d.png"]
os.makedirs(f"{video_dir}{time}/raw_images/left_sync", exist_ok=True)
subprocess.call(raw_image_L, shell=False)
raw_image_R = ['ffmpeg', '-i', right_vid, '-start_number', '0', f"{video_dir}{time}/raw_images/right_sync/image%d.png"]
os.makedirs(f"{video_dir}{time}/raw_images/right_sync", exist_ok=True)
subprocess.call(raw_image_R, shell=False)

coordinates = np.loadtxt("tmp/retinafacepts.csv").astype(np.int64)
left_x = coordinates[0]
left_y = coordinates[1]
right_x = coordinates[2]
right_y = coordinates[3]


auto_cropping_L = ['ffmpeg', '-i', f'{video_dir}{time}/raw_images/left_sync/image%d.png', '-vf',
                              f'crop=700:700:{left_x}:{left_y}', '-c:a', 'copy',
                              f"{video_dir}{time}/cropped_images/left_sync/image%d.png"]
os.makedirs(f"{video_dir}{time}/cropped_images/left_sync", exist_ok=True)
subprocess.call(auto_cropping_L, shell=False)


auto_cropping_R = ['ffmpeg', '-i', f'{video_dir}{time}/raw_images/right_sync/image%d.png', '-vf',
                              f'crop=700:700:{right_x}:{right_y}', '-c:a', 'copy',
                              f"{video_dir}{time}/cropped_images/right_sync/image%d.png"]
os.makedirs(f"{video_dir}{time}/cropped_images/right_sync", exist_ok=True)
subprocess.call(auto_cropping_R, shell=False)



print("==========================RUNNING SAPIENS ON VIDEO==============================")
sapiens_pipe_L = ['bash', '/home/kwangkim/sapiens/lite/scripts/demo/torchscript/pose_keypoints308_SINGLE.sh',
            f"{video_dir}{time}/cropped_images/left_sync", f"{video_dir}{time}/sapiens/cotracker/left_sync"]
subprocess.call(sapiens_pipe_L, shell=False)

sapiens_pipe_R = ['bash', '/home/kwangkim/sapiens/lite/scripts/demo/torchscript/pose_keypoints308_SINGLE.sh',
            f"{video_dir}{time}/cropped_images/right_sync", f"{video_dir}{time}/sapiens/cotracker/right_sync"]
subprocess.call(sapiens_pipe_R, shell=False)
#
read_json(f"{video_dir}{time}/sapiens/cotracker/left_sync/sapiens_1b", left_x, left_y, 1)
read_json(f"{video_dir}{time}/sapiens/cotracker/right_sync/sapiens_1b", right_x, right_y, 2)

