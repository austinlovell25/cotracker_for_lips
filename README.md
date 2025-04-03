# 3D markerless tracking of speech movements with submillimeter accuracy

### [CoTracker](https://co-tracker.github.io/)

Credit to Meta and their CoTracker project, which this repository is based on.


## Install
Clone this repository and setup Conda within your environment. Repository was developed using Python 3.10

Install necessary packages
```
pip install -r requirements.txt
cd cotracker
pip install -e .
cd SPIGA
pip install -e .
```

Download the spiga_300wprivate.pt file from this [Google Drive](https://drive.google.com/drive/folders/1olrkoiDNK_NUCscaG9BbO3qsussbDi7I)
and move under SPIGA/spiga/models/weights/ (create the weights/ directory if needed).


## Guide

0. Create an empty directory, and move your left and right-angled mp4 files to this directory. Intermediate files 
   and the final output will be stored in this directory.

1. Prepare left and right-angled mp4 file videos to run CoTracker on. If the start times of the videos are not 
   already synced, then run pipeline.py to sync them. Example:
```
python pipeline.py --fps 60 --left_vid left_video.mp4 --right_vid right_video.mp4
```

- NOTE: pipeline will prompt the user for the seconds after video start to look for synchronization data.
- This must be a positive integer. Inputting 0 will cause an error.


2. Use grid_frames.py to extract the checkerboard frames from the videos for calibration. Example:
Use relative paths for the videos.
```
python grid_frames.py -s 660 -e 1620 -l videos/left_sync_video.mp4 -r videos/right_sync_video.mp4
```
where -s is the first frame the checkerboard appears on, and -e is the last frame.

3. Create the calibration matrices. Example:
```
python calibration.py --rows 17 --columns 24 --scaling 15 --dir /home/user/directory/
```
Where --rows is the number of rows on the checkerboard, --columns is the number of columns, and --scaling is the world 
scaling (default is 15)

 
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
- QUESTION: What to look for in the 10 second clip?

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

