NOTE: For all commands in this guide, make sure to replace the command line arguments with the appropriate corresponding file names and values


1. Open up PyCharm and make sure the PyCharm terminal (at the bottom) is in the directory ~/Projects/cotracker_new
2. In PyCharm terminal, run
	1. ```python pipeline.py --fps 60 --left_vid left_video.mp4 --right_vid right_video.mp4 ```
	2. IMPORTANT: Make sure fps is correct
	3. This command will take the two inputted videos, sync their start time, and save them to the same directories they were already in with the new names of left_sync_audio.mp4 and right_sync_audio.mp4
3. In PyCharm terminal, run
	1. ```python grid_frames.py -s 10 -e 500 -l /home/kwangkim/Projects/kids/GUIDE_TEST/Left_Camera/LEFT_SYNC.mp4 -r /home/kwangkim/Projects/kids/GUIDE_TEST/Right_Camera/RIGHT_SYNC.mp4```
		1. You have to specific the starting frame (-s) and the ending frame (-e) of the video where the checkerboard first enters and exits. Do this by watching the start of the videos and guess based on the times where it enters and leaves (remember to multiply by the frame rate)
	2. This produces the D2, J2, and synched folders both in the directory with the videos and identical copies in the calibration directory
4. Open up a terminal (ctrl+alt+t) and run the following commands
	1. `cd python-environments/env/`
	2. `source bin/activate`
	3. `cd SPIGA/spiga/demo/calibration/`
	4. `python calibration.py run 17 24 1.5`
		1. 17x24 is for the calibration board, and 1.5 is world scaling
		2. This will calibrate the cameras using the images of the checkerboard, and save the coefficients to some files
		3. It may take a while.
5. Using ffmpeg, trim videos to 1-5 seconds length. There are two options for doing this. Make sure to change the output file names to what they should be and run these commands in terminal in the same directory as the videos.
	1. Specify start and end times of video. example:
		1. `ffmpeg -ss 00:09:28 -to 00:09:34 -i RIGHT_SYNC.MP4 -c copy right_9-28_9-34.mp4`
	2. Specify start time in seconds and length of trimmed video in frames. example:
		1. `ffmpeg -ss 191 -i RIGHT_SYNC.MP4 -c:v libx264 -c:a aac -frames:v 120 left311-313.mp4`
	3. Either should work. The first method is probably easier though.
6. Return to the PyCharm terminal. Run the following command to run cotracker
	1. `bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/L2038/sync_left_9-28_9-34.mp4 ~/Projects/cotracker_new/assets/L2038/sync_right_9-28_9-34.mp4 testing global_lip.json`
	2. The arguments are:
		1. Trimmed left video
		2. Trimmed right video
		3. Experiment name
		4. Supporting grid
			1. The grid options are listed in the grid_configs folder
	3. Some windows will open up then close, but no user interaction is required.
7. After the previous command finished, the results will be saved under a folder in the calibration directory with the experiment name given in the previous step. The video output will be saved in ~/Projects/cotracker_new/videos/pipeline/'experiment_name'