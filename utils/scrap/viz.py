import os
import sys
import matplotlib.pyplot as plt
from tqdm import tqdm

import imageio
import glob
import torch
import numpy as np
import util
import subprocess
from config import config_parser
from trainer import BaseTrainer
import colorsys
from matplotlib import cm
import cv2


color_map = cm.get_cmap("jet")
fps = 10  # Frames per second to save visualization videos at.

compare_points = True
low_pt = 6
high_pt = 30


def vis_trail(scene_dir, kpts_foreground, kpts_background, save_path):
    """
    This function calculates the median motion of the background, which is subsequently
    subtracted from the foreground motion. This subtraction process "stabilizes" the camera and
    improves the interpretability of the foreground motion trails.
    """
    img_dir = os.path.join(scene_dir, "color")
    img_files = sorted(list(glob.glob(os.path.join(img_dir, "*"))))
    images = np.array([imageio.v2.imread(img_file) for img_file in img_files])

    kpts_foreground = kpts_foreground[:, ::1]  # can adjust kpts sampling rate here

    num_imgs, num_pts = kpts_foreground.shape[:2]
    print(f"{num_pts=}")

    frames = []

    x_low_pts = np.zeros(num_imgs)
    x_high_pts = np.zeros(num_imgs)
    y_low_pts = np.zeros(num_imgs)
    y_high_pts = np.zeros(num_imgs)
    for i in tqdm(range(num_imgs)):

        kpts = kpts_foreground - np.median(kpts_background - kpts_background[i], axis=1, keepdims=True)

        img_curr = images[i]

        for t in range(i):

            img1 = img_curr.copy()
            # changing opacity
            alpha = max(1 - 0.9 * ((i - t) / ((i + 1) * .99)), 0.1)

            for j in range(num_pts):
                if compare_points and j != low_pt and j != high_pt:
                    continue
                color = np.array(color_map(j/max(1, float(num_pts - 1)))[:3]) * 255

                color_alpha = 1

                hsv = colorsys.rgb_to_hsv(color[0], color[1], color[2])
                color = colorsys.hsv_to_rgb(hsv[0], hsv[1]*color_alpha, hsv[2])

                pt1 = kpts[t, j]
                pt2 = kpts[t+1, j]
                print(f"{pt1=} {pt2=}")
                p1 = (int(round(pt1[0])), int(round(pt1[1])))
                p2 = (int(round(pt2[0])), int(round(pt2[1])))

                cv2.line(img1, p1, p2, color, thickness=1, lineType=16)

            img_curr = cv2.addWeighted(img1, alpha, img_curr, 1 - alpha, 0)

        for j in range(num_pts):
            if compare_points and j != low_pt and j != high_pt:
                continue
            color = np.array(color_map(j/max(1, float(num_pts - 1)))[:3]) * 255
            pt1 = kpts[i, j]
            p1 = (int(round(pt1[0])), int(round(pt1[1])))
            cv2.circle(img_curr, p1, 2, color, -1, lineType=16)
            # cv2.putText(img_curr, f"{j}", p1, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA, True)
            # print(f"{j=} --- {pt1[0]=} --- {pt1[1]=}")
            if j == low_pt:
                x_low_pts[i] = pt1[0]
                y_low_pts[i] = pt1[1]
            elif j == high_pt:
                x_high_pts[i] = pt1[0]
                y_high_pts[i] = pt1[1]


        frames.append(img_curr)

    imageio.mimwrite(save_path, frames, quality=8, fps=fps)
    if compare_points:
        print(num_imgs)
        x = np.arange(0, num_imgs, 1)
        x_diff = np.zeros(num_imgs)
        y_diff = np.zeros(num_imgs)
        for i in range(num_imgs):
            x_diff[i] = x_high_pts[i] - x_low_pts[i]
            y_diff[i] = y_high_pts[i] - y_low_pts[i]

        fig, ax = plt.subplots()
        ax.plot(x, y_diff, linewidth=2.0, c='r', label="y diff")
        ax.plot(x, x_diff, linewidth=2.0, c='b', label="x diff")
        ax.set(ylim=(1.5 * np.min(x_diff), 1.5 * np.max(y_diff)))
        legend = ax.legend(loc='upper center', shadow=True, fontsize='x-large')
        ax.set_xlabel('frames')
        ax.set_ylabel('x and y pixel diff')
        ax.set_title('Difference between upper lip and lower lip point estimation')
        plt.savefig("viz_both_diff")

        fig, ax = plt.subplots()
        ax.plot(x, y_diff, linewidth=2.0, c='r', label="y diff")
        ax.set(ylim=(np.min(y_diff) - 5, 5 + np.max(y_diff)))
        ax.set_xlabel('frames')
        ax.set_ylabel('x and y pixel diff')
        ax.set_title('Difference between upper lip and lower lip point estimation')
        plt.savefig("viz_y_diff")

        end_frame = 170
        fig, ax = plt.subplots()
        crop_y = y_diff[0:end_frame]
        ax.plot(x[0:end_frame], crop_y, linewidth=2.0, c='r', label="y diff")
        # ax.plot(x, x_diff, linewidth=2.0, c='b', label="x diff")
        ax.set(ylim=(np.min(crop_y) - 2, 2 + np.max(crop_y)))
        ax.set_xlabel('frames')
        ax.set_ylabel('y pixel diff')
        ax.set_title('Difference between upper lip and lower lip point estimation')
        plt.savefig("viz_section_y_diff")

        with open("120_crop_gopro_out/120_crop_ydiff_6_30.npy", "wb") as f:
            np.save(f, y_diff)
        with open("120_crop_gopro_out/120_crop_xdiff_6_30.npy", "wb") as f:
            np.save(f, x_diff)


