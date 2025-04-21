# First video should be Left Camera
fname1="$1"
fname2="$2"
exp_name="$3"
grid_config="$4"
save_dir="$5"
CAM_CONFIG_PATH="$6"
is_snap="$7"
lip_coords_dir="$8"
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
  echo "$fname1"
  python SPIGA/spiga/demo/app_2d.py -i "$fname1" -d 300wprivate
  mv 2d_lip_coordinates.csv tmp/2d_lip_coords_L.csv
  mv support_pts.csv tmp/spiga_support_L.csv

  # Find coordinates of video 2
  echo "$fname2"
  python SPIGA/spiga/demo/app_2d.py -i "$fname2" -d 300wprivate
  mv 2d_lip_coordinates.csv tmp/2d_lip_coords_R.csv
  mv support_pts.csv tmp/spiga_support_R.csv
fi

# Create csv average of first 5 points and find cropped points
pts=($(python 5pt_average.py tmp/2d_lip_coords_L.csv tmp/2d_lip_coords_R.csv reduce | tr -d '[],'))

# Crop video using offset based on lip points
ffmpeg -hide_banner -nostats -loglevel 0 -i "$fname1" -y -nostats -loglevel 0 -filter:v "crop=704:512:${pts[0]}:${pts[1]}" tmp/vid1_crop.mp4
ffmpeg -hide_banner -nostats -loglevel 0 -i "$fname2" -y -nostats -loglevel 0 -filter:v "crop=704:512:${pts[2]}:${pts[3]}" tmp/vid2_crop.mp4

# Run cotracker on first video
#deactivate
#source venv/bin/activate
python quickstart.py -v tmp/vid1_crop.mp4 -n 0 -e "$exp_name" -gc "$grid_config" -d "$save_dir" --snap_middle "$is_snap"

# Run cotracker on second video
python quickstart.py -v tmp/vid2_crop.mp4 -n 1 -e "$exp_name" -gc "$grid_config" -d "$save_dir" --snap_middle "$is_snap"

# Correct points to full size coordinates and save
python 5pt_average.py tmp/2d_lip_coords_L.csv tmp/2d_lip_coords_R.csv revert

#cd ~/python-environments/env
#source bin/activate
#cd SPIGA/spiga/demo/calibration
#echo "Listing variables"
#echo "$exp_name"
#echo "$CAM_CONFIG_PATH"
#echo "$save_dir"
python calibration.py triangulate cotracker "$exp_name" "$CAM_CONFIG_PATH" "$save_dir"

echo "Finished."