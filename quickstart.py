import os
import sys

import pandas as pd
import torch
import cv2
import imageio.v3 as iio
import numpy as np
from cotracker.utils.visualizer import Visualizer, read_video_from_path
from cotracker.predictor import CoTrackerPredictor


df = pd.read_csv("first_5_avg.csv")
video_file = sys.argv[1]
video_num = int(sys.argv[2])

frames = iio.imread(video_file, plugin="FFMPEG")  # plugin="pyav"
device = 'cuda'
video = torch.tensor(frames).permute(0, 3, 1, 2)[None].float().to(device)  # B T C H W

cotracker = torch.hub.load("facebookresearch/co-tracker", "cotracker2_online").to(device)


# Get points to track.
pts = []
pts.append([0., float(df["x1_mean_incrop"][video_num]), float(df["y1_mean_incrop"][video_num])])
pts.append([0., float(df["x2_mean_incrop"][video_num]), float(df["y2_mean_incrop"][video_num])])

def grid_loop(x, y, start1, stop1, end1, start2, stop2, end2):
    for i in range(start1, stop1, end1):
        for z in range(start2, stop2, end2):
            pts.append([0., x + i, y])
            pts.append([0., x - i, y])
            pts.append([0., x, y + z])
            pts.append([0., x, y - z])

            pts.append([0., x + i, y + z])
            pts.append([0., x + i, y - z])
            pts.append([0., x - i, y + z])
            pts.append([0., x - i, y - z])
def griddify(x, y):
    grid_loop(x, y, 1, 3, 1, 1, 3, 1)
    grid_loop(x, y, 5, 50, 5, 5, 40, 5)

griddify(float(df["x1_mean_incrop"][video_num]), float(df["y1_mean_incrop"][video_num]))
griddify(float(df["x2_mean_incrop"][video_num]), float(df["y2_mean_incrop"][video_num]))


# Initialize Model
model = CoTrackerPredictor(checkpoint=os.path.join('./checkpoints/cotracker2.pth'))
if torch.cuda.is_available():
    model = model.cuda()
    video = video.cuda()
# print(f"{torch.cuda.is_available()=}")
# print(f"{torch.cuda.device_count()=}")
# print(f"{torch.cuda.current_device()=}")
print(f"{torch.cuda.get_device_name(torch.cuda.current_device())=}")

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
vis = Visualizer(save_dir=f'./videos/pipeline/vid{video_num}', linewidth=3, mode='cool', tracks_leave_trace=-1)
vis.visualize(video=video, tracks=pred_tracks, visibility=pred_visibility, filename=f'{video_num}_queries_trace', video_num=video_num)

vis2 = Visualizer(save_dir=f'./videos/pipeline/vid{video_num}', pad_value=120, linewidth=3)
vis2.visualize(video, pred_tracks, pred_visibility, filename=f'{video_num}_queries_notrace', video_num=video_num)
