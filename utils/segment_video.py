import subprocess
import sys
import cv2

fname = sys.argv[1]

cap = cv2.VideoCapture(fname)
fps = round(cap.get(cv2.CAP_PROP_FPS))
total_vid_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"{total_vid_frames} -- {fps}")

segment_length = int(sys.argv[2])
lr = sys.argv[3]

start = 0.0
end = start + float(segment_length) / float(fps)
i = 0
while end < total_vid_frames / fps:
    str = f"ffmpeg -ss {start} -i {fname} -y -nostats -loglevel 0 -c:v libx264 -c:a aac -frames:v {segment_length} tmp/out{i}_{lr}.mp4"
    print(str)
    subprocess.run(str, shell=True)
    start = end
    end = start + float(segment_length) / float(fps)
    i += 1
