import argparse
import cv2
import os
import subprocess

RESIZE_SCALE = 3
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", help="The file")
args = parser.parse_args()
path = args.path

filename, file_ext = os.path.splitext(path)
if file_ext == ".mp4" or file_ext == ".MP4":
    cmd = f'ffmpeg -y -i {path} -vf "select=eq(n\\,0)" -q:v 3 tmp_select_points_img.jpg'
    subprocess.run(cmd, shell=True)
    path = 'tmp_select_points_img.jpg'

img = cv2.imread(path, 1)
img = cv2.resize(img, (int((5312/RESIZE_SCALE)), (int(2988/RESIZE_SCALE))), interpolation=cv2.INTER_NEAREST)


def draw_rectangle(event, x, y, flags, params):
    # checking for left mouse clicks
    if event == cv2.EVENT_LBUTTONDOWN:
        x1 = x
        y1 = y
        x2 = x1 + int(512/RESIZE_SCALE)
        y2 = y1 + int(512/RESIZE_SCALE)

        img_copy = img.copy()
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), (255, 255, 0), 4)
        cv2.imshow('Image', img_copy)

        x1_resize = x * RESIZE_SCALE
        y1_resize = y * RESIZE_SCALE
        print(f"{x1_resize}, {y1_resize}")


cv2.imshow('Image', img)
cv2.setMouseCallback('Image', draw_rectangle)
cv2.waitKey(0)
cv2.destroyAllWindows()
