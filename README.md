# 3D markerless tracking of speech movements with sub-millimeter accuracy

### [CoTracker](https://co-tracker.github.io/)

Credit to Meta and their CoTracker project, which this repository relies on.

## Install
Clone this repository and setup a Python virtual environment using 
Python 3.10 within your environment. Ensure you have both PyTorch and TorchVision 
installed on your system. Follow the instructions on PyTorch's website [here](https://pytorch.org/get-started/locally/) 
for the installation.


Install necessary packages
```
pip install -r requirements.txt
sudo apt 
cd cotracker
pip install -e .
cd ..
cd SPIGA
pip install -e .
cd ..
mkdir checkpoints
cd checkpoints
wget https://huggingface.co/facebook/cotracker/resolve/main/cotracker2.pth
wget https://huggingface.co/facebook/cotracker3/resolve/main/scaled_online.pth
```

Download the spiga_300wprivate.pt file from this [Google Drive](https://drive.google.com/drive/folders/1olrkoiDNK_NUCscaG9BbO3qsussbDi7I)
and move under SPIGA/spiga/models/weights/ (create the weights/ directory if needed).

#### Note: Sapiens Installation
The instructions above only support running CoTracker with the SPIGA model for facial landmark detection. In order to use Sapiens, you must install it as well. Follow the installation instructions for sapiens_lite [here](https://github.com/facebookresearch/sapiens). We have included the files that were modified under /sapiens_files. We recommend following the installation instructions for sapiens and then replacing the files we changed making sure that the hard coded file paths match your systems path. Make sure to use the same directory structure that sapiens uses. The model checkpoint we used for sapiens, sapiens-pose-1b, is called sapiens_1b_goliath_best_goliath_AP_639_torchscript.pt2


## GUI Guide
We recommend using the GUI to run our software if you are not comfortable with command-line applications. Our GUI allows users to run every step of an experiment within an easy to use graphic interface. The steps for using it are listed below.
1. Create an empty directory, and move your left and right-angled mp4 files to this directory. Intermediate files and the final output will be stored in this directory.
2. Run the GUI.py script using the Python environment setup by following the install commands.
3. Select your chosen directory, left video, and right video, and enter the video's FPS and what point of the video 
   to end the search for the clap noise (e.g. if 100 is entered, then the program will 
   search for the clap noise from the start of the video to 100 seconds into the video). Click "Sync Videos" and 
   respond to the popup confirmation.
4. Enter the first and last second that the checkerboard fully appears on in the video. It does not have to be 
   perfect, however, the calibration will be more accurate the less occluded the checkerboard is. Click "Extract 
   Checkerboard Frames." This step may take a few minutes.
5. Enter the number of rows, number of columns, and length of the checkerboard in millimeters. Click "Calibrate Cameras"
6. Move to the next tab to create samples. These are the small segments of the video that will be trimmed and then 
   used for tracking in the next step. Follow the formatting guide in the GUI description and hit "Trim Samples."
   Additionally, if there are other people in the video samples that could interfere with the facial dectection system,
   we also have included a blocking functionally that allows you to cover up parts of the video so they are not tracked.
   Use this after trimming the samples if needed.
8. Move to the next tab to run the tracker. Enter an experiment name and line-separated start times based on the 
   snippets created in the previous step. This information can also be entered from a JSON file (see trial_example.json).
    Hit "Run Tracker". This step may take over 30 minutes if a large amount of samples are being processed.
9. The final results with be saved and output in the directory chosen in step 2.

## Command Line Interface Guide

1. Create an empty directory, and move your left and right-angled mp4 files to this directory. Intermediate files 
   and the final output will be stored in this directory.

2. Prepare left and right-angled mp4 file videos to run CoTracker on. If the start times of the videos are not 
   already synced, then run pipeline.py to sync them. Example:
```
python pipeline.py --fps 60 --left_vid left_video.mp4 --right_vid right_video.mp4
```

3. Use grid_frames.py to extract the checkerboard frames from the videos for calibration. Example:
Use relative paths for the videos.
```
python grid_frames.py -s 660 -e 1620 -l videos/left_sync_video.mp4 -r videos/right_sync_video.mp4
```
where -s is the first frame the checkerboard appears on, and -e is the last frame.

4. Create the calibration matrices. Example:
```
python calibration.py --rows 17 --columns 24 --scaling 15 --dir /home/user/directory/
```
Where --rows is the number of rows on the checkerboard, --columns is the number of columns, and --scaling is the world 
scaling (default is 15)

 
5. Using ffmpeg, trim the videos to be under 10 seconds of length to make the program run faster. This can be done 
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

6. Create a json file with your experiment details, and then use run_tests.py on that file to estimate the lip 
   coordinates. Example:
```
python run_tests.py -f foo.json
```

Where the json file is set up with the following fields:
 - "experiment_name": A String representing the chosen name of the experiment
 - "source_data_directory": The directory being used for the experiment
 - "save_directory": Directory to save results to
 - "cam_config_directory": Directory containing camera configuration files
 - "trimmed_or_overlay":
 - "is_use_snap": Toggle to use snapping for lip points to border
 - "is_crop_shift": Toggle to use crop shifting option
 - "is_cotracker_three": Toggle to use Cotracker 3 or Cotracker 2
 - "times": An Array of the times of the samples listed in the String format specified in step 4.

See trial_example.json for an example of this formatting. \
After the script is finished running, the output will be saved in the directory under the cotracker_out subdirectory

