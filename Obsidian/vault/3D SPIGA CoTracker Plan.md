1. Using 2 checkpoint videos, find matrices/coefficients. Store them
	1. Done, I think
2. Using SPIGA on each of 2 experiment videos, find facial landmarks and crop videos to smaller size (size will be same). Store the offset dimension values for later
	1. Done
3. Using SPIGA on first 5 frames of 2 experiment videos, find upper and lower lip coordinates
	1. Done
4. Using these 2 coordinates for experiment video 1, run cotracker and store estimated coordinates for every frame. Repeat for experiment video 2
	1. WIP
5. Correct offset values at this step before triangulation by adding buffer back to pts
6. Using these estimated coordinates for both videos, use matrices/coefficients to determine true 3d locations.
7. Calculate Euclidean distance between 3d upper and lower lip. Hope it is consistent
	1. Output of triangulation should be in real world 3d mm coords
- Program to coordinate start time of 2 videos based on clap/sound/laser/something