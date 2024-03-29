# First video should be Left Camera
fname1="$1"
fname2="$2"
exp_name="$3"
grid_config="$4"

# Find coordinates of video 1 (change thims to a loop later maybe)
echo "$fname1"
echo "Running spiga 2d on $fname1 ..."
cd ~/python-environments/env
source bin/activate
cd SPIGA/spiga/demo
python app_2d.py -i "$fname1" -d 300wprivate
mv 2d_lip_coordinates.csv ~/Projects/cotracker_new/2d_lip_coords_L.csv
mv support_pts.csv ~/Projects/cotracker_new/tmp/spiga_support_L.csv

# Find coordinates of video 2
echo "Running spiga 2d on $fname2 ..."
cd ~/python-environments/env
cd SPIGA/spiga/demo
python app_2d.py -i "$fname2" -d 300wprivate
mv 2d_lip_coordinates.csv ~/Projects/cotracker_new/2d_lip_coords_R.csv
mv support_pts.csv ~/Projects/cotracker_new/tmp/spiga_support_R.csv

# Create csv average of first 5 points and find cropped points
echo "Creating csv average..."
cd ~/Projects/cotracker_new/
pts=($(python 5pt_average.py 2d_lip_coords_L.csv 2d_lip_coords_R.csv reduce | tr -d '[],'))

# Crop video using offset based on lip points
echo "Cropping video 1..."
ffmpeg -i "$fname1" -y -nostats -loglevel 0 -filter:v "crop=700:500:${pts[0]}:${pts[1]}" vid1_crop.mp4

echo "Cropping video 2..."
ffmpeg -i "$fname2" -y -nostats -loglevel 0 -filter:v "crop=700:500:${pts[2]}:${pts[3]}" vid2_crop.mp4

# Run cotracker on first video
echo "Running cotracker on video 1..."
deactivate
source venv/bin/activate
python quickstart.py -v vid1_crop.mp4 -n 0 -e "$exp_name" -gc "$grid_config"

# Run cotracker on second video
echo "Running cotracker on video 2..."
python quickstart.py -v vid2_crop.mp4 -n 1 -e "$exp_name" -gc "$grid_config"


# Correct points to full size coordinates and save
echo "Correcting points to full size..."
python 5pt_average.py 2d_lip_coords_L.csv 2d_lip_coords_R.csv revert

echo "Running Triangulation..."
cd ~/python-environments/env
source bin/activate
cd SPIGA/spiga/demo/calibration
python calibration.py triangulate cotracker "$exp_name" "$CAM_CONFIG_PATH"


echo "Finished."