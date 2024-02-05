fname1="$1"
fname2="$2"

# Find coordinates of video 1 (change this to a loop later maybe)
echo "Running spiga 2d on $fname1 ..."
cd ~/python-environments/env
source bin/activate
cd SPIGA/spiga/demo
python app_2d.py -i "$fname1" -d 300wprivate
mv 2d_lip_coordinates.csv ~/Projects/cotracker_new/2d_lip_coords_L.csv

# Find coordinates of video 2
echo "Running spiga 2d on $fname2 ..."
cd ~/python-environments/env
cd SPIGA/spiga/demo
python app_2d.py -i "$fname2" -d 300wprivate
mv 2d_lip_coordinates.csv ~/Projects/cotracker_new/2d_lip_coords_R.csv

# Create csv average of first 5 points
echo "Creating csv average..."
cd ~/Projects/cotracker_new/
pts=($(python 5pt_average.py 2d_lip_coords_L.csv 2d_lip_coords_R.csv | tr -d '[],'))

# Crop video using offset based on lip points
echo "Cropping video 1..."
ffmpeg -i "$fname1" -y -nostats -loglevel 0 -filter:v "crop=800:800:${pts[0]}:${pts[1]}" vid1_crop.mp4

echo "Cropping video 2..."
ffmpeg -i "$fname2" -y -nostats -loglevel 0 -filter:v "crop=800:800:${pts[2]}:${pts[3]}" vid2_crop.mp4

# Run cotracker on first video
echo "Running cotracker on video 1..."
deactivate
source venv/bin/activate
python quickstart.py vid1_crop.mp4 0