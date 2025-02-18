# 3D markerless tracking of speech movements with submillimeter accuracy

### [CoTracker](https://co-tracker.github.io/)

Credit to Meta and their CoTracker project, which this repository is based.

## Install
Clone this repository and setup Conda within your environment.

Install necessary packages
```
pip install -r requirements.txt
```

## Guide

1. Prepare left and right-angled mp4 file videos to run CoTracker on. If the start times of the videos are not already synced, then run pipeline.py to sync them. Example:
```
python pipeline.py --fps 60 --left_vid left_video.mp4 --right_vid right_video.mp4
```
2. Use grid_frames.py to extract the checkerboard frames from the videos for calibration. Example
```
python grid_frames.py -s 10 -e 500 -l left_sync_video.mp4 -r right_sync_video.mp4
```
where -s is the first frame the checkerboard appears on, and -e is the last frame.

3. Create the calibration matrices.
4. Using ffmpeg, trim the videos to be under 10 seconds of length to make the program run faster. This can be done by specifying the start and end time of the snippet. Example
```
ffmpeg -ss 00:09:28 -to 00:09:34 -i right_video -c copy right_video_9-28_9-34.mp4
```
Or by specifying the start time in seconds and length of snippet in frames. Example
```
ffmpeg -ss 191 -i right_video.mp4 -c:v libx264 -c:a aac -frames:v 120 right_video_191_193.mp4
```

5. Create a json file with your experiment details, and then use run_tests.py on that file to estimate the lip coordinates. Example
```
python run_tests.py -m true -f foo.json
```
