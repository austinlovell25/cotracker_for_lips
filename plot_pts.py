import cv2
import pandas as pd
import numpy as np
import config

# File paths moved to config.py
#video_path = "/datadrive/individual_data/foamheadc/1m0s/foamheadc_left_sync_1m0s_trimmed.mp4"
#cotracker_path = "/home/kwangkim/Desktop/Fig2_foamheadc/cotracker_pts.csv"
#config.lip_coords_path = "/home/kwangkim/Desktop/Fig2_foamheadc/2d_lip_coordinates.csv"

#video_path = "/datadrive/individual_data/L2087/8m48s/L2087_left_sync_8m48s_trimmed.mp4"
#cotracker_path = "/home/kwangkim/Desktop/Fig2_L2087/cotracker_pts.csv"
#config.lip_coords_path = "/home/kwangkim/Desktop/Fig2_L2087/2d_lip_coordinates.csv"
#video_path = "/datadrive/individual_data/PrecisionCombo/3m43s/PrecisionCombo_left_sync_3m43s_trimmed.mp4"
#cotracker_path = "/home/kwangkim/Desktop/Fig2_PrecisionCombo/cotracker_pts.csv"
#config.lip_coords_path = "/home/kwangkim/Desktop/Fig2_PrecisionCombo/2d_lip_coordinates.csv"

#output_video_path = "output_video.mp4"
#cropped_video_path = "cropped_video.mp4"
r_l = "1" # left=1, right=2

# Load data from CSV files
cotracker_df = pd.read_csv(config.cotracker_path)
lip_coords_df = pd.read_csv(config.lip_coords_path)

# Open the video
cap = cv2.VideoCapture(config.video_path)
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# Get video properties
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Define codec and create VideoWriter for the initial output
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(config.output_video_path, fourcc, fps, (frame_width, frame_height))

frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Plot points from 2d_lip_coordinates.csv
    if frame_idx < len(lip_coords_df):
        for i in range(1, 11):
            x = lip_coords_df.loc[frame_idx, f'x{i}']
            y = lip_coords_df.loc[frame_idx, f'y{i}']
            cv2.circle(frame, (int(x), int(y)), 3, (167, 121, 204), -1)

    # Plot points from cotracker_pts.csv (f1 points)
    if frame_idx < len(cotracker_df):
        for i in range(1, 6):  # f1_x to f1_x5
            if i == 1:
                lower_x = cotracker_df.loc[frame_idx, f'f{r_l}_lower_x']
                lower_y = cotracker_df.loc[frame_idx, f'f{r_l}_lower_y']
                upper_x = cotracker_df.loc[frame_idx, f'f{r_l}_upper_x']
                upper_y = cotracker_df.loc[frame_idx, f'f{r_l}_upper_y']
            else:
                lower_x = cotracker_df.loc[frame_idx, f'f{r_l}_lower_x{i}']
                lower_y = cotracker_df.loc[frame_idx, f'f{r_l}_lower_y{i}']
                upper_x = cotracker_df.loc[frame_idx, f'f{r_l}_upper_x{i}']
                upper_y = cotracker_df.loc[frame_idx, f'f{r_l}_upper_y{i}']

            # Draw points for f1
            cv2.circle(frame, (int(lower_x), int(lower_y)), 3, (233, 180, 86), -1)
            cv2.circle(frame, (int(upper_x), int(upper_y)), 3, (233, 180, 86), -1)

    # Write the frame to the output video
    out.write(frame)

    frame_idx += 1

# Release resources for the first video
cap.release()
out.release()

# Read the output video and crop it
cap = cv2.VideoCapture(config.output_video_path)
if not cap.isOpened():
    print("Error: Could not open the output video for cropping.")
    exit()

# Define codec and create VideoWriter for the cropped video
out_cropped = cv2.VideoWriter(config.cropped_video_path, fourcc, fps, (512, 512))

frame_idx = 0
center_x = int(cotracker_df.loc[0, f'f{r_l}_upper_x'])
center_y = int(cotracker_df.loc[0, f'f{r_l}_upper_y'])

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Get the center point for cropping from cotracker_df
    if frame_idx < len(cotracker_df):

        # Calculate cropping coordinates
        crop_x1 = max(0, center_x - 256)
        crop_y1 = max(0, center_y - 256)
        crop_x2 = min(frame_width, center_x + 256)
        crop_y2 = min(frame_height, center_y + 256)

        # Crop the frame
        cropped_frame = frame[crop_y1:crop_y2, crop_x1:crop_x2]

        # Resize to 512x512 if necessary
        cropped_frame = cv2.resize(cropped_frame, (512, 512))

        # Write the cropped frame to the cropped video
        out_cropped.write(cropped_frame)

    frame_idx += 1

# Release resources for the cropped video
cap.release()
out_cropped.release()

print("Video processing complete. Saved cropped video to:", config.cropped_video_path)
