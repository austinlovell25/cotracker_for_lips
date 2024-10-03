
# Bash
- Get numbered images from video: `ffmpeg -i right_trim.mp4 %04d.jpg`
- Renumber images starting from 0: `ls | cat -n | while read n f; do mv "$f" `printf "%04d.jpg" $n`; done`
- Trim video: `ffmpeg -ss 00:09:28 -to 00:09:34 -i 37L2038_SRTKIN_RIGHT.MP4 -c copy right_9-28_9-34.mp4`
- Start video from offset: `ffmpeg -ss 1.966 -i right_9-28_9-34.mp4 -c:v libx264 -c:a aac sync_right_9-28_9-34.mp4`
- Get cropped images: `ffmpeg -i GX010190.MP4 -qscale:v 2 -filter:v "crop=300:200:1150:520"  -start_number 0 00%03d.jpg`
- Get cropped video: `ffmpeg -i GX010176.mp4 -filter:v "crop=800:520:2480:1220" GX010176_crop.mp4`
- Start at second 191 and trim to 120 frames length: `ffmpeg -ss 191 -i 37L2045_SRTKIN_LEFT.MP4 -c:v libx264 -c:a aac -frames:v 120 left311-313.mp4`
	- Use this for left and right videos with earlier starting video having framedif/fps subtracted from start time.
- Quickly cut first x seconds of video: `ffmpeg -ss 00:05 -i input.mp4 -c:v copy -c:a copy output.mp4`


## Syncing
- Right camera: board makes contact at 2275.jpg
- Left camera: board makes contact at 2039.jpg
	- diff of 236
- Right_Video/new_imgs contains board synched with left
- Left camera = D2 = camera-1

## L2033
- checker_right_trim (1:00-1:40) snap at 4695
- checker_left_trim (1:00-1:40) snap at 2174
	- diff of 2521 -> 21.0083333333 sec
- right 2177 + left 2174
