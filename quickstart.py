import csv
import os
import sys

import pandas as pd
import torch
import cv2
import imageio.v3 as iio
import numpy as np
from cotracker.utils.visualizer import Visualizer, read_video_from_path
from cotracker.predictor import CoTrackerPredictor
from pathlib import Path
import argparse
import json
import subprocess

pts = []

def correct_top_spiga_pt(vid_file, pt):
    str = f'ffmpeg -y -i {vid_file} -vf "select=eq(n\,0)" -vframes 1 tmp/edge_out.png'
    print(str)
    subprocess.run(str, shell=True)

    ratio = 3
    kernel_size = 3
    low_threshold = 10

    src = cv2.imread(cv2.samples.findFile("tmp/edge_out.png"))
    if src is None:
        print('Could not open or find the image: tmp/edge_out.png')
        exit(0)
    src_gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

    img_blur = cv2.blur(src_gray, (3, 3))
    detected_edges = cv2.Canny(img_blur, low_threshold, low_threshold * ratio, kernel_size)
    mask = detected_edges != 0
    x_pt = round(pt[1])
    y_iter = round(pt[2])
    orig_y_iter = y_iter
    # Y is first
    while mask[y_iter, x_pt] == 0:
        y_iter -= 1
        # Failsafe
        if (orig_y_iter - y_iter) >= 30:
            y_iter = orig_y_iter
            break
    return x_pt, y_iter




def global_grid(x_end, y_end):
    for i in range(0, x_end, 70):
        for z in range(0, y_end, 50):
            pts.append([0., i, z])
def grid_loop(x, y, start1, stop1, step1, start2, stop2, step2):
    for i in range(start1, stop1, step1):
        for z in range(start2, stop2, step2):
            pts.append([0., x + i, y])
            pts.append([0., x - i, y])
            pts.append([0., x, y + z])
            pts.append([0., x, y - z])

            pts.append([0., x + i, y + z])
            pts.append([0., x + i, y - z])
            pts.append([0., x - i, y + z])
            pts.append([0., x - i, y - z])
def griddify(x, y):
    if data["dense_local"]:
        grid_loop(x, y, 1, 5, 1, 1, 5, 1)
    grid_loop(x, y, data["x1"], data["y2"], data["y3"], data["y1"], data["y2"], data["y3"])
def contour_grid(x, y, isUpper):
    if isUpper:
        #for i in range(1, 8, 1):
            #pts.append([0, x + 5*i, y-2*i])
            #pts.append([0, x - 5*i, y-2*i])
            #pts.append([0, x + 5*i, y+2*i])
            #pts.append([0, x - 5*i, y+2*i])
        for i in range(0, 30, 5): #20 and 30 gave me the best ones, 10 for kids
            for z in range(0, 30, 5): #5, 30, 5, 10 for kids
                pts.append([0., x - i, y - z])
                pts.append([0., x + i, y - z])
                pts.append([0., x - i, y + z])
                pts.append([0., x + i, y + z])
    elif not isUpper:
        #for i in range(1, 8, 1):
            #pts.append([0, x + 5*i, y+2*i])
            #pts.append([0, x - 5*i, y+2*i])
            #pts.append([0, x + 5*i, y-2*i])
            #pts.append([0, x - 5*i, y-2*i])

        for i in range(0, 30, 5): # 10 for kids
            for z in range(0, 30, 5): #5, 30, 5, 10 for kids
                pts.append([0., x - i, y + z])
                pts.append([0., x + i, y + z])
                pts.append([0., x - i, y - z])
                pts.append([0., x + i, y - z])
def spiga_support():
    if video_num == 0:
        fname = "tmp/spiga_support_L.csv"
    else:
        fname = "tmp/spiga_support_R.csv"
    with open(fname) as f:
        reader_obj = csv.reader(f)
        for row in reader_obj:
            pts.append([0., float(row[1]), float(row[2])])

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--vid_name", help="Name of video")
parser.add_argument("-n", "--vid_num", help="Number of video (left = 0, right = 1)")
parser.add_argument("-e", "--exp_name", default="exp", help="Experiment name")
parser.add_argument("-gc", "--grid_config", default="global_config.json", help="Grid config file (JSON)")
parser.add_argument("-d", "--save_dir", default="/home/kwangkim/Desktop", help="Directory to save videos in")
args = parser.parse_args()

df = pd.read_csv("first_5_avg.csv")
video_file = args.vid_name
video_num = int(args.vid_num)
exp_name = args.exp_name
vid_save_dir = args.save_dir

# Path(f"/home/kwangkim/Desktop/segmented_test_9_12_24/cotracker_output_global_dense").mkdir(parents=True, exist_ok=True)
# Path(f"/home/kwangkim/Desktop/segmented_test_9_12_24/cotracker_output_global_dense/vid{video_num}").mkdir(parents=True, exist_ok=True)
Path(f"{vid_save_dir}/cotracker_out/{exp_name}").mkdir(parents=True, exist_ok=True)
Path(f"{vid_save_dir}/cotracker_out/{exp_name}/vid{video_num}").mkdir(parents=True, exist_ok=True)
# Path(f"./videos/pipeline/{exp_name}").mkdir(parents=True, exist_ok=True)
# Path(f"./videos/pipeline/{exp_name}/vid{video_num}").mkdir(parents=True, exist_ok=True)

frames = iio.imread(video_file, plugin="FFMPEG")  # plugin="pyav"
device = 'cuda'
video = torch.tensor(frames).permute(0, 3, 1, 2)[None].float().to(device)  # B T C H W

