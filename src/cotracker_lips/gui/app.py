"""Main GUI — wraps the pipeline in a 3-tab customtkinter wizard.

This module is UI only: every button delegates to the corresponding function
in the rest of the package. No subprocess calls, no business logic.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Literal

import customtkinter as ctk
import cv2
import matplotlib.pyplot as plt
import numpy as np
from customtkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from cotracker_lips.calibration import extract_checkerboard_frames, run_calibration
from cotracker_lips.config import Config, load_config
from cotracker_lips.io import ffmpeg
from cotracker_lips.pipeline import SampleSpec, run_pipeline
from cotracker_lips.sync import (
    align_stereo_videos,
    detect_clap_frames,
    extract_pcm,
    suggested_threshold,
    StereoSync,
)

logger = logging.getLogger(__name__)

WINDOW_GEOMETRY = "1200x1200"
HEADER_FONT_SIZE = 20
BODY_FONT_SIZE = 16
LABEL_FONT = ctk.CTkFont
WRAP = 300

TrackerChoice = Literal["Spiga", "Sapiens"]
CotrackerChoice = Literal["Cotracker2", "Cotracker3"]


def _font(size: int = BODY_FONT_SIZE) -> tuple[type, int]:
    return (LABEL_FONT, size)


class App(ctk.CTk):
    def __init__(self, cfg: Config) -> None:
        super().__init__()
        self._cfg = cfg

        # Pipeline state
        self.data_dir: Path | None = None
        self.left_video: Path | None = None
        self.right_video: Path | None = None
        self.json_run: dict | None = None
        self.left_img_pts: list[int] = [0, 0, 0, 0]
        self.right_img_pts: list[int] = [0, 0, 0, 0]
        self.left_image_fig = None
        self.right_image_fig = None
        self.running_message: ctk.CTkLabel | None = None
        self.plt_canvas: FigureCanvasTkAgg | None = None
        self.rmse_label: ctk.CTkLabel | None = None
        self.inspect_label: ctk.CTkLabel | None = None

        self.title("CoTracker for lips")
        self.geometry(WINDOW_GEOMETRY)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tab1 = self.tabview.add("Calibrate Cameras")
        self.tab2 = self.tabview.add("Create Samples")
        self.tab3 = self.tabview.add("Run Tracker")
        for button in self.tabview._segmented_button._buttons_dict.values():
            button.configure(width=100, height=50, font=_font())

        self._build_tab1()
        self._build_tab2()
        self._build_tab3()

    # ---------- Tab 1 — sync, checkerboard, calibrate ---------- #

    def _build_tab1(self) -> None:
        ctk.CTkLabel(
            self.tab1,
            text="1. Choose a directory with the left and right videos, enter FPS, "
                 "and the upper bound (in seconds) for clap detection.",
            font=_font(HEADER_FONT_SIZE),
            wraplength=WRAP,
        ).grid(row=0, column=0, pady=(20, 20), padx=40, sticky="nw")

        ctk.CTkButton(self.tab1, text="Select Directory", command=self.select_dir,
                      font=_font()).grid(row=1, column=0, pady=(5, 0))
        self.selected_dir_label = ctk.CTkLabel(self.tab1, text="Selected Dir: ", font=_font())
        self.selected_dir_label.grid(row=2, column=0, pady=(0, 2))

        ctk.CTkButton(self.tab1, text="Select Left Video", command=self.select_left_video,
                      font=_font()).grid(row=3, column=0, pady=(5, 0))
        self.selected_left_vid_label = ctk.CTkLabel(self.tab1, text="Selected Video: ", font=_font())
        self.selected_left_vid_label.grid(row=4, column=0, pady=(0, 2))

        ctk.CTkButton(self.tab1, text="Select Right Video", command=self.select_right_video,
                      font=_font()).grid(row=5, column=0, pady=(5, 0))
        self.selected_right_vid_label = ctk.CTkLabel(self.tab1, text="Selected Video: ", font=_font())
        self.selected_right_vid_label.grid(row=6, column=0, pady=(0, 2))

        ctk.CTkLabel(self.tab1, text="FPS", font=_font()).grid(row=7, column=0, pady=5)
        self.fps_entry = ctk.CTkEntry(self.tab1, placeholder_text="0", font=_font())
        self.fps_entry.grid(row=8, column=0, pady=5)

        ctk.CTkLabel(
            self.tab1,
            text="Seconds-from-start within which to search for the clap.",
            font=_font(),
            wraplength=WRAP,
        ).grid(row=9, column=0, pady=10)
        self.clapperboard_entry = ctk.CTkEntry(self.tab1, placeholder_text="60", font=_font())
        self.clapperboard_entry.grid(row=10, column=0, pady=10)

        ctk.CTkButton(self.tab1, text="Sync Videos", command=self.sync_videos,
                      font=_font()).grid(row=11, column=0, pady=5)

        # Column 2 — checkerboard
        ctk.CTkLabel(
            self.tab1,
            text="2. Enter the first / last second the checkerboard fully appears in the videos.",
            font=_font(HEADER_FONT_SIZE),
            wraplength=WRAP,
        ).grid(row=0, column=1, pady=(20, 20), padx=40)

        ctk.CTkLabel(self.tab1, text="First second", font=_font()).grid(row=1, column=1, pady=5)
        self.first_grid_second_entry = ctk.CTkEntry(self.tab1, placeholder_text="0", font=_font())
        self.first_grid_second_entry.grid(row=2, column=1, pady=5)

        ctk.CTkLabel(self.tab1, text="Last second", font=_font()).grid(row=3, column=1, pady=5)
        self.last_grid_second_entry = ctk.CTkEntry(self.tab1, placeholder_text="100", font=_font())
        self.last_grid_second_entry.grid(row=4, column=1, pady=5)

        ctk.CTkButton(self.tab1, text="Extract Checkerboard Frames", command=self.checkerboard,
                      font=_font()).grid(row=6, column=1, pady=5)

        # Column 3 — calibrate
        ctk.CTkLabel(
            self.tab1,
            text="3. Enter rows × columns and the square length (mm).",
            font=_font(HEADER_FONT_SIZE),
            wraplength=WRAP,
        ).grid(row=0, column=2, pady=(20, 20), padx=40)

        self.rows_entry = ctk.CTkEntry(self.tab1, placeholder_text="rows", font=_font())
        self.rows_entry.grid(row=1, column=2, pady=5)
        self.columns_entry = ctk.CTkEntry(self.tab1, placeholder_text="columns", font=_font())
        self.columns_entry.grid(row=2, column=2, pady=5)
        self.scaling_entry = ctk.CTkEntry(self.tab1, placeholder_text="length (mm)", font=_font())
        self.scaling_entry.grid(row=3, column=2, pady=5)

        ctk.CTkButton(self.tab1, text="Calibrate Cameras", command=self.calibrate,
                      font=_font()).grid(row=6, column=2, pady=5)

        ctk.CTkButton(self.tab1, text="Inspect Video", command=self.inspect,
                      font=_font()).grid(row=8, column=2, pady=5)

    # ---------- Tab 2 — trim + block ---------- #

    def _build_tab2(self) -> None:
        ctk.CTkLabel(
            self.tab2,
            text="4. List samples to trim. One per line: ``<start>, <length_seconds>`` "
                 "(e.g. ``1m35s, 2`` for a 2-second snippet starting at 1:35).",
            font=_font(HEADER_FONT_SIZE),
            wraplength=WRAP,
        ).grid(row=0, column=0, pady=(20, 20), rowspan=2, sticky="nw", padx=(40, 0))

        self.times_textbox = ctk.CTkTextbox(self.tab2)
        self.times_textbox.grid(row=2, column=0, rowspan=7, sticky="nsew", padx=(40, 0))

        ctk.CTkButton(self.tab2, text="Trim Samples", command=self.trim,
                      font=_font()).grid(row=10, column=0, pady=5, padx=(40, 0))

        ctk.CTkLabel(
            self.tab2,
            text="(Optional) draw a black rectangle to occlude regions of the samples.",
            font=_font(HEADER_FONT_SIZE),
            wraplength=WRAP,
        ).grid(row=0, column=1, pady=(20, 20), padx=(40, 0))

        ctk.CTkButton(self.tab2, text="Draw Black Box", command=self.open_block_video,
                      font=_font()).grid(row=1, column=1, pady=5, padx=(40, 0))

        ctk.CTkLabel(
            self.tab2,
            text="Left-click = top-left, right-click = bottom-right.",
            font=_font(),
            wraplength=WRAP,
        ).grid(row=10, column=1, pady=5, padx=(40, 0))

        self.left_pt1_label = ctk.CTkLabel(self.tab2, text="Top Left: ", font=_font())
        self.left_pt1_label.grid(row=11, column=1, pady=5, padx=(40, 0))
        self.left_pt2_label = ctk.CTkLabel(self.tab2, text="Bottom Right: ", font=_font())
        self.left_pt2_label.grid(row=12, column=1, pady=5, padx=(40, 0))

        ctk.CTkButton(self.tab2, text="Block Selection", command=self.run_block,
                      font=_font()).grid(row=13, column=1, pady=5, padx=(40, 0))

        self.right_pt1_label = ctk.CTkLabel(self.tab2, text="Top Left: ", font=_font())
        self.right_pt1_label.grid(row=11, column=3, pady=5, padx=(40, 0))
        self.right_pt2_label = ctk.CTkLabel(self.tab2, text="Bottom Right: ", font=_font())
        self.right_pt2_label.grid(row=12, column=3, pady=5, padx=(40, 0))

    # ---------- Tab 3 — run ---------- #

    def _build_tab3(self) -> None:
        ctk.CTkLabel(
            self.tab3,
            text="5. Enter experiment name and a line-separated list of sample times "
                 "(e.g. 1m35s). Or upload a JSON spec.",
            font=_font(HEADER_FONT_SIZE),
            wraplength=WRAP,
        ).grid(row=0, column=1, pady=(20, 20), sticky="nw", padx=(40, 0))

        ctk.CTkButton(self.tab3, text="Upload JSON", command=self.open_json,
                      font=_font()).grid(row=1, column=1, pady=5, padx=(40, 0))

        ctk.CTkLabel(self.tab3, text="Experiment name", font=_font(HEADER_FONT_SIZE)).grid(
            row=2, column=1, pady=(2, 0), padx=(40, 0))
        self.experiment_entry = ctk.CTkEntry(self.tab3, font=_font())
        self.experiment_entry.grid(row=3, column=1, pady=5, padx=(40, 0))

        self.run_textbox = ctk.CTkTextbox(self.tab3)
        self.run_textbox.grid(row=4, column=1, rowspan=7, sticky="nsew", padx=(40, 0))

        self.cotracker_var = ctk.StringVar(value="Cotracker3")
        ctk.CTkOptionMenu(
            self.tab3, values=["Cotracker2", "Cotracker3"],
            font=_font(), variable=self.cotracker_var,
        ).grid(row=12, column=1, pady=10, padx=(40, 0))

        self.tracker_var = ctk.StringVar(value="Spiga")
        ctk.CTkOptionMenu(
            self.tab3, values=["Spiga", "Sapiens"],
            font=_font(), variable=self.tracker_var,
        ).grid(row=13, column=1, pady=10, padx=(40, 0))

        ctk.CTkButton(self.tab3, text="Run Tracker", command=self.track,
                      font=_font()).grid(row=14, column=1, pady=10, padx=(40, 0))

    # ---------- handlers ---------- #

    def show_error(self, msg: str) -> None:
        messagebox.showerror("Error", msg)

    def select_dir(self) -> None:
        path = filedialog.askdirectory()
        if not path:
            return
        self.data_dir = Path(path).resolve()
        self.selected_dir_label.configure(text=f"Selected Dir: {self.data_dir.name}")

    def select_left_video(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(self.data_dir) if self.data_dir else None,
            filetypes=[("MP4 Files", ["*.mp4", "*.MP4"])],
        )
        if not path:
            return
        self.left_video = Path(path).resolve()
        self.selected_left_vid_label.configure(text=f"Selected Video: {self.left_video.name}")

    def select_right_video(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(self.data_dir) if self.data_dir else None,
            filetypes=[("MP4 Files", ["*.mp4", "*.MP4"])],
        )
        if not path:
            return
        self.right_video = Path(path).resolve()
        self.selected_right_vid_label.configure(text=f"Selected Video: {self.right_video.name}")

    def inspect(self) -> None:
        if self.left_video is None:
            self.show_error("Select a left video first.")
            return
        cap = cv2.VideoCapture(str(self.left_video))
        if not cap.isOpened():
            text = "Could not open video."
        else:
            fps = round(cap.get(cv2.CAP_PROP_FPS))
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            text = f"FPS: {fps}\nResolution: {w}x{h}"
        cap.release()
        if self.inspect_label is not None:
            self.inspect_label.destroy()
        self.inspect_label = ctk.CTkLabel(
            self.tab1, text=text, font=_font(HEADER_FONT_SIZE), wraplength=WRAP
        )
        self.inspect_label.grid(row=9, column=2, pady=(20, 20), padx=(40, 0))

    def sync_videos(self) -> None:
        if self.data_dir is None or self.left_video is None or self.right_video is None:
            self.show_error("Select directory and both videos first.")
            return
        try:
            fps = int(self.fps_entry.get())
            range_end = int(self.clapperboard_entry.get())
        except ValueError:
            self.show_error("FPS and clap window must be positive integers.")
            return

        self.waiting(self.tab1, "Syncing videos…")
        cfg = self._cfg_for_dir()

        left_pcm = extract_pcm(self.left_video, range_end_sec=range_end)
        right_pcm = extract_pcm(self.right_video, range_end_sec=range_end)
        threshold = self._prompt_threshold(left_pcm, right_pcm, range_end)
        left_frame, right_frame = detect_clap_frames(
            left_pcm, right_pcm,
            fps=fps,
            sample_rate_hz=cfg.audio_sample_rate_hz,
            threshold=threshold,
        )
        sync = StereoSync(left_clap_frame=left_frame, right_clap_frame=right_frame, threshold=threshold)
        align_stereo_videos(
            fps=fps,
            left_video=self.left_video,
            right_video=self.right_video,
            sync=sync,
            out_left=cfg.work_dir / "left_sync.mp4",
            out_right=cfg.work_dir / "right_sync.mp4",
        )
        self.left_video = cfg.work_dir / "left_sync.mp4"
        self.right_video = cfg.work_dir / "right_sync.mp4"
        self.selected_left_vid_label.configure(text=f"Selected Video: {self.left_video.name}")
        self.selected_right_vid_label.configure(text=f"Selected Video: {self.right_video.name}")
        self.finished()

    def _prompt_threshold(self, left: np.ndarray, right: np.ndarray, range_end: int) -> int:
        fig, ax = plt.subplots(figsize=(5, 4))
        x_vals = np.linspace(0, range_end, left.size)
        ax.plot(x_vals, left, label="left")
        ax.plot(x_vals, right, label="right")
        ax.set_title("Audio waveforms (clap search window)")
        ax.set_xlabel("seconds")
        ax.set_ylabel("amplitude")
        ax.legend()
        self.plt_canvas = FigureCanvasTkAgg(fig, master=self.tab1)
        self.plt_canvas.get_tk_widget().grid(row=12, column=1, columnspan=2, padx=10, pady=10)

        threshold = suggested_threshold(left, right, ratio=self._cfg.clap_threshold_ratio)
        choice_var = ctk.StringVar()
        check_label = ctk.CTkLabel(
            self.tab1,
            text=f"Suggested threshold: {threshold}. OK?",
            font=_font(24), text_color="Red", wraplength=WRAP,
        )
        check_label.grid(row=11, column=1, columnspan=2, pady=2)
        combobox = ctk.CTkComboBox(self.tab1, values=["Yes", "No"], variable=choice_var, font=_font())
        combobox.grid(row=10, column=1, columnspan=2, pady=2)
        check_label.waitvar(choice_var)
        check_label.destroy()
        combobox.destroy()

        if choice_var.get() == "No":
            label = ctk.CTkLabel(self.tab1, text="Enter desired threshold:", font=_font(24))
            label.grid(row=10, column=1, columnspan=2, pady=2)
            entry = ctk.CTkEntry(self.tab1, font=_font(24))
            entry.grid(row=11, column=1, columnspan=1, pady=2)
            done_var = tk.IntVar()
            button = ctk.CTkButton(self.tab1, text="Run", command=lambda: done_var.set(1))
            button.grid(row=11, column=2, columnspan=1, pady=2)
            button.wait_variable(done_var)
            try:
                threshold = int(entry.get())
            except ValueError:
                pass
            label.destroy()
            entry.destroy()
            button.destroy()

        if self.plt_canvas is not None:
            self.plt_canvas.get_tk_widget().destroy()
            self.plt_canvas = None
        return threshold

    def checkerboard(self) -> None:
        if self.data_dir is None or self.left_video is None or self.right_video is None:
            self.show_error("Select directory and both videos first.")
            return
        try:
            fps = int(self.fps_entry.get())
            first = int(self.first_grid_second_entry.get()) * fps
            last = int(self.last_grid_second_entry.get()) * fps
        except ValueError:
            self.show_error("Enter integer FPS and seconds.")
            return
        self.waiting(self.tab1, "Extracting checkerboard frames…")
        extract_checkerboard_frames(
            left_video=self.left_video,
            right_video=self.right_video,
            start_frame=first,
            end_frame=last,
            out_dir=self.data_dir,
        )
        self.finished()

    def calibrate(self) -> None:
        if self.data_dir is None:
            self.show_error("Select a directory first.")
            return
        try:
            rows = int(self.rows_entry.get())
            cols = int(self.columns_entry.get())
            scaling = float(self.scaling_entry.get())
        except ValueError:
            self.show_error("Rows / columns must be integers; scaling must be a number.")
            return
        self.waiting(self.tab1, "Calibrating cameras…")
        run_calibration(
            cam_config_dir=self.data_dir,
            rows=rows,
            cols=cols,
            world_scaling=scaling,
        )
        self.finished()
        self._display_rmse()

    def _display_rmse(self) -> None:
        rmse_path = (self.data_dir or Path()) / "rmse.json"
        if not rmse_path.exists():
            return
        with rmse_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if self.rmse_label is not None:
            self.rmse_label.destroy()
        self.rmse_label = ctk.CTkLabel(
            self.tab1,
            text=(
                f"Left camera RMSE:  {float(data['camera1_rmse']):.3f}\n"
                f"Right camera RMSE: {float(data['camera2_rmse']):.3f}"
            ),
            font=_font(),
        )
        self.rmse_label.grid(row=7, column=2, pady=5)

    # ---------- Tab 2 handlers ---------- #

    def trim(self) -> None:
        if self.data_dir is None or self.left_video is None or self.right_video is None:
            self.show_error("Select directory and both videos first.")
            return
        self.waiting(self.tab2, "Trimming samples…")
        samples_dir = self.data_dir / "samples"
        samples_dir.mkdir(exist_ok=True)

        text = self.times_textbox.get("1.0", tk.END)
        for line in text.splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 2:
                continue
            label, length = parts
            mm_ss = label.replace("m", ":").replace("s", "")
            mm, ss = mm_ss.split(":")
            start_sec = int(mm) * 60 + int(ss)
            length_sec = float(length)
            ffmpeg.trim(
                self.left_video,
                samples_dir / f"left_{mm}m{ss}s.mp4",
                start_sec=start_sec,
                length_sec=length_sec,
            )
            ffmpeg.trim(
                self.right_video,
                samples_dir / f"right_{mm}m{ss}s.mp4",
                start_sec=start_sec,
                length_sec=length_sec,
            )
        self.finished()

    def open_block_video(self) -> None:
        if self.data_dir is None:
            self.show_error("Select a directory first.")
            return
        samples_dir = self.data_dir / "samples"
        if not samples_dir.is_dir():
            self.show_error(f"No samples directory at {samples_dir}.")
            return
        videos = sorted(p for p in samples_dir.iterdir() if p.is_file())
        left = next((p for p in videos if p.name.startswith("left")), None)
        right = next((p for p in videos if p.name.startswith("right")), None)
        if left is None or right is None:
            self.show_error("Need both a 'left_*' and 'right_*' sample to draw block boxes.")
            return
        self._show_first_frame(left, side="left")
        self._show_first_frame(right, side="right")

    def _show_first_frame(self, video: Path, *, side: str) -> None:
        cap = cv2.VideoCapture(str(video))
        ok, frame = cap.read()
        cap.release()
        if not ok:
            self.show_error(f"Could not read {video}")
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        fig = plt.figure()
        plt.imshow(frame_rgb)
        canvas = FigureCanvasTkAgg(fig, master=self.tab2)
        col = 1 if side == "left" else 3
        canvas.get_tk_widget().grid(row=2, column=col, rowspan=7, columnspan=2, pady=5, padx=(40, 0))
        if side == "left":
            self.left_image_fig = fig
            fig.canvas.mpl_connect("button_press_event", self._left_image_click)
        else:
            self.right_image_fig = fig
            fig.canvas.mpl_connect("button_press_event", self._right_image_click)

    def _left_image_click(self, event: object) -> None:
        x, y = round(event.xdata), round(event.ydata)  # type: ignore[attr-defined]
        plt.plot(event.xdata, event.ydata, ".", color="black", markersize=15)  # type: ignore[attr-defined]
        if self.left_image_fig is not None:
            self.left_image_fig.canvas.draw()
        if event.button == 1:  # type: ignore[attr-defined]
            self.left_img_pts[0:2] = [x, y]
            self.left_pt1_label.configure(text=f"Top Left: ({x}, {y})")
        elif event.button == 3:  # type: ignore[attr-defined]
            self.left_img_pts[2:4] = [x, y]
            self.left_pt2_label.configure(text=f"Bottom Right: ({x}, {y})")

    def _right_image_click(self, event: object) -> None:
        x, y = round(event.xdata), round(event.ydata)  # type: ignore[attr-defined]
        plt.plot(event.xdata, event.ydata, ".", color="black", markersize=15)  # type: ignore[attr-defined]
        if self.right_image_fig is not None:
            self.right_image_fig.canvas.draw()
        if event.button == 1:  # type: ignore[attr-defined]
            self.right_img_pts[0:2] = [x, y]
            self.right_pt1_label.configure(text=f"Top Left: ({x}, {y})")
        elif event.button == 3:  # type: ignore[attr-defined]
            self.right_img_pts[2:4] = [x, y]
            self.right_pt2_label.configure(text=f"Bottom Right: ({x}, {y})")

    def run_block(self) -> None:
        if not all(self.left_img_pts) or not all(self.right_img_pts):
            self.show_error("Click two points on each image first.")
            return
        if self.data_dir is None:
            return
        self.waiting(self.tab2, "Blocking videos…")
        samples_dir = self.data_dir / "samples"
        original_dir = samples_dir / "original"
        original_dir.mkdir(exist_ok=True)

        text = self.times_textbox.get("1.0", tk.END)
        labels = [line.split(",")[0].strip() for line in text.splitlines() if line.strip()]
        for label in labels:
            for prefix, pts in (("left", self.left_img_pts), ("right", self.right_img_pts)):
                self._apply_block(samples_dir, original_dir, f"{prefix}_{label}.mp4", pts)
        self.finished()

    def _apply_block(self, samples_dir: Path, original_dir: Path, name: str, pts: list[int]) -> None:
        sample = samples_dir / name
        if not sample.exists():
            return
        backup = original_dir / name
        if not backup.exists():
            shutil.move(str(sample), str(backup))
        cap = cv2.VideoCapture(str(backup))
        if not cap.isOpened():
            return
        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(sample), fourcc, fps, (width, height))
            try:
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break
                    frame[pts[1]:pts[3], pts[0]:pts[2]] = 0
                    out.write(frame)
            finally:
                out.release()
        finally:
            cap.release()

    # ---------- Tab 3 handlers ---------- #

    def open_json(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.json_run = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            self.show_error(f"Could not read JSON: {e}")

    def track(self) -> None:
        if self.data_dir is None:
            self.show_error("Select a directory first.")
            return
        self.waiting(self.tab3, "Running tracker… (this may take a while)")

        if self.json_run:
            exp_name = self.json_run["experiment_name"]
            video_dir = Path(self.json_run.get("source_data_directory") or self.data_dir)
            times = self.json_run["times"]
            cfg = self._cfg_with_cotracker_version()
            samples = self._build_samples(video_dir, times, exp_name)
            run_pipeline(
                cfg=cfg,
                samples=samples,
                tracker="spiga" if self.tracker_var.get() == "Spiga" else "sapiens",
                cam_config_dir=video_dir,
                save_dir=video_dir,
            )
        else:
            exp_name = self.experiment_entry.get().strip()
            text = self.run_textbox.get("1.0", tk.END)
            times = [line.strip() for line in text.splitlines() if line.strip()]
            cfg = self._cfg_with_cotracker_version()
            samples = self._build_samples(self.data_dir, times, exp_name)
            run_pipeline(
                cfg=cfg,
                samples=samples,
                tracker="spiga" if self.tracker_var.get() == "Spiga" else "sapiens",
                cam_config_dir=self.data_dir,
                save_dir=self.data_dir,
            )
        self.finished()

    def _build_samples(self, video_dir: Path, times: list[str], exp_name: str) -> list[SampleSpec]:
        samples_dir = video_dir / "samples"
        return [
            SampleSpec(
                name=f"{exp_name}_{t}",
                left_video=samples_dir / f"left_{t}.mp4",
                right_video=samples_dir / f"right_{t}.mp4",
            )
            for t in times
        ]

    # ---------- helpers ---------- #

    def waiting(self, tab: ctk.CTkFrame, message: str = "Running…") -> None:
        if self.running_message is not None:
            self.running_message.destroy()
        self.running_message = ctk.CTkLabel(
            tab, text=message, font=_font(30), text_color="DodgerBlue4"
        )
        self.running_message.grid(row=14, column=1, pady=(40, 0))
        self.tabview.update()

    def finished(self) -> None:
        if self.running_message is None:
            return
        self.running_message.configure(text="Finished.")
        self.tabview.update()
        time.sleep(1)
        self.running_message.grid_forget()
        self.running_message = None

    def _cfg_for_dir(self) -> Config:
        if self.data_dir is None:
            return self._cfg
        from cotracker_lips.config import with_overrides

        return with_overrides(self._cfg, work_dir=self.data_dir)

    def _cfg_with_cotracker_version(self) -> Config:
        from cotracker_lips.config import with_overrides

        version = 3 if self.cotracker_var.get() == "Cotracker3" else 2
        cfg = self._cfg_for_dir()
        return with_overrides(cfg, cotracker_version=version)


def launch_main_gui(cfg: Config | None = None) -> None:
    """Entry point used by the CLI's ``gui`` subcommand."""
    if cfg is None:
        cfg = load_config()
    cfg.ensure_dirs()
    app = App(cfg)
    app.mainloop()


# Keep os imported (used by Path operations indirectly).
_ = os
