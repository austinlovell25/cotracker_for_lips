#!/bin/bash

# L033
: '
export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/L2033"
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/L2033/crop_trim_left_11-38.mp4 ~/Projects/cotracker_new/assets/L2033/real_crop_sync_right_11-38.mp4 L2033_11-38_global_grid global_config.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/L2033/crop_trim_left_11-38.mp4 ~/Projects/cotracker_new/assets/L2033/real_crop_sync_right_11-38.mp4 L2033_11-38_dense_local dense_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/L2033/crop_trim_left_11-38.mp4 ~/Projects/cotracker_new/assets/L2033/real_crop_sync_right_11-38.mp4 L2033_11-38_global_and_dense_local global_and_dense_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/L2033/crop_trim_left_11-38.mp4 ~/Projects/cotracker_new/assets/L2033/real_crop_sync_right_11-38.mp4 L2033_11-38_global_and_local global_and_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/L2033/crop_trim_left_11-38.mp4 ~/Projects/cotracker_new/assets/L2033/real_crop_sync_right_11-38.mp4 L2033_11-38_global_and_sparse_local global_and_sparse_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/L2033/crop_trim_left_11-38.mp4 ~/Projects/cotracker_new/assets/L2033/real_crop_sync_right_11-38.mp4 L2033_11-38_local local.json
'

# head3
export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/head3"
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global_lip global_lip.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_lip lip_contour.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global global_config.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_dense dense_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global_dense global_and_dense_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global_local global_and_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global_sparse global_and_sparse_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_local local.json
