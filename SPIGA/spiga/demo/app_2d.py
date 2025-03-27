import os
import cv2
import pkg_resources
import pandas as pd

# My libs
import spiga.demo.analyze.track.get_tracker as tr
import spiga.demo.analyze.extract.spiga_processor as pr_spiga
from spiga.demo.analyze.analyzer import VideoAnalyzer
from spiga.demo.visualize.viewer import Viewer
import numpy as np

import sys


class Suppressor():
    def __enter__(self):
        self.stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exception_type, value, traceback):
        sys.stdout = self.stdout
        if exception_type is not None:
            # Do normal exception handling
            raise Exception(f"Got exception: {exception_type} {value} {traceback}")

    def write(self, x): pass

    def flush(self): pass


# Paths
video_out_path_dft = pkg_resources.resource_filename('spiga', 'demo/outputs')
if not os.path.exists(video_out_path_dft):
    os.makedirs(video_out_path_dft)


def main():
    import argparse
    pars = argparse.ArgumentParser(description='Face App')
    pars.add_argument('-i', '--input', type=str, default='0', help='Video input')
    pars.add_argument('-d', '--dataset', type=str, default='wflw',
                      choices=['wflw', '300wpublic', '300wprivate', 'merlrav'],
                      help='SPIGA pretrained weights per dataset')
    pars.add_argument('-t', '--tracker', type=str, default='RetinaSort',
                      choices=['RetinaSort', 'RetinaSort_Res50'], help='Tracker name')
    pars.add_argument('-sh', '--show', nargs='+', type=str, default=['face_id', 'landmarks'],
                      choices=['fps', 'bbox', 'face_id', 'landmarks', 'headpose'],
                      help='Select the attributes of the face to be displayed ')
    pars.add_argument('-s', '--save', action='store_true', help='Save record')
    pars.add_argument('-a', '--all', action='store_true', help='Run on all frames')
    pars.add_argument('-nv', '--noview', action='store_false', help='Do not visualize the window')
    pars.add_argument('--outpath', type=str, default=video_out_path_dft, help='Video output directory')
    pars.add_argument('--fps', type=int, default=30, help='Frames per second')
    pars.add_argument('--shape', nargs='+', type=int, help='Visualizer shape (W,H)')
    pars.add_argument('--filename', type=str, default='Distance(2d).txt', help='file name')
    pars.add_argument('--shake', type=str, default='False', help='use camera shake mode')
    args = pars.parse_args()

    if args.shape:
        if len(args.shape) != 2:
            raise ValueError('--shape requires two values: width and height. Ej: --shape 256 256')
        else:
            video_shape = tuple(args.shape)
    else:
        args
    video_shape = None

    if not args.noview and not args.save:
        raise ValueError('No results will be saved neither shown')

    video_app(args.input, spiga_dataset=args.dataset, tracker=args.tracker, fps=args.fps,
              save=args.save, output_path=args.outpath, video_shape=video_shape, visualize=args.noview, plot=args.show,
              filename=args.filename, all=args.all, shake=args.shake)


