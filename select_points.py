import argparse
import cv2
import os
import subprocess

RESIZE_SCALE = 3
win_name = 'Top left -> Bottom right. Press ESC when done'
points = []
is_first = True

def click_event(event, x, y, flags, params):
    global points
    global output
    global is_first
    # checking for left mouse clicks
    if event == cv2.EVENT_LBUTTONDOWN:
        x_real = x * RESIZE_SCALE
        y_real = y * RESIZE_SCALE
        points += [[x_real, y_real]]

        # displaying the coordinates
        # on the image window
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, str(x_real) + ',' +
                    str(y_real), (x, y), font,
                    1, (255, 0, 0), 2)
        cv2.imshow(win_name, img)

        if len(points) == 2:
            x_out = points[0][0]
            y_out = points[0][1]
            width_out = points[1][0] - points[0][0]
            height_out = points[1][1] - points[0][1]
            if is_first:
                output += f'drawbox=x={x_out}:y={y_out}:w={width_out}:h={height_out}:color=black@1.0:t=fill'
                is_first = False
            else:
                output += f', drawbox=x={x_out}:y={y_out}:w={width_out}:h={height_out}:color=black@1.0:t=fill'
            points = []


# driver function
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="The file")
    parser.add_argument("-l", "--is_left", help="Is it the left video", default=0)
    args = parser.parse_args()

    path = args.path
    output = f'ffmpeg -y -i {path} -vf "'

    filename, file_ext = os.path.splitext(path)
    abs_dir = os.path.dirname(os.path.abspath(path))
    if file_ext == ".mp4" or file_ext == ".MP4":
        cmd = f'ffmpeg -y -i {path} -vf "select=eq(n\\,0)" -q:v 3 tmp_select_points_img.jpg'
        subprocess.run(cmd, shell=True)
        path = 'tmp_select_points_img.jpg'

    img = cv2.imread(path, 1)
    img = cv2.resize(img, (int((5312/RESIZE_SCALE)), (int(2988/RESIZE_SCALE))), interpolation=cv2.INTER_NEAREST)
    cv2.imshow(win_name, img)
    cv2.setMouseCallback(win_name, click_event)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print(abs_dir)
    if args.is_left == "1":
        output += f'" {abs_dir}/squares_out_left.mp4'
    elif args.is_left == "0":
        output += f'" {abs_dir}/squares_out_right.mp4'
    else:
        print("Error: invalid argument for args.is_left. \nNow exiting and crashing...")
        exit(1)

    subprocess.run(output, shell=True)
