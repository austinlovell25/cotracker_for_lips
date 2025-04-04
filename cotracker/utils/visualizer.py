# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
import os
import numpy as np
import imageio
import torch
import tqdm
import pandas as pd

from matplotlib import cm
import torch.nn.functional as F
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw


def read_video_from_path(path):
    try:
        reader = imageio.get_reader(path)
    except Exception as e:
        print("Error opening video file: ", e)
        return None
    frames = []
    for i, im in enumerate(reader):
        frames.append(np.array(im))
    return np.stack(frames)


def draw_circle(rgb, coord, radius, color=(255, 0, 0), visible=True):
    # color = (204, 121, 167)
    #color = (0, 114, 178) # blue for regular
    color = (86, 180, 233) #skyblue for inpainted
    #color = (0,158,115) #blusihgreen for inpainted?
    # color = (213, 94, 0)
    # color = (230, 159, 0)
    # Create a draw object
    draw = ImageDraw.Draw(rgb)
    # Calculate the bounding box of the circle
    left_up_point = (coord[0] - radius, coord[1] - radius)
    right_down_point = (coord[0] + radius, coord[1] + radius)
    # Draw the circle
    draw.ellipse(
        [left_up_point, right_down_point],
        fill=tuple(color), #if visible else None,
        #outline=tuple([255, 255, 255])
    )
    return rgb


def draw_line(rgb, coord_y, coord_x, color, linewidth):
    # color = (204, 121, 167)
    # color = (213, 94, 0)
    # color = (230, 159, 0)
    draw = ImageDraw.Draw(rgb)
    draw.line(
        (coord_y[0], coord_y[1], coord_x[0], coord_x[1]),
        fill=tuple(color),
        width=linewidth,
    )
    return rgb


def add_weighted(rgb, alpha, original, beta, gamma):
    return (rgb * alpha + original * beta + gamma).astype("uint8")


