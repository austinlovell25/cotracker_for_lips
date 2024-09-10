import argparse
from audio import find_sync
import easygui

big = 9999999999
parser = argparse.ArgumentParser()
parser.add_argument("-g", "--gui", help="Use GUI", default="False")
parser.add_argument("-fps", "--fps", help="Path to right video mp4")
parser.add_argument("-l", "--left_vid", help="Path to left video mp4")
parser.add_argument("-r", "--right_vid", help="Path to right video mp4")
parser.add_argument("-f1", "--first_frame", help="First frame checker board appears")
parser.add_argument("-f2", "--last_frame", help="Last frame checker board appears")
args = parser.parse_args()

if args.gui == "True" or args.gui == "T" or args.gui == "true" or args.gui == "t":
    fps = easygui.integerbox(msg="Enter the FPS of your videos", title="FPS", upperbound=big)
    video_dir = easygui.diropenbox("Choose directory with videos")
    left_vid = video_dir + "/left_video.mp4"
    right_vid = video_dir + "/right_video.mp4"
    find_sync(fps, left_vid, right_vid)

    frames = easygui.multenterbox(msg="Enter the first and last frame the checker board appears", title="First frame",
                                  fields=["First frame", "Last frame"])
    first_frame = int(frames[0])
    last_frame = int(frames[0])




else:
    find_sync(args.fps, args.left_vid, args.right_vid)


