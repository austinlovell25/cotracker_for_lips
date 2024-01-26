#!/bin/bash

SECONDS=0

cd ..
cd preprocessing
python main_processing.py --data_dir /home/kwangkim/Projects/omnimotion/shortened_120_crop_gopro/ --chain
ELAPSED="Elapsed: $(($SECONDS / 3600))hrs $((($SECONDS / 60) % 60))min $(($SECONDS % 60))sec"
echo "$ELAPSED" > preproc_time.txt

cd ..
python train.py --config configs/new_config.txt --data_dir shortened_120_crop_gopro/
ELAPSED="Elapsed: $(($SECONDS / 3600))hrs $((($SECONDS / 60) % 60))min $(($SECONDS % 60))sec"
echo "$ELAPSED" > total_time.txt
