#Directory paths
import os
# For plot_pts.py
video_path = "/datadrive/individual_data/foamheadc/1m0s/foamheadc_left_sync_1m0s_trimmed.mp4"
cotracker_path = "/home/kwangkim/Desktop/Fig2_foamheadc/cotracker_pts.csv"
lip_coords_path = "/home/kwangkim/Desktop/Fig2_foamheadc/2d_lip_coordinates.csv"

output_video_path = "output_video.mp4"
cropped_video_path = "cropped_video.mp4"


# For calibration.py
calib_dir = "/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration"
spiga_demo_path = "/home/skill/Projects/cotracker_for_lips3/cotracker_for_lips/"

# For 5pt_average.py

# For calibration.py and 5pt_average.py
cotracker_new_path = os.getcwd()

cotracker_directory = os.getcwd()

#For visualiser.py which writes to upper_pts.csv and lower_pts.csv
#Read by 5pt_average.py when calling revert
upper_lower_tmp_csv_dir = os.getcwd() + "/tmp"
# For run_tests.py (Used by spiga_pipeline.sh)
#TODO replace with current directory
lip_coords_dir = os.getcwd()
# TODO:
# Parameterize all the filepaths in run_tests
# Compress user filepaths into a single input file directory, and a single output directory
