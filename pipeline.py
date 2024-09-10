import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-fps", "--fps", help="Path to right video mp4")
parser.add_argument("-l", "--left_vid", help="Path to left video mp4")
parser.add_argument("-r", "--right_vid", help="Path to right video mp4")
args = parser.parse_args()