class Visualizer:
    def __init__(
        self,
        save_dir: str = "./results",
        grayscale: bool = False,
        pad_value: int = 0,
        fps: int = 10,
        mode: str = "rainbow",  # 'cool', 'optical_flow'
        linewidth: int = 2,
        show_first_frame: int = 10,
        tracks_leave_trace: int = 0,  # -1 for infinite
    ):
        self.mode = mode
        self.save_dir = save_dir
        if mode == "rainbow":
            # self.color_map = cm.get_cmap("gist_rainbow")
            self.color_map = cm.get_cmap(mode)
        elif mode == "cool":
            self.color_map = cm.get_cmap(mode)
        self.show_first_frame = show_first_frame
        self.grayscale = grayscale
        self.tracks_leave_trace = tracks_leave_trace
        self.pad_value = pad_value
        self.linewidth = linewidth
        self.fps = fps

    def visualize(
        self,
        video: torch.Tensor,  # (B,T,C,H,W)
        tracks: torch.Tensor,  # (B,T,N,2)
        visibility: torch.Tensor = None,  # (B, T, N, 1) bool
        gt_tracks: torch.Tensor = None,  # (B,T,N,2)
        segm_mask: torch.Tensor = None,  # (B,1,H,W)
        filename: str = "video",
        writer=None,  # tensorboard Summary Writer, used for visualization during training
        step: int = 0,
        query_frame: int = 0,
        save_video: bool = True,
        compensate_for_camera_motion: bool = False,
        video_num: int = 42
    ):
        if compensate_for_camera_motion:
            assert segm_mask is not None
        if segm_mask is not None:
            coords = tracks[0, query_frame].round().long()
            segm_mask = segm_mask[0, query_frame][coords[:, 1], coords[:, 0]].long()

        video = F.pad(
            video,
            (self.pad_value, self.pad_value, self.pad_value, self.pad_value),
            "constant",
            255,
        )
        tracks = tracks + self.pad_value

        if self.grayscale:
            transform = transforms.Grayscale()
            video = transform(video)
            video = video.repeat(1, 1, 3, 1, 1)

        res_video = self.draw_tracks_on_video(
            video=video,
            tracks=tracks,
            visibility=visibility,
            segm_mask=segm_mask,
            gt_tracks=gt_tracks,
            query_frame=query_frame,
            compensate_for_camera_motion=compensate_for_camera_motion,
            video_num=video_num
        )
        if save_video:
            self.save_video(res_video, filename=filename, writer=writer, step=step)
        return res_video

    def save_video(self, video, filename, writer=None, step=0):
        if writer is not None:
            writer.add_video(
                filename,
                video.to(torch.uint8),
                global_step=step,
                fps=self.fps,
            )
        else:
            os.makedirs(self.save_dir, exist_ok=True)
            wide_list = list(video.unbind(1))
            wide_list = [wide[0].permute(1, 2, 0).cpu().numpy() for wide in wide_list]

            # Prepare the video file path
            save_path = os.path.join(self.save_dir, f"{filename}.mp4")

            # Create a writer object
            video_writer = imageio.get_writer(save_path, fps=self.fps)

            # Write frames to the video file
            for frame in wide_list[2:-1]:
                video_writer.append_data(frame)

            video_writer.close()


    def draw_tracks_on_video(
        self,
        video: torch.Tensor,
        tracks: torch.Tensor,
        visibility: torch.Tensor = None,
        segm_mask: torch.Tensor = None,
        gt_tracks=None,
        query_frame: int = 0,
        compensate_for_camera_motion=False,
        video_num: int = 42
    ):
        B, T, C, H, W = video.shape
        _, _, N, D = tracks.shape

        assert D == 2
        assert C == 3
        video = video[0].permute(0, 2, 3, 1).byte().detach().cpu().numpy()  # S, H, W, C
        double_tracks = tracks[0].double().detach().cpu().numpy()
        tracks = tracks[0].long().detach().cpu().numpy()  # S, N, 2
        if gt_tracks is not None:
            gt_tracks = gt_tracks[0].detach().cpu().numpy()

        res_video = []

        # process input video
        for rgb in video:
            res_video.append(rgb.copy())
        vector_colors = np.zeros((T, N, 3))

        if self.mode == "optical_flow":
            import flow_vis

            vector_colors = flow_vis.flow_to_color(tracks - tracks[query_frame][None])
        elif segm_mask is None:
            if self.mode == "rainbow":
                y_min, y_max = (
                    tracks[query_frame, :, 1].min(),
                    tracks[query_frame, :, 1].max(),
                )
                norm = plt.Normalize(y_min, y_max)
                for n in range(N):
                    color = np.array([86,180,233])[None]
                    # color = self.color_map(norm(tracks[query_frame, n, 1]))
                    # color = np.array(color[:3])[None] * 255
                    vector_colors[:, n] = np.repeat(color, T, axis=0)
            else:
                # color changes with time
                for t in range(T):
                    # color = [0, 114, 178]
                    color = np.array(self.color_map(t / T)[:3])[None] * 255
                    vector_colors[t] = np.repeat(color, N, axis=0)
        else:
            if self.mode == "rainbow":
                vector_colors[:, segm_mask <= 0, :] = 255

                y_min, y_max = (
                    tracks[0, segm_mask > 0, 1].min(),
                    tracks[0, segm_mask > 0, 1].max(),
                )
                norm = plt.Normalize(y_min, y_max)
                for n in range(N):
                    if segm_mask[n] > 0:
                        color = self.color_map(norm(tracks[0, n, 1]))
                        color = np.array(color[:3])[None] * 255
                        vector_colors[:, n] = np.repeat(color, T, axis=0)

            else:
                # color changes with segm class
                segm_mask = segm_mask.cpu()
                # color = [0, 114, 178]
                color = np.array([86,180,233])[None]
                # color = np.zeros((segm_mask.shape[0], 3), dtype=np.float32)
                # color[segm_mask > 0] = np.array(self.color_map(1.0)[:3]) * 255.0
                # color[segm_mask <= 0] = np.array(self.color_map(0.0)[:3]) * 255.0
                vector_colors = np.repeat(color[None], T, axis=0)

        #  draw tracks
        if self.tracks_leave_trace != 0:
            for t in range(query_frame + 1, T):
                first_ind = (
                    max(0, t - self.tracks_leave_trace) if self.tracks_leave_trace >= 0 else 0
                )
                curr_tracks = tracks[first_ind : t + 1]
                curr_colors = vector_colors[first_ind : t + 1]
                if compensate_for_camera_motion:
                    diff = (
                        tracks[first_ind : t + 1, segm_mask <= 0]
                        - tracks[t : t + 1, segm_mask <= 0]
                    ).mean(1)[:, None]

                    curr_tracks = curr_tracks - diff
                    curr_tracks = curr_tracks[:, segm_mask > 0]
                    curr_colors = curr_colors[:, segm_mask > 0]

                res_video[t] = self._draw_pred_tracks(
                    res_video[t],
                    curr_tracks,
                    curr_colors,
                )
                if gt_tracks is not None:
                    res_video[t] = self._draw_gt_tracks(res_video[t], gt_tracks[first_ind : t + 1])

        # T = Total number frames, t = index of frame, i = index of point
        upper_pts = np.zeros((10, T))
        lower_pts = np.zeros((10, T))
        #  draw points
        for t in range(query_frame, T):
            img = Image.fromarray(np.uint8(res_video[t]))
            for i in range(N):
                coord = (tracks[t, i, 0], tracks[t, i, 1])
                double_coord = (double_tracks[t, i, 0], double_tracks[t, i, 1])
                visibile = True
                if visibility is not None:
                    visibile = visibility[0, t, i]
                if coord[0] != 0 and coord[1] != 0:
                    if not compensate_for_camera_motion or (
                        compensate_for_camera_motion and segm_mask[i] > 0
                    ):
                        if i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
                            img = draw_circle(
                                img,
                                coord=double_coord,
                                radius=int(self.linewidth * 1),#*2
                                color=vector_colors[t, i].astype(int),
                                visible=visibile,
                            )
                    # double_coord = (double_tracks[t, i, 0], double_tracks[t, i, 1])
                    if i == 9:#9 8 6 0
                        upper_pts[0, t] = double_coord[0]
                        upper_pts[1, t] = double_coord[1]
                    elif i == 1:
                        upper_pts[2, t] = double_coord[0]
                        upper_pts[3, t] = double_coord[1]
                    elif i == 3:
                        upper_pts[4, t] = double_coord[0]
                        upper_pts[5, t] = double_coord[1]
                    elif i == 5:
                        upper_pts[6, t] = double_coord[0]
                        upper_pts[7, t] = double_coord[1]
                    elif i == 7:
                        upper_pts[8, t] = double_coord[0]
                        upper_pts[9, t] = double_coord[1]
                    elif i == 8:# 8 9 1 7
                        lower_pts[0, t] = double_coord[0]
                        lower_pts[1, t] = double_coord[1]
                    elif i == 0:
                        lower_pts[2, t] = double_coord[0]
                        lower_pts[3, t] = double_coord[1]
                    elif i == 2:
                        lower_pts[4, t] = double_coord[0]
                        lower_pts[5, t] = double_coord[1]
                    elif i == 4:
                        lower_pts[6, t] = double_coord[0]
                        lower_pts[7, t] = double_coord[1]
                    elif i == 6:
                        lower_pts[8, t] = double_coord[0]
                        lower_pts[9, t] = double_coord[1]
                    # print(f"{coord=}")
                    # print(f"{double_coord=}")

            res_video[t] = np.array(img)

        # x_diff = np.zeros(T)
        # y_diff = np.zeros(T)
        # x_diff = upper_pts[0] - lower_pts[0]
        # y_diff = upper_pts[1] - lower_pts[1]
        # x = np.arange(T)
        #
        # trial = "F"
        # many_vs_one = "one"

        # fig, ax = plt.subplots()
        # ax.plot(x, y_diff, linewidth=2.0, c='r', label="y diff")
        # legend = ax.legend(loc='lower right', shadow=True, fontsize='x-large')
        # ax.set_xlabel('frames')
        # ax.set_ylabel('y diff')
        # ax.set_title('Difference between upper lip and lower lip point estimation')
        # plt.savefig("/home/kwangkim/Projects/cotracker_new/test1")
        # print("Saving image to /home/kwangkim/Projects/cotracker_new/test1")
        #
        # fig, ax = plt.subplots()
        # ax.plot(x[0:120], upper_pts[1][0:120], linewidth=2.0, c='r', label="upper y")
        # ax.plot(x, lower_pts[1], linewidth=2.0, c='r', label="lower y")
        # legend = ax.legend(loc='lower right', shadow=True, fontsize='x-large')
        # ax.set_xlabel('frames')
        # ax.set_ylabel('y')
        # ax.set_title('Variation in y value by frame on upper and lower pts')
        # plt.savefig("/home/kwangkim/Projects/cotracker_new/test2")
        # print("Saving image to /home/kwangkim/Projects/cotracker_new/test2")

        with open(f"/home/kwangkim/Projects/cotracker_new/videos/pipeline/vid{video_num}/upper_pts.csv", "wb") as f:
            np.savetxt(f, upper_pts, delimiter=",")
        with open(f"/home/kwangkim/Projects/cotracker_new/videos/pipeline/vid{video_num}/lower_pts.csv", "wb") as f:
            np.savetxt(f, lower_pts, delimiter=",")
        out_df = pd.DataFrame(
            {'img_name': ["null"],
             'x1': [lower_pts[0, -1]],
             'y1': [lower_pts[1, -1]],
             'x2': [upper_pts[0, -1]],
             'y2': [upper_pts[1, -1]]}
        )
        out_df.to_csv(f"/home/kwangkim/Projects/cotracker_new/tmp/cotracker_end{video_num}.csv")




        #  construct the final rgb sequence
        if self.show_first_frame > 0:
            res_video = [res_video[0]] * self.show_first_frame + res_video[1:]
        return torch.from_numpy(np.stack(res_video)).permute(0, 3, 1, 2)[None].byte()

    def _draw_pred_tracks(
        self,
        rgb: np.ndarray,  # H x W x 3
        tracks: np.ndarray,  # T x 2
        vector_colors: np.ndarray,
        alpha: float = 0.5,
    ):
        T, N, _ = tracks.shape
        rgb = Image.fromarray(np.uint8(rgb))
        for s in range(T - 1):
            vector_color = vector_colors[s]
            original = rgb.copy()
            alpha = (s / T) ** 2
            for i in range(N):
                coord_y = (int(tracks[s, i, 0]), int(tracks[s, i, 1]))
                coord_x = (int(tracks[s + 1, i, 0]), int(tracks[s + 1, i, 1]))
                if coord_y[0] != 0 and coord_y[1] != 0:
                    rgb = draw_line(
                        rgb,
                        coord_y,
                        coord_x,
                        vector_color[i].astype(int),
                        self.linewidth,
                    )
            if self.tracks_leave_trace > 0:
                rgb = Image.fromarray(
                    np.uint8(add_weighted(np.array(rgb), alpha, np.array(original), 1 - alpha, 0))
                )
        rgb = np.array(rgb)
        return rgb

    def _draw_gt_tracks(
        self,
        rgb: np.ndarray,  # H x W x 3,
        gt_tracks: np.ndarray,  # T x 2
    ):
        T, N, _ = gt_tracks.shape
        color = np.array((211, 0, 0))
        rgb = Image.fromarray(np.uint8(rgb))
        for t in range(T):
            for i in range(N):
                gt_tracks = gt_tracks[t][i]
                #  draw a red cross
                if gt_tracks[0] > 0 and gt_tracks[1] > 0:
                    length = self.linewidth * 3
                    coord_y = (int(gt_tracks[0]) + length, int(gt_tracks[1]) + length)
                    coord_x = (int(gt_tracks[0]) - length, int(gt_tracks[1]) - length)
                    rgb = draw_line(
                        rgb,
                        coord_y,
                        coord_x,
                        color,
                        self.linewidth,
                    )
                    coord_y = (int(gt_tracks[0]) - length, int(gt_tracks[1]) + length)
                    coord_x = (int(gt_tracks[0]) + length, int(gt_tracks[1]) - length)
                    rgb = draw_line(
                        rgb,
                        coord_y,
                        coord_x,
                        color,
                        self.linewidth,
                    )
        rgb = np.array(rgb)
        return rgb
