# First video should be Left Camera
fname1="$1"
fname2="$2"
exp_name="$3"
grid_config="$4"
save_dir="$5"
CAM_CONFIG_PATH="$6"
is_snap="$7"

set -euo pipefail

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

# Create csv average of first 5 points and find cropped points
pts=($(python 5pt_average.py tmp/2d_lip_coords_L.csv tmp/2d_lip_coords_R.csv rerun | tr -d '[],'))

# Crop video using offset based on lip points
ffmpeg -hide_banner -nostats -loglevel 0 -i "$fname1" -y -nostats -loglevel 0 -filter:v "crop=704:512:${pts[0]}:${pts[1]}" tmp/vid1_crop.mp4
ffmpeg -hide_banner -nostats -loglevel 0 -i "$fname2" -y -nostats -loglevel 0 -filter:v "crop=704:512:${pts[2]}:${pts[3]}" tmp/vid2_crop.mp4

# Run cotracker on first video
python quickstart.py -v tmp/vid1_crop.mp4 -n 0 -e "$exp_name" -gc "$grid_config" -d "$save_dir" --snap_middle "$is_snap"

# Run cotracker on second video
python quickstart.py -v tmp/vid2_crop.mp4 -n 1 -e "$exp_name" -gc "$grid_config" -d "$save_dir" --snap_middle "$is_snap"

# Correct points to full size coordinates and save
python 5pt_average.py tmp/2d_lip_coords_L.csv tmp/2d_lip_coords_R.csv rerun_revert
cp tmp/cotracker_pts.csv "$save_dir"/cotracker_out/"$exp_name"/cotracker_pts.csv

python calibration.py triangulate cotracker "$exp_name" "$CAM_CONFIG_PATH" "$save_dir"

echo "Finished."