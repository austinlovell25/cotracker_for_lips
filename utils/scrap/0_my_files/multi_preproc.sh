#!/bin/bash

cd preprocessing
python main_processing.py --data_dir /home/kwangkim/Projects/omnimotion/854_480_120fps_crop/ --chain
python main_processing.py --data_dir /home/kwangkim/Projects/omnimotion/400_260_crop_gopro/

