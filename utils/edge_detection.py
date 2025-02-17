import cv2 as cv
import argparse

max_lowThreshold = 100
window_name = 'Edge Map'
title_trackbar = 'Min Threshold:'
ratio = 3
kernel_size = 3


def CannyThreshold(val):
    low_threshold = val
    img_blur = cv.blur(src_gray, (3, 3))
    detected_edges = cv.Canny(img_blur, low_threshold, low_threshold * ratio, kernel_size)
    mask = detected_edges != 0
    dst = src * (mask[:, :, None].astype(src.dtype))
    x_pt = 246
    y_iter = 370
    print(mask[y_iter, x_pt])
    while mask[y_iter, x_pt] == 0:
        print(f"{x_pt}, {y_iter} - {mask[y_iter, x_pt]} - {dst[y_iter, x_pt, 0]}, {dst[y_iter, x_pt, 1]}, {dst[y_iter, x_pt, 2]}")
        y_iter -= 1
    print(f"{x_pt}, {y_iter} - {mask[y_iter, x_pt]} - {dst[y_iter, x_pt, 0]}, {dst[y_iter, x_pt, 1]}, {dst[y_iter, x_pt, 2]}")

    cv.imshow(window_name, dst)


parser = argparse.ArgumentParser(description='Code for Canny Edge Detector tutorial.')
parser.add_argument('--input', help='Path to input image.', default='/home/kwangkim/Desktop/edge2.png')
args = parser.parse_args()

src = cv.imread(cv.samples.findFile(args.input))
if src is None:
    print('Could not open or find the image: ', args.input)
    exit(0)

src_gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)

cv.namedWindow(window_name)
cv.createTrackbar(title_trackbar, window_name, 0, max_lowThreshold, CannyThreshold)

CannyThreshold(0)
cv.waitKey()