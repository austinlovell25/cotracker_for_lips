import os
import sys
import torch
import cv2
import imageio.v3 as iio
import numpy as np
from cotracker.utils.visualizer import Visualizer, read_video_from_path
from cotracker.predictor import CoTrackerPredictor

trial = "D"
many_or_one = "one"
vid_name = "GX010001_crop"
video_file = f'assets/{vid_name}.mp4'

frames = iio.imread(video_file, plugin="FFMPEG")  # plugin="pyav"
device = 'cuda'
video = torch.tensor(frames).permute(0, 3, 1, 2)[None].float().to(device)  # B T C H W

cotracker = torch.hub.load("facebookresearch/co-tracker", "cotracker2_online").to(device)


# Get points to track.
pts = []
def Capture_Event(event, x, y, flags, params):
    # If the left mouse button is pressed
    if event == cv2.EVENT_LBUTTONDOWN:
        # Print the coordinate of the
        # clicked point
        pts.append([0., float(x), float(y)])
        print(f"({x}, {y})")

def getFirstFrame(videofile):
    vidcap = cv2.VideoCapture(videofile)
    success, image = vidcap.read()
    if success:
        cv2.imwrite("/home/kwangkim/Projects/cotracker/first_frame.jpeg", image)  # save frame as JPEG file

getFirstFrame(video_file)
img = cv2.imread("/home/kwangkim/Projects/cotracker/first_frame.jpeg", 1)
cv2.imshow('image', img)
cv2.setMouseCallback('image', Capture_Event)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Initialize Model
model = CoTrackerPredictor(checkpoint=os.path.join('./checkpoints/cotracker2.pth'))
if torch.cuda.is_available():
    model = model.cuda()
    video = video.cuda()
print(f"{torch.cuda.is_available()=}")
print(f"{torch.cuda.device_count()=}")
print(f"{torch.cuda.current_device()=}")
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
vis = Visualizer(save_dir=f'./videos/many_vs_one/{trial}/{vid_name}', linewidth=3, mode='cool', tracks_leave_trace=-1)
vis.visualize(video=video, tracks=pred_tracks, visibility=pred_visibility, filename=f'{many_or_one}_queries_trace')

vis2 = Visualizer(save_dir=f"./videos/many_vs_one/{trial}/{vid_name}", pad_value=120, linewidth=3)
vis2.visualize(video, pred_tracks, pred_visibility, filename=f"{many_or_one}_queries_notrace")
