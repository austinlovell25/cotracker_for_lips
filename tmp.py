import torch
import os
import imageio.v3 as iio


from cotracker.utils.visualizer import Visualizer, read_video_from_path

frames = iio.imread('assets/120_gopro_crop.mp4', plugin="FFMPEG")  # plugin="pyav"
device = 'cuda'
grid_size = 10
video = torch.tensor(frames).permute(0, 3, 1, 2)[None].float().to(device)  # B T C H W

cotracker = torch.hub.load("facebookresearch/co-tracker", "cotracker2_online").to(device)

# Run Online CoTracker, the same model with a different API:
# Initialize online processing
cotracker(video_chunk=video, is_first_step=True, grid_size=grid_size)

# Process the video
for ind in range(0, video.shape[1] - cotracker.step, cotracker.step):
    pred_tracks, pred_visibility = cotracker(
        video_chunk=video[:, ind : ind + cotracker.step * 2]
    )  # B T N 2,  B T N 1

from cotracker.utils.visualizer import Visualizer

vis = Visualizer(save_dir="./saved_videos", pad_value=120, linewidth=3)
vis.visualize(video, pred_tracks, pred_visibility)





















import os
import torch
import cv2
import imageio.v3 as iio

from base64 import b64encode
from cotracker.utils.visualizer import Visualizer, read_video_from_path
from IPython.display import HTML

video_file = 'assets/120_gopro_crop.mp4'
# video = read_video_from_path(video_file)
# video = torch.from_numpy(video).permute(0, 3, 1, 2)[None].float()

frames = iio.imread(video_file, plugin="FFMPEG")  # plugin="pyav"
device = 'cuda'
video = torch.tensor(frames).permute(0, 3, 1, 2)[None].float().to(device)  # B T C H W

cotracker = torch.hub.load("facebookresearch/co-tracker", "cotracker2_online").to(device)


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

from cotracker.predictor import CoTrackerPredictor

model = CoTrackerPredictor(
    checkpoint=os.path.join(
        './checkpoints/cotracker2.pth'
    )
)

if torch.cuda.is_available():
    model = model.cuda()
    video = video.cuda()
print(f"{torch.cuda.is_available()=}")
print(f"{torch.cuda.device_count()=}")
print(f"{torch.cuda.current_device()=}")
print(f"{torch.cuda.get_device_name(torch.cuda.current_device())=}")
print(f"{video.shape=}")

queries = torch.tensor(pts)
if torch.cuda.is_available():
    queries = queries.cuda()

print(queries)
# Run Online CoTracker, the same model with a different API:
# Initialize online processing
cotracker(video_chunk=video, is_first_step=True, queries=queries[None])

# Process the video
for ind in range(0, video.shape[1] - cotracker.step, cotracker.step):
    print(f"{ind=}")
    pred_tracks, pred_visibility = cotracker(
        video_chunk=video[:, ind : ind + cotracker.step * 2], queries=queries[None]
    )  # B T N 2,  B T N 1

vis = Visualizer(save_dir='./videos', linewidth=3, mode='cool', tracks_leave_trace=-1)
vis.visualize(video=video, tracks=pred_tracks, visibility=pred_visibility, filename='queries')

vis2 = Visualizer(save_dir="./videos", pad_value=120, linewidth=3)
vis2.visualize(video, pred_tracks, pred_visibility)

# pred_tracks, pred_visibility = model(video, queries=queries[None])

# vis = Visualizer(
#     save_dir='./videos',
#     linewidth=3,
#     mode='cool',
#     tracks_leave_trace=-1
# )
# vis.visualize(
#     video=video,
#     tracks=pred_tracks,
#     visibility=pred_visibility,
#     filename='queries');

# pred_tracks, pred_visibility = model(video, grid_size=30)
# vis = Visualizer(save_dir='./videos', pad_value=100)
# vis.visualize(video=video, tracks=pred_tracks, visibility=pred_visibility, filename='teaser');
