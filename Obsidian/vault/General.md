## Omnimotion training ideas 11/8/23
- Problem: training takes too long and records a lot of unnecessary information by tracking the background of the image.
- Idea: attempt faster training by cropping the images

### Stack trace from training on full_gopro
```Traceback (most recent call last):
  File "exhaustive_raft.py", line 110, in <module>
    run_exhaustive_flow(args)
  File "exhaustive_raft.py", line 67, in run_exhaustive_flow
    flow_low, flow_up = model(image1, image2, iters=20, test_mode=True, flow_init=flow_low_prev)
  File "/home/kwangkim/miniconda3/envs/omnimotion/lib/python3.8/site-packages/torch/nn/modules/module.py", line 1102, in _call_impl
    return forward_call(*input, **kwargs)
  File "/home/kwangkim/Projects/omnimotion/preprocessing/RAFT/core/raft.py", line 107, in forward
    corr_fn = CorrBlock(fmap1, fmap2, radius=self.args.corr_radius)
  File "/home/kwangkim/Projects/omnimotion/preprocessing/RAFT/core/corr.py", line 19, in __init__
    corr = CorrBlock.corr(fmap1, fmap2)
  File "/home/kwangkim/Projects/omnimotion/preprocessing/RAFT/core/corr.py", line 60, in corr
    return corr  / torch.sqrt(torch.tensor(dim).float())
RuntimeError: CUDA out of memory. Tried to allocate 15.37 GiB (GPU 0; 23.66 GiB total capacity; 15.69 GiB already allocated; 5.37 GiB free; 16.08 GiB reserved in total by PyTorch) If reserved memory is >> allocated memory try setting max_split_size_mb to avoid fragmentation.  See documentation for Memory Management and PYTORCH_CUDA_ALLOC_CONF
```
- Problem is due to size of image (~2700x1500), I tried using a dataset with just 5 images, and it still gave me this error
- I could not find where to reduce num_workers or batch_size or similar. Changing max_split_size_mb did not help either.

### Cropping
- Used ```ffmpeg -i GX010190.MP4 -qscale:v 2 -filter:v "crop=300:200:1150:520"  -start_number 0 00%03d.jpg``` to get cropped images.
- `fmpeg -i GX010176.mp4 -filter:v "crop=800:520:2480:1220" GX010176_crop.mp4` for cropping to video
- `ffmpeg -ss 00:00:00 -to 00:00:03 -i GX010176.mp4 -c copy GX010176_0-3.mp4` for trimming video
- Preprocessing ~800 300x200 images still takes around 16 hours just for the "computing all pairwise optical flows using exhaustive_raft.py" phase.
    - exhaustive_raft.py phase does not seem super dependent on image size as for how long it takes, preprocessing on ~600x400 images gave around the same time estimation

### Speed & Size Issues
- For 120_crop_gopro (905 images 400x260), raft_exhaustive folder was 400+ gb large (could have possibly been more but ran out of space before finishing)
	- Ended up being ~681gb for raft_exhaustive. This is for the dense pairwise optical flows from RAFT.
- For 120 frames of 400x260 images (120fps video so 1 second).
	- Total preproc + train time: 11 hours 11 mins
	- Preproc: 28 minutes
	- Train: 10 hours 43 mins

## Checklist for 12/06/23
- Run visualization of model training on one video with another video.
	- Also try using pretrained models
		- Compare
- Run Spiga and compare
- Track pixel vertical fluctuation
- Try tracking 1-3 seconds frames and overlap them.

## SPIGA -> Omnimotion Plan
- Step 1: Use SPIGA to find correct lip points on single video.
- Step 2: Preprocess and train video with omnimotion
- Step 3: Using omnimotion visualization, visualize and graph the 2 points

#### Important Notes
- Find a way to modify omnimotion training/preproc to ensure that the 2 points returned by SPIGA are being tracked by omnimotion
- Run tests on small videos so I do not have to wait years for training. 

## 1/17/24
- Using cotracker currently. quickstart.py works for tracking points but fails to correctly plot them for some reason.
	- Fixed, was due to using ints instead of floats.
- Try deeplabcut arm tracking if time is available
