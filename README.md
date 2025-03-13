# 3D markerless tracking of speech movements with submillimeter accuracy

### [CoTracker](https://co-tracker.github.io/)

Credit to Meta and their CoTracker project, which this repository is based on.


## Install
Clone this repository and setup Conda within your environment.
- NOTE:
- create new python environment
- install python 3.10
- 
Install necessary packages
```
pip install -r requirements.txt
```

### Downloading Cotracker:
- move to cotracker subdirectory
- ensure setup.py exists, and its version is 2.0
- run
` pip install -e .`

## Guide

0. Create an empty directory, and move your left and right-angled mp4 files to this directory. Intermediate files 
   and the final output will be stored in this directory.

1. Prepare left and right-angled mp4 file videos to run CoTracker on. If the start times of the videos are not 
   already synced, then run pipeline.py to sync them. Example:
```
python pipeline.py --fps 60 --left_vid left_video.mp4 --right_vid right_video.mp4
```
- NOTE: pipeline will ask for seconds after start to look for synchronization data. Inputting 0 will cause an error.
- Inputting 1 seems to work fine
- MAJOR ISSUE:
- pipeline deletes the right video.

2. Use grid_frames.py to extract the checkerboard frames from the videos for calibration. Example:
```
python grid_frames.py -s 10 -e 500 -l left_sync_video.mp4 -r right_sync_video.mp4
```
where -s is the first frame the checkerboard appears on, and -e is the last frame.

3. Create the calibration matrices. Example:
```
python calibration.py --rows 17 --columns 24 --scaling 15 --dir /home/user/directory/
```
Where --rows is the number of rows on the checkerboard, --columns is the number of columns, and --scaling is the world 
scaling (default is 15)
- NOTE index error:
```
~/Projects/cotracker_for_lips$ python calibration.py --rows 17 --columns 24 --scaling 15 --dir ~/Projects
17 24 15
Traceback (most recent call last):
  File "/home/skill/Projects/cotracker_for_lips/calibration.py", line 385, in <module>
    mtx1, dist1, ret1 = calibrate_camera(images_folder=f'{dir}/D2/*', rows=rows, columns=columns, world_scaling=world_scaling)
  File "/home/skill/Projects/cotracker_for_lips/calibration.py", line 39, in calibrate_camera
    width = images[0].shape[1]
IndexError: list index out of range
```
 
4. Using ffmpeg, trim the videos to be under 10 seconds of length to make the program run faster. This can be done 
   by specifying the start and end time of the snippet. Example:
```
ffmpeg -ss 00:09:28 -to 00:09:34 -i right_video -c copy right_9m28s.mp4
```
Or by specifying the start time in seconds and length of snippet in frames. Example:
```
ffmpeg -ss 191 -i right_video.mp4 -c:v libx264 -c:a aac -frames:v 120 right_9m28s.mp4
```
Rename the files following the format of "right_9m28s.mp4" or "left_9m28s.mp4" and move these videos to a 
subdirectory called "samples"


5. Create a json file with your experiment details, and then use run_tests.py on that file to estimate the lip 
   coordinates. Example:
```
python run_tests.py -f foo.json
```

Where the json file is set up with the following fields:
 - "experiment_name": A String representing the chosen name of the experiment
 - "source_directory": The directory being used for the experiment
 - "times": An Array of the times of the samples listed in the String format specified in step 4.

See trial_example.json for an example of this formatting. \
After the script is finished running, the output will be saved in the directory under the cotracker_out subdirectory