def video_app(input_name, spiga_dataset=None, tracker=None, fps=30, save=False,
              output_path=video_out_path_dft, video_shape=None, visualize=True, plot=(), filename=None, all=False, shake="False"):
    # Load video
    file = open(filename, 'w')
    support_pts = []
    try:
        capture = cv2.VideoCapture(int(input_name))
        video_name = None
        if not visualize:
            print('WARNING: Webcam must be visualized in order to close the app')
        visualize = True

    except:
        try:
            capture = cv2.VideoCapture(input_name)
            video_name = input_name.split('/')[-1][:-4]
        except:
            raise ValueError('Input video path %s not valid' % input_name)

    if capture is not None:
        # Initialize viewer
        if video_shape is not None:
            vid_w, vid_h = video_shape
        else:
            vid_w, vid_h = capture.get(3), capture.get(4)
        viewer = Viewer('face_app', width=vid_w, height=vid_h, fps=fps)
        if save:
            viewer.record_video(output_path, video_name)

        # Ignore print statements
        with Suppressor():
            # Initialize face tracker
            faces_tracker = tr.get_tracker(tracker)
            faces_tracker.detector.set_input_shape(capture.get(4), capture.get(3))
            faces_tracker_flipped = tr.get_tracker(tracker)
            faces_tracker_flipped.detector.set_input_shape(capture.get(4), capture.get(3))
            # Initialize processors
            processor = pr_spiga.SPIGAProcessor(dataset=spiga_dataset)
            processor_flipped = pr_spiga.SPIGAProcessor(dataset=spiga_dataset)
            # Initialize Analyzer
            faces_analyzer = VideoAnalyzer(faces_tracker, processor=processor)
            faces_analyzer_flipped = VideoAnalyzer(faces_tracker_flipped, processor=processor_flipped)
            all_probs = []
            all_probs_flipped = []
            ids_to_remove = []
            all_ratios = []

        img_name = []
        x1 = []
        y1 = []
        x2 = []
        y2 = []
        x3 = []
        y3 = []
        x4 = []
        y4 = []
        x5 = []
        y5 = []
        x6 = []
        y6 = []
        x7 = []
        y7 = []
        x8 = []
        y8 = []
        x9 = []
        y9 = []
        x10 = []
        y10 = []

        # Convert FPS to the amount of milliseconds that each frame will be displayed
        if visualize:
            viewer.start_view()
        frame_count = -1
        while capture.isOpened():
            frame_count += 1
            # print(f"{frame_count=}")
            if shake == "False" and not all and frame_count == 1:
                break
            elif shake != "False" and not all and frame_count == 1:
                break
            elif not all and frame_count == 5:
                break
            ret, frame = capture.read()
            if ret:
                with Suppressor():
                    # Process frame
                    tracked_obj, ratio = faces_analyzer.process_frame(frame, frame_count, 0)
                    current_probs = []
                    for i, j in enumerate(faces_analyzer.tracked_obj):
                        current_probs.append(j.bbox[4])
                    faces_analyzer.tracked_obj = [j for i, j in enumerate(faces_analyzer.tracked_obj) if
                                                  j.bbox[4] == max(current_probs)]
                    img_name.append(f'img{frame_count:04}.png')
                    x1.append(faces_analyzer.tracked_obj[0].landmarks[58][0])
                    y1.append(faces_analyzer.tracked_obj[0].landmarks[58][1])
                    x2.append(faces_analyzer.tracked_obj[0].landmarks[52][0])
                    y2.append(faces_analyzer.tracked_obj[0].landmarks[52][1])

                    x3.append(faces_analyzer.tracked_obj[0].landmarks[59][0])
                    y3.append(faces_analyzer.tracked_obj[0].landmarks[59][1])
                    x4.append(faces_analyzer.tracked_obj[0].landmarks[53][0])
                    y4.append(faces_analyzer.tracked_obj[0].landmarks[53][1])

                    x5.append(faces_analyzer.tracked_obj[0].landmarks[55][0])
                    y5.append(faces_analyzer.tracked_obj[0].landmarks[55][1])
                    x6.append(faces_analyzer.tracked_obj[0].landmarks[49][0])
                    y6.append(faces_analyzer.tracked_obj[0].landmarks[49][1])

                    x7.append(faces_analyzer.tracked_obj[0].landmarks[56][0])
                    y7.append(faces_analyzer.tracked_obj[0].landmarks[56][1])
                    x8.append(faces_analyzer.tracked_obj[0].landmarks[50][0])
                    y8.append(faces_analyzer.tracked_obj[0].landmarks[50][1])

                    x9.append(faces_analyzer.tracked_obj[0].landmarks[57][0])
                    y9.append(faces_analyzer.tracked_obj[0].landmarks[57][1])
                    x10.append(faces_analyzer.tracked_obj[0].landmarks[51][0])
                    y10.append(faces_analyzer.tracked_obj[0].landmarks[51][1])

                    if frame_count == 0:
                        for z in range(68):
                            try:
                                if z not in [49, 50, 51, 52, 53, 55, 56, 57, 58, 59]:
                                    support_pts.append([0., faces_analyzer.tracked_obj[0].landmarks[z][0],
                                                        faces_analyzer.tracked_obj[0].landmarks[z][1]])
                            except:
                                print(f"{z} out of range")
                    flipped_frame = cv2.flip(frame, 1)
                    tracked_obj_flipped, ratio_flipped = faces_analyzer_flipped.process_frame(frame, frame_count, 0)
                    current_probs_flipped = []
                    for i, j in enumerate(faces_analyzer_flipped.tracked_obj):
                        current_probs_flipped.append(j.bbox[4])
                    faces_analyzer_flipped.tracked_obj = [j for i, j in enumerate(faces_analyzer_flipped.tracked_obj) if
                                                          j.bbox[4] == max(current_probs_flipped)]
                    if faces_analyzer.tracked_obj[0].headpose[0] > 0:
                        dist = (abs(faces_analyzer.tracked_obj[0].landmarks[57][0] -
                                    faces_analyzer.tracked_obj[0].landmarks[51][0]) ** 2 + abs(
                            faces_analyzer.tracked_obj[0].landmarks[57][1] -
                            faces_analyzer.tracked_obj[0].landmarks[51][1]) ** 2) ** 0.5
                        file.write(str(dist) + '\n')
                    else:
                        dist = (abs(faces_analyzer_flipped.tracked_obj[0].landmarks[57][0] -
                                    faces_analyzer_flipped.tracked_obj[0].landmarks[51][0]) ** 2 + abs(
                            faces_analyzer_flipped.tracked_obj[0].landmarks[57][1] -
                            faces_analyzer_flipped.tracked_obj[0].landmarks[51][1]) ** 2) ** 0.5
                        file.write(str(dist) + '\n')
                    # Show results
                    key = viewer.process_image(frame, drawers=[faces_analyzer], show_attributes=plot)
                    # viewer.save_canvas("/home/kwangkim/python-environments/env/SPIGA/spiga/demo/")
                    # if key:
                    #     break
            else:
                break

        capture.release()
        # viewer.close()

    if shake == "False":
        df = pd.DataFrame(list(zip(img_name, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6, x7, y7, x8, y8, x9, y9, x10, y10)),
                          columns=['img_name', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4', 'x5', 'y5', 'x6', 'y6', 'x7',
                                   'y7', 'x8', 'y8', 'x9', 'y9', 'x10', 'y10'])
        # print(df.head())
        if os.path.exists('2d_lip_coordinates.csv'):
            df.to_csv('2d_lip_coordinates.csv', mode='a', header=False)
            # print(f"Appending to 2d_lip_coordinates.csv")
        else:
            df.to_csv('2d_lip_coordinates.csv', mode='w', header=True)
            # print(f"Creating 2d_lip_coordinates.csv")

        np.savetxt("support_pts.csv", np.asarray(support_pts), delimiter=",")
    else:
        if shake == "none":
            df = pd.DataFrame(
                list(zip(img_name, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6, x7, y7, x8, y8, x9, y9, x10, y10)),
                columns=['img_name', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4', 'x5', 'y5', 'x6', 'y6', 'x7',
                         'y7', 'x8', 'y8', 'x9', 'y9', 'x10', 'y10'])
            df.to_csv('2d_lip_coordinates.csv', mode='w', header=True)
            np.savetxt("support_pts.csv", np.asarray(support_pts), delimiter=",")
        elif shake == "right":
            x1[0] = x1[0] - 100
            x2[0] = x2[0] - 100
            x3[0] = x3[0] - 100
            x4[0] = x4[0] - 100
            x5[0] = x5[0] - 100
            x6[0] = x6[0] - 100
            x7[0] = x7[0] - 100
            x8[0] = x8[0] - 100
            x9[0] = x9[0] - 100
            x10[0] = x10[0] - 100
            df = pd.DataFrame(
                list(zip(img_name, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6, x7, y7, x8, y8, x9, y9, x10, y10)),
                columns=['img_name', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4', 'x5', 'y5', 'x6', 'y6', 'x7',
                         'y7', 'x8', 'y8', 'x9', 'y9', 'x10', 'y10'])
            df.to_csv('2d_lip_coordinates.csv', mode='a', header=False)
        elif shake == "left":
            x1[0] = x1[0] + 100
            x2[0] = x2[0] + 100
            x3[0] = x3[0] + 100
            x4[0] = x4[0] + 100
            x5[0] = x5[0] + 100
            x6[0] = x6[0] + 100
            x7[0] = x7[0] + 100
            x8[0] = x8[0] + 100
            x9[0] = x9[0] + 100
            x10[0] = x10[0] + 100
            df = pd.DataFrame(
                list(zip(img_name, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6, x7, y7, x8, y8, x9, y9, x10, y10)),
                columns=['img_name', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4', 'x5', 'y5', 'x6', 'y6', 'x7',
                         'y7', 'x8', 'y8', 'x9', 'y9', 'x10', 'y10'])
            df.to_csv('2d_lip_coordinates.csv', mode='a', header=False)
        elif shake == "up":
            y1[0] = y1[0] + 100
            y2[0] = y2[0] + 100
            y3[0] = y3[0] + 100
            y4[0] = y4[0] + 100
            y5[0] = y5[0] + 100
            y6[0] = y6[0] + 100
            y7[0] = y7[0] + 100
            y8[0] = y8[0] + 100
            y9[0] = y9[0] + 100
            y10[0] = y10[0] + 100
            df = pd.DataFrame(
                list(zip(img_name, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6, x7, y7, x8, y8, x9, y9, x10, y10)),
                columns=['img_name', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4', 'x5', 'y5', 'x6', 'y6', 'x7',
                         'y7', 'x8', 'y8', 'x9', 'y9', 'x10', 'y10'])
            df.to_csv('2d_lip_coordinates.csv', mode='a', header=False)
        elif shake == "down":
            y1[0] = y1[0] - 100
            y2[0] = y2[0] - 100
            y3[0] = y3[0] - 100
            y4[0] = y4[0] - 100
            y5[0] = y5[0] - 100
            y6[0] = y6[0] - 100
            y7[0] = y7[0] - 100
            y8[0] = y8[0] - 100
            y9[0] = y9[0] - 100
            y10[0] = y10[0] - 100
            df = pd.DataFrame(
                list(zip(img_name, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6, x7, y7, x8, y8, x9, y9, x10, y10)),
                columns=['img_name', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4', 'x5', 'y5', 'x6', 'y6', 'x7',
                         'y7', 'x8', 'y8', 'x9', 'y9', 'x10', 'y10'])
            df.to_csv('2d_lip_coordinates.csv', mode='a', header=False)
        else:
            for i in range(10):
                print("Something went wrong in app2d!")




if __name__ == '__main__':
    main()
