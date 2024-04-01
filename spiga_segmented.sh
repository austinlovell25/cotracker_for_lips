#!/bin/bash

full_l="/home/kwangkim/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4"
full_r="/home/kwangkim/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4"
exp_name="$3"
grid_config="$4"
end_num=14
fps=30
counter=0


echo "--------------------------------- RUNNING SPIGA -------------------------------------"
# Find coordinates of video 1 (change this to a loop later maybe)
cd ~/python-environments/env
source bin/activate
cd SPIGA/spiga/demo
python app_2d.py -i "$full_l" -d 300wprivate
mv 2d_lip_coordinates.csv ~/Projects/cotracker_new/2d_lip_coords_L.csv

# Find coordinates of video 2
cd ~/python-environments/env
cd SPIGA/spiga/demo
python app_2d.py -i "$full_r" -d 300wprivate
mv 2d_lip_coordinates.csv ~/Projects/cotracker_new/2d_lip_coords_R.csv


echo "--------------------------------- RUNNING COTRACKER ON FIRST VIDEO -------------------------------------"
# Create csv average of first 5 points and find cropped points
cd ~/Projects/cotracker_new/
pts=($(python 10pt_all.py 2d_lip_coords_L.csv 2d_lip_coords_R.csv 0 0 reduce | tr -d '[],'))
ffmpeg -i /home/kwangkim/Projects/cotracker_new/tmp/out0_l.mp4 -y -nostats -loglevel 0 -filter:v "crop=700:500:${pts[0]}:${pts[1]}" vid1_crop.mp4
ffmpeg -i /home/kwangkim/Projects/cotracker_new/tmp/out0_r.mp4 -y -nostats -loglevel 0 -filter:v "crop=700:500:${pts[2]}:${pts[3]}" vid2_crop.mp4
deactivate
source venv/bin/activate
python quickstart.py -v vid1_crop.mp4 -n 0 -e "$exp_name" -gc "$grid_config"
python quickstart.py -v vid2_crop.mp4 -n 1 -e "$exp_name" -gc "$grid_config"
python 10pt_all.py 2d_lip_coords_L.csv 2d_lip_coords_R.csv 0 0 revert 0


for i in $(seq 1 "$end_num");
do
  # First video should be Left Camera
  fname1="/home/kwangkim/Projects/cotracker_new/tmp/out${i}_l.mp4"
  fname2="/home/kwangkim/Projects/cotracker_new/tmp/out${i}_r.mp4"
  echo "--------------------------------- RUNNING ON $fname1 -------------------------------------"

  # Create csv average of first 5 points and find cropped points
  cd ~/Projects/cotracker_new/
  pts=($(python 10pt_all.py 2d_lip_coords_L.csv 2d_lip_coords_R.csv ${i} 30 reduce | tr -d '[],'))

  # Crop video using offset based on lip points
  ffmpeg -i "$fname1" -y -nostats -loglevel 0 -filter:v "crop=700:500:${pts[0]}:${pts[1]}" vid1_crop.mp4
  ffmpeg -i "$fname2" -y -nostats -loglevel 0 -filter:v "crop=700:500:${pts[2]}:${pts[3]}" vid2_crop.mp4

  # Run cotracker
  deactivate
  source venv/bin/activate
  python quickstart.py -v vid1_crop.mp4 -n 0 -e "$exp_name" -gc "$grid_config"
  python quickstart.py -v vid2_crop.mp4 -n 1 -e "$exp_name" -gc "$grid_config"

  # Correct points to full size coordinates and save
  python 10pt_all.py 2d_lip_coords_L.csv 2d_lip_coords_R.csv 0 0 revert "$i"
done

python stack_dataframes.py

cd ~/python-environments/env
source bin/activate
cd SPIGA/spiga/demo/calibration
python calibration.py triangulate cotracker "$exp_name" "$CAM_CONFIG_PATH"
echo "------------------------------------- FIN ------------------------------------------"