if __name__ == '__main__':
    args = config_parser()
    seq_name = os.path.basename(args.data_dir.rstrip('/'))

    trainer = BaseTrainer(args)
    num_imgs = trainer.num_imgs
    vis_dir = os.path.join(args.save_dir, '{}_{}'.format(args.expname, seq_name), 'vis')
    print('output will be saved in {}'.format(vis_dir))

    os.makedirs(vis_dir, exist_ok=True)
    query_id = args.query_frame_id
    radius = 3  # the point radius for point correspondence visualization

    mask = None
    if os.path.exists(args.foreground_mask_path):
        h, w = trainer.h, trainer.w
        mask = imageio.v2.imread(args.foreground_mask_path)[..., -1]  # rgba image, take the alpha channel
        mask = cv2.resize(mask, dsize=(w, h)) == 255

    # for DAVIS video sequences which come with segmentation masks
    # or when a foreground mask for the query frame is provided
    if trainer.with_mask or mask is not None:
        # foreground
        frames, kpts_forground = trainer.eval_video_correspondences(query_id, use_mask=True,
                                                                    mask=mask,
                                                                    vis_occlusion=args.vis_occlusion,
                                                                    occlusion_th=args.occlusion_th,
                                                                    use_max_loc=args.use_max_loc,
                                                                    radius=radius,
                                                                    return_kpts=True)
        imageio.mimwrite(os.path.join(vis_dir, '{}_{:06d}_foreground_{}.mp4'.format(seq_name, trainer.step, query_id)),
                         frames, quality=8, fps=fps)
        kpts_forground = kpts_forground.cpu().numpy()

        # background
        frames, kpts_background = trainer.eval_video_correspondences(query_id, use_mask=True,
                                                                     reverse_mask=True,
                                                                     mask=mask,
                                                                     vis_occlusion=args.vis_occlusion,
                                                                     occlusion_th=args.occlusion_th,
                                                                     use_max_loc=args.use_max_loc,
                                                                     radius=radius,
                                                                     return_kpts=True)
        kpts_background = kpts_background.cpu().numpy()
        imageio.mimwrite(os.path.join(vis_dir, '{}_{:06d}_background_{}.mp4'.format(seq_name, trainer.step, query_id)),
                         frames, quality=8, fps=fps)
        # visualize trails
        vis_trail(args.data_dir, kpts_forground, kpts_background,
                  os.path.join(vis_dir, '{}_{:06d}_{}_trails.mp4'.format(seq_name, trainer.step, query_id)))

    else:
        frames = trainer.eval_video_correspondences(query_id,
                                                    vis_occlusion=args.vis_occlusion,
                                                    occlusion_th=args.occlusion_th,
                                                    use_max_loc=args.use_max_loc,
                                                    radius=radius)
        imageio.mimwrite(os.path.join(vis_dir, '{}_{:06d}_{}.mp4'.format(seq_name, trainer.step, query_id)),
                         frames, quality=8, fps=fps)




