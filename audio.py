from pydub import AudioSegment
from matplotlib import pyplot as plt
from tqdm import tqdm
import numpy as np
import subprocess
import os


def compute_pcm(vid, side):
    audio_file = AudioSegment.from_file(vid)
    data = audio_file._data
    pcm16_signed_integers = []
    rng = len(data) / 8
    for sample_index in tqdm(range(int(rng))):
        sample = int.from_bytes(data[sample_index * 2:sample_index * 2 + 2], 'little', signed=True)
        pcm16_signed_integers.append(sample)
    fname = "left_audio.npy" if side == "LEFT" else "right_audio.npy"
    with open(fname, 'wb') as f:
        np.save(f, pcm16_signed_integers)
    return pcm16_signed_integers


def get_threshold(left_ints, right_ints):
    # Now plot the samples!
    plt.plot(left_ints)
    plt.plot(right_ints)
    plt.show(block=False)

    threshold = int((np.max(left_ints) + np.max(right_ints)) * (6/16))
    print(f"Threshold selected to be {threshold}")
    print("Is this value ok?")
    print("[Y/N]")
    choice = input().lower()
    if choice != "yes" and choice != 'y':
        print("Enter your threshold")
        threshold = int(input())
    print(f"Chosen threshold: {threshold}")
    return threshold


def find_sync(fps, left_video, right_video):

    print("Running on first 1/8 of video...")
    print("Running on left video")
    left_pcm16_signed_integers = compute_pcm(left_video, "LEFT")
    print("Running on right video")
    right_pcm16_signed_integers = compute_pcm(right_video, "RIGHT")
    # with open("left_audio.npy", 'rb') as f:
    #     left_pcm16_signed_integers = np.load(f)
    # with open("right_audio.npy", 'rb') as f:
    #     right_pcm16_signed_integers = np.load(f)
    print(len(left_pcm16_signed_integers))

    left_ints = np.asarray(left_pcm16_signed_integers)
    right_ints = np.asarray(right_pcm16_signed_integers)
    threshold = get_threshold(left_ints, right_ints)

    hz = 48000
    fps = int(fps)

    frame = np.where(left_ints > threshold)
    num = frame[0][0] * fps
    denom = hz * 2
    left_frame = int(num/denom)

    frame = np.where(right_ints > threshold)
    num = frame[0][0] * fps
    denom = hz * 2
    right_frame = int(num/denom)

    print(f"Left video clap frame = {left_frame}")
    print(f"Right video clap frame = {right_frame}")
    left_folder = os.path.dirname(left_video)
    right_folder = os.path.dirname(right_video)
    if right_frame <= left_frame:
        second_diff = (left_frame - right_frame) / int(fps)
        print(f"Right video starts {left_frame - right_frame} frames ({second_diff} seconds) after left video")
        str = f"ffmpeg -ss {second_diff} -i {left_video} -c:v copy -c:a copy {left_folder}/left_sync.mp4"
        print(str)
        subprocess.run(str, shell=True)
        str = f"mv {right_video} {right_folder}/right_sync.mp4"
        subprocess.run(str, shell=True)

    else:
        second_diff = (right_frame - left_frame) / int(fps)
        print(f"Left video starts {right_frame - left_frame} frames ({second_diff} seconds) after right frame")
        str = f"ffmpeg -ss {second_diff} -i {right_video} -c:v copy -c:a copy {right_folder}/right_sync.mp4"
        print(str)
        subprocess.run(str, shell=True)
        str = f"mv {left_video} {left_folder}/left_sync.mp4"
        subprocess.run(str, shell=True)
