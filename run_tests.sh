#!/bin/bash

# SPIGA Segmented
export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/head3"
#bash spiga_segmented.sh none none head3_30SpSeg_startlater200_none none.json
bash spiga_segmented.sh none none head3_30SpSeg_startlater200_GlLp global_lip.json
#bash spiga_segmented.sh none none head3_30SpSeg_startlater200_Gl global.json

: '
export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/head3"
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_spiga spiga.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global_spiga global_spiga.json

bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4 ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_spiga spiga.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4 ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_global_spiga global_spiga.json

export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/L2033"
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/L2033/crop_trim_left_11-38.mp4 ~/Projects/cotracker_new/assets/L2033/real_crop_sync_right_11-38.mp4 L2033_11-38_spiga spiga.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/L2033/crop_trim_left_11-38.mp4 ~/Projects/cotracker_new/assets/L2033/real_crop_sync_right_11-38.mp4 L2033_11-38_global_spiga global_spiga.json
'

: '
#Cotracker Segmented
export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/head3"
bash cotracker_segmented.sh none none head3_coseg_startlater_global_lip global_lip.json
'

: ' # head3 startlater 200 frames
export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/head3"
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 color_head3_startlater_200_global global_config.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 color_head3_startlater_200_global_local global_and_local.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 color_head3_startlater_200_lip lip_contour.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 color_head3_startlater_200_global_dense global_and_dense_local.json


#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4 ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 head3_startlater_200_global_lip global_lip.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 head3_startlater_200_lip lip_contour.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 head3_startlater_200_global global_config.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 head3_startlater_200_dense dense_local.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 head3_startlater_200_global_dense global_and_dense_local.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 head3_startlater_200_global_local global_and_local.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 head3_startlater_200_global_sparse global_and_sparse_local.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 head3_startlater_200_local local.json
#bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_startlater_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_startlater_0_200.mp4 head3_startlater_200_very_sparse_local very_sparse_local.json
'

# head3 no movement 200 frames
: '
export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/head3"
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4 ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_global_lip global_lip.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_lip lip_contour.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_global_lip global_lip.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_global global_config.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_dense dense_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_global_dense global_and_dense_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_global_local global_and_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_global_sparse global_and_sparse_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_local local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_trim_0_200.mp4  ~/Projects/cotracker_new/assets/head3/head_right_trim_0_200.mp4 head3_nomovement_very_sparse_local very_sparse_local.json
'

: '
# SPIGA Segmented
export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/head3"
bash spiga_segmented.sh none none head3_startlater_global_lip global_lip.json
'

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
: '
export CAM_CONFIG_PATH="/home/kwangkim/python-environments/env/SPIGA/spiga/demo/calibration/video_sets/head3"
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_lip lip_contour.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global_lip global_lip.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global global_config.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_dense dense_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global_dense global_and_dense_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global_local global_and_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_global_sparse global_and_sparse_local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_local local.json
bash spiga_pipeline.sh ~/Projects/cotracker_new/assets/head3/head_left_3_startlater.mp4 ~/Projects/cotracker_new/assets/head3/head_right_3_startlater.mp4 head3_startlater_very_sparse_local very_sparse_local.json
'