cotracker = torch.hub.load("facebookresearch/co-tracker", "cotracker2_online").to(device)

# Get points to track.
pts.append([0., float(df["x1_mean_incrop"][video_num]), float(df["y1_mean_incrop"][video_num])])
pts.append([0., float(df["x2_mean_incrop"][video_num]), float(df["y2_mean_incrop"][video_num])])
pts.append([0., float(df["x3_mean_incrop"][video_num]), float(df["y3_mean_incrop"][video_num])])
pts.append([0., float(df["x4_mean_incrop"][video_num]), float(df["y4_mean_incrop"][video_num])])
pts.append([0., float(df["x5_mean_incrop"][video_num]), float(df["y5_mean_incrop"][video_num])])
pts.append([0., float(df["x6_mean_incrop"][video_num]), float(df["y6_mean_incrop"][video_num])])
pts.append([0., float(df["x7_mean_incrop"][video_num]), float(df["y7_mean_incrop"][video_num])])
pts.append([0., float(df["x8_mean_incrop"][video_num]), float(df["y8_mean_incrop"][video_num])])
pts.append([0., float(df["x9_mean_incrop"][video_num]), float(df["y9_mean_incrop"][video_num])])
pts.append([0., float(df["x10_mean_incrop"][video_num]), float(df["y10_mean_incrop"][video_num])])

# Pull up top middle point using edge detection
print(video_file)
print(pts[9])
pts[9][1], pts[9][2] = correct_top_spiga_pt(video_file, pts[9])

with open(f"grid_configs/{args.grid_config}", "r") as read_file:
    data = json.load(read_file)
if data["global_grid"]:
    global_grid(700, 500)
if data["local_grid"]:
    # griddify(float(df["x1_mean_incrop"][video_num]), float(df["y1_mean_incrop"][video_num]))
    # griddify(float(df["x8_mean_incrop"][video_num]), float(df["y8_mean_incrop"][video_num]))
    #griddify(float(df["x7_mean_incrop"][video_num]), float(df["y7_mean_incrop"][video_num]))
    #griddify(float(df["x2_mean_incrop"][video_num]), float(df["y2_mean_incrop"][video_num]))
    griddify(float(df["x10_mean_incrop"][video_num]), float(df["y10_mean_incrop"][video_num]))
    griddify(float(df["x9_mean_incrop"][video_num]), float(df["y9_mean_incrop"][video_num]))
if "lip_contour" in data and data["lip_contour"]:
    # contour_grid(float(df["x1_mean_incrop"][video_num]), float(df["y1_mean_incrop"][video_num]), isUpper=True)
    # contour_grid(float(df["x8_mean_incrop"][video_num]), float(df["y8_mean_incrop"][video_num]), isUpper=False)
    #contour_grid(float(df["x7_mean_incrop"][video_num]), float(df["y7_mean_incrop"][video_num]), isUpper=True)
    #contour_grid(float(df["x2_mean_incrop"][video_num]), float(df["y2_mean_incrop"][video_num]), isUpper=False)
    contour_grid(float(df["x10_mean_incrop"][video_num]), float(df["y10_mean_incrop"][video_num]), isUpper=True)
    contour_grid(float(df["x9_mean_incrop"][video_num]), float(df["y9_mean_incrop"][video_num]), isUpper=False)

if "spiga_support" in data and data["spiga_support"]:
    spiga_support()

# Initialize Model
model = CoTrackerPredictor(checkpoint=os.path.join('./checkpoints/cotracker2.pth'))
if torch.cuda.is_available():
    model = model.cuda()
    video = video.cuda()
# print(f"{torch.cuda.get_device_name(torch.cuda.current_device())=}")

queries = torch.tensor(pts)
if torch.cuda.is_available():
    queries = queries.cuda()

# Run Online CoTracker, the same model with a different API:
# Initialize online processing
cotracker(video_chunk=video, is_first_step=True, queries=queries[None])

# Process the video
for ind in range(0, video.shape[1] - cotracker.step, cotracker.step):
    pred_tracks, pred_visibility = cotracker(
        video_chunk=video[:, ind : ind + cotracker.step * 2], queries=queries[None]
    )  # B T N 2,  B T N 1

# Visualize
# vis = Visualizer(save_dir=f'./videos/pipeline/{exp_name}/vid{video_num}', linewidth=3, mode='cool', tracks_leave_trace=-1)
# vis.visualize(video=video, tracks=pred_tracks, visibility=pred_visibility, filename=f'{video_num}_queries_trace', video_num=video_num)

# vis2 = Visualizer(save_dir=f'./videos/pipeline/{exp_name}/vid{video_num}', pad_value=120, linewidth=3)
# vis2.visualize(video, pred_tracks, pred_visibility, filename=f'{video_num}_queries_notrace', video_num=video_num)

vis = Visualizer(save_dir=f'{vid_save_dir}/cotracker_out/{exp_name}/vid{video_num}', linewidth=3, mode='cool', tracks_leave_trace=-1)
vis.visualize(video=video, tracks=pred_tracks, visibility=pred_visibility, filename=f'{video_num}_queries_trace', video_num=video_num)

vis2 = Visualizer(save_dir=f'{vid_save_dir}/cotracker_out/{exp_name}/vid{video_num}', pad_value=120, linewidth=3)
vis2.visualize(video, pred_tracks, pred_visibility, filename=f'{video_num}_queries_notrace', video_num=video_num)

print(f"------------------------------ VIDEOS SAVED TO {vid_save_dir}/cotracker_out/ -------------------------------------")
