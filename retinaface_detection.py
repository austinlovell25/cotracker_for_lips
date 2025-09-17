import spiga.demo.analyze.track.get_tracker as tr
import cv2
import numpy as np
import sys

video_input_L = sys.argv[1]
video_input_R = sys.argv[2]
cfg_retinasort = {

    'retina': {
        'model_name': 'mobile0.25',
        'extra_features': ['landmarks'],
        'postreat': {
            'resize': 1.,
            'score_thr': 0.75,
            'top_k': 5000,
            'nms_thr': 0.4,
            'keep_top_k': 50}
        },

    'sort': {
        'max_age': 1,
        'min_hits': 3,
        'iou_threshold': 0.3,
    }
}
print(cfg_retinasort['retina']['model_name'])

coordinates = []
capture = cv2.VideoCapture(video_input_L)
vid_w, vid_h = capture.get(3), capture.get(4)
faces_tracker = tr.get_tracker('RetinaSort')
faces_tracker.detector.set_input_shape(capture.get(4), capture.get(3))
ret, frame = capture.read()
features = faces_tracker.detector.inference(frame)
bboxes = features['bbox']
face_x = bboxes[0][0]
face_y = bboxes[0][1]
print(f"{face_x} {face_y}")
coordinates.append(face_x)
coordinates.append(face_y)

capture = cv2.VideoCapture(video_input_R)
vid_w, vid_h = capture.get(3), capture.get(4)
faces_tracker.detector.set_input_shape(capture.get(4), capture.get(3))
ret, frame = capture.read()
features = faces_tracker.detector.inference(frame)
bboxes = features['bbox']
face_x = bboxes[0][0]
face_y = bboxes[0][1]
print(f"{face_x} {face_y}")
coordinates.append(face_x)
coordinates.append(face_y)

np.savetxt("/home/kwangkim/Projects/cotracker_new/tmp/retinafacepts.csv", np.asarray(coordinates), delimiter=",")
