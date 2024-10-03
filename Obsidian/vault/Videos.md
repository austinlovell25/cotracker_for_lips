# Videos (under asset)  
- Note:   
	- "_crop" postfix means that dimensions of video are cropped to reduce total video size  
	- "_trimx-y" postfix means that video was trimmed from *x* second start time to *y* second end time   
- 1.mp4 2.mp4 - 30 1920x1080 fps videos of girl taken on phone  
- 3.mp4 - 240fps 2704×1520 videos of girl  
- GX01000x - differing FPS and lightning videos taken with gopro to compare using cotracker  
  
## Videos/many_vs_one  
- A, B, C - Testing on 30fps GX010004.mp4 to compare how cotracker does when specificing more points for support  
	- Results: tracking is more stable and accurate with more points tracked  
- D - Same experiment as above but repeated for 120fps GX01001.mp4