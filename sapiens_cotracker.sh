#!/bin/bash
# First video should be Left Camera
fname1="$1"
fname2="$2"
exp_name="$3"
grid_config="$4"
save_dir="$5"
CAM_CONFIG_PATH="$6"
is_snap="$7"
#lip_coords_dir="$8"
json_file="$8"
is_cotracker_three="$9"

USE_CROP_SHIFTING=false

set -euo pipefail

# Check if files exist
echo "$fname1"
if [ ! -f "$fname1" ]; then
    echo "File 1 does not exist. Please try again"
    exit 1
elif [ ! -f "$fname2" ]; then
    echo "File 2 does not exist. Please try again"
    exit 1
fi



## SKIP DON'T HAVE TO WORRY ABOUT IT
if [ "$USE_CROP_SHIFTING" = true ]; then
  echo "Using crop shifting"
  cd ~/python-environments/env
  source bin/activate
  cd SPIGA/spiga/demo
  rm -f 2d_lip_coordinates.csv

  for z in {0..4}
  do
    echo "$z" > shake_opt.txt
    python app_2d.py -i "$fname1" -d 300wprivate --shake False
  done
  mv 2d_lip_coordinates.csv "$lip_coords_dir"/2d_lip_coords_L.csv
  mv support_pts.csv "$lip_coords_dir"/tmp/spiga_support_L.csv
  rm -f 2d_lip_coordinates.csv

  for z in {0..4}
  do
    echo "$z" > shake_opt.txt
    python app_2d.py -i "$fname2" -d 300wprivate --shake False
  done
  mv 2d_lip_coordinates.csv "$lip_coords_dir"/2d_lip_coords_R.csv
  mv support_pts.csv "$lip_coords_dir"/tmp/spiga_support_R.csv
  rm -f 2d_lip_coordinates.csv
  echo 0 > shake_opt.txt

else
  #  echo "Not using crop shifting"
  #  cd ~/python-environments/env
  #  source bin/activate
  #  cd SPIGA/spiga/demo
  #  python app_2d.py -i "$fname1" -d 300wprivate

  # Find coordinates of video 1
  #echo "$fname1"
  source /home/kwangkim/miniconda3/bin/deactivate
  python /home/kwangkim/Projects/cotracker_new/retinaface_detection.py "$fname1" "$fname2"


  #python SPIGA/spiga/demo/app_2d.py -i "$fname1" -d 300wprivate
  source /home/kwangkim/miniconda3/bin/activate sapiens_lite
  python /home/kwangkim/Projects/cotracker_new/sapiens_for_cotracker.py "$fname1" "$fname2" "$exp_name"
  mv /home/kwangkim/Desktop/sapiens/2d_lip_coords_L.csv tmp/2d_lip_coords_L.csv
  mv /home/kwangkim/Desktop/sapiens/support_pts_L.csv tmp/spiga_support_L.csv
  mv /home/kwangkim/Desktop/sapiens/2d_lip_coords_R.csv tmp/2d_lip_coords_R.csv
  mv /home/kwangkim/Desktop/sapiens/support_pts_R.csv tmp/spiga_support_R.csv

fi

#Create csv average of first 5 points and find cropped points

pts=($(python 5pt_average.py tmp/2d_lip_coords_L.csv tmp/2d_lip_coords_R.csv reduce | tr -d '[],'))

#echo ${pts[0]}
#Crop video using offset based on lip points
#conda activate sapiens_lite
source /home/kwangkim/miniconda3/bin/deactivate
ffmpeg -hide_banner -nostats -loglevel 0 -i "$fname1" -y -nostats -loglevel 0 -filter:v "crop=704:512:${pts[0]}:${pts[1]}" tmp/sapien_vid1_crop.mp4
ffmpeg -hide_banner -nostats -loglevel 0 -i "$fname2" -y -nostats -loglevel 0 -filter:v "crop=704:512:${pts[2]}:${pts[3]}" tmp/sapien_vid2_crop.mp4
#
#
#
## Run cotracker on first video
#deactivate

source venv/bin/activate
python quickstart.py -v tmp/sapien_vid1_crop.mp4 -n 0 -e "$exp_name" -gc "$grid_config" -d "$save_dir" --snap_middle "$is_snap" -sapiens "sapiens" --is_cotracker_three "$is_cotracker_three"

# Run cotracker   on second video
python quickstart.py -v tmp/sapien_vid2_crop.mp4 -n 1 -e "$exp_name" -gc "$grid_config" -d "$save_dir" --snap_middle "$is_snap" -sapiens "sapiens" --is_cotracker_three "$is_cotracker_three"

# Correct points to full size coordinates and save
python 5pt_average.py tmp/2d_lip_coords_L.csv tmp/2d_lip_coords_R.csv revert
cp tmp/cotracker_pts.csv "$save_dir"/sapiens_cotracker/"$exp_name"/sapiens_cotracker_pts.csv

#cd ~/python-environments/env
#source bin/activate
#cd SPIGA/spiga/demo/calibration
#echo "Listing variables"
#echo "$exp_name"
#echo "$CAM_CONFIG_PATH"
#echo "$save_dir"

## need to add cotracker_sapiens line too
python calibration.py triangulate sapiens_cotracker "$exp_name" "$CAM_CONFIG_PATH" "$save_dir"

echo "Finished."