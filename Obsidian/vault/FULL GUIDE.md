NOTE: For all commands in this guide, make sure to replace the command line arguments with the appropriate corresponding file names and values.


1. Open up PyCharm and make sure the PyCharm terminal (at the bottom) is in the directory ~/Projects/cotracker_new
2. In PyCharm terminal, run
	1. `python pipeline.py --fps 60 --left_vid left_video.mp4 --right_vid right_video.mp4`
	2. IMPORTANT: Make sure fps is correct
	3. This command will take the two inputted videos, sync their start time, and save them to the same directories they were already in with the new names of left_sync_audio.mp4 and right_sync_audio.mp4
3. In PyCharm terminal, run
	1. ```python grid_frames.py -s 10 -e 500 -l /home/kwangkim/Projects/kids/GUIDE_TEST/Left_Camera/left_sync_audio.mp4 -r /home/kwangkim/Projects/kids/GUIDE_TEST/Right_Camera/right_sync_audio.mp4```
		1. You have to specify the starting frame (-s) and the ending frame (-e) of the video where the checkerboard first enters and exits. Do this by watching the start of the videos and guess based on the times where it enters and leaves (remember to multiply by the frame rate)
	2. This produces the D2, J2, and synched folders both in the directory with the videos and identical copies in the calibration directory
	3. The previous D2, J2, and synched folders will be moved to a randomly named directory (name will be printed to terminal) in calibration/configs
4. Open up a terminal (ctrl+alt+t) and run the following commands
	1. `cd python-environments/env/`
	2. `source bin/activate`
	3. `cd SPIGA/spiga/demo/calibration/`
	4. `python calibration.py run 17 24 15 config_name`
		1. 17x24 is for the calibration board, and 15 is world scaling
		2. This will calibrate the cameras using the images of the checkerboard, and save the camera1.yml, camera2.yml, and stereo_coeffs.yml to calibration/ as well as calibration/configs/config_name
		3. It may take a while.
	5. The previous camera1.yml, camera2.yml, and stereo_coeffs.yml folders will be moved to a randomly named directory (name will be printed to terminal) in calibration/configs
5. Using ffmpeg, trim videos to 1-5 seconds length. There are two options for doing this. Make sure to change the output file names to what they should be and run these commands in terminal in the same directory as the videos.
	1. Specify start and end times of video. example:
		1. `ffmpeg -ss 00:09:28 -to 00:09:34 -i RIGHT_SYNC.mp4 -c copy right_9-28_9-34.mp4`
	2. OR Specify start time in seconds and length of trimmed video in frames. example:
		1. `ffmpeg -ss 191 -i RIGHT_SYNC.mp4 -c:v libx264 -c:a aac -frames:v 120 left311-313.mp4`
	3. Either should work. The first method is probably easier though.
	4. James' script also works.
6. If there are people in the video other than the subject, in PyCharm terminal run the select_points.py script as following to remove them. Otherwise, ignore this step.
	1. `python select_points.py -p left_vid.mp4 -l 1`
	2. `python select_points.py -p right_vid.mp4 -l 0`
	3. Make sure to use the output of these commands for the next step. The files saved will be named squares_out_left.mp4 and squares_out_right.mp4 and saved in the same directory as the inputted videos
7. (WHERE TO START AFTER CALCULATING TRIANGULATION) Return to the PyCharm terminal. Run the following command to run cotracker.
	1. MAKE SURE YOU HAVE THE RIGHT camera1.yml, camera2.yml, and stereo_coeffs.yml IN calibration/ !!!!!!!!!!!!!!!!!. These are the camera matrix configs that the pipeline uses.
	2. `python run_tests.py -v1 left_vid.mp4 -v2 right_vid.mp4 -t exp_name -d /home/kwangkim/directory_to_save_vids_to`
	3. The arguments are:
		1. -v1 Trimmed left video
		2. -v2 Trimmed right video
		3. -t Experiment/data name
		4. -d Directory to save videos to
	4. Or to read from a csv file
		1. -m true
		2. -f file_name.csv
	5. Some windows will open up then close, but no user interaction is required.
	6. The program will cotracker with the (possibly several) grids that are listed in the 'configs' variable in run_tests.py. You can modify the grids that will be used by referencing the grids in grid_configs/
8. After the previous command finished, the results will be saved under a folder in the calibration directory with the experiment name given in the previous step. The video output will be saved in the specified directory