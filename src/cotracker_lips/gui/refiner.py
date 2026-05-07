"""Manual tracking refiner GUI.

Lets the user click on a frame in an existing tracking result to re-seed
upper/lower lip points and re-run CoTracker on the trailing portion of the
clip. The result is spliced into the original ``cotracker_pts.csv`` and
re-triangulated.
"""

from __future__ import annotations

import json
import logging
import shutil
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
import cv2
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog

from cotracker_lips.calibration.triangulate import rerun_triangulate
from cotracker_lips.config import Config, load_config, with_overrides
from cotracker_lips.io import ffmpeg
from cotracker_lips.io.csv_schema import NUM_LIP_PAIRS
from cotracker_lips.io.video import probe
from cotracker_lips.pipeline import Pipeline, SampleSpec

logger = logging.getLogger(__name__)


class RefinerApp(ctk.CTk):
    def __init__(self, cfg: Config) -> None:
        super().__init__()
        self._cfg = cfg
        self.data_dir: Path | None = None
        self.selected_frame: int | None = None
        self.upper_left_pt: list[int] | None = None
        self.lower_left_pt: list[int] | None = None
        self.upper_right_pt: list[int] | None = None
        self.lower_right_pt: list[int] | None = None
        self.left_fig = None
        self.right_fig = None
        self.left_canvas: FigureCanvasTkAgg | None = None
        self.right_canvas: FigureCanvasTkAgg | None = None
        self.plot_canvas: FigureCanvasTkAgg | None = None

        self.title("Tracking Refiner")
        self.geometry("2000x1400")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack()
        self.tab1 = self.tabview.add("Refine")
        self.tab1.rowconfigure(0, weight=1)
        self.tab1.columnconfigure(1, minsize=600, weight=1)
        for button in self.tabview._segmented_button._buttons_dict.values():
            button.configure(width=100, height=50, font=(ctk.CTkFont, 16))

        self._build_controls()

    def _build_controls(self) -> None:
        frm = ctk.CTkFrame(self.tab1, fg_color="burlywood3")
        frm.grid(row=0, column=0, rowspan=12, sticky="ns")

        ctk.CTkButton(frm, text="Select Tracking Samples Directory",
                      command=self.select_dir, font=(ctk.CTkFont, 16)).grid(row=0, column=0, pady=(5, 0))
        self.selected_dir_label = ctk.CTkLabel(frm, text="Selected Dir: ", font=(ctk.CTkFont, 16))
        self.selected_dir_label.grid(row=1, column=0, pady=(5, 0))
        ctk.CTkButton(frm, text="Display", font=(ctk.CTkFont, 16),
                      command=self.display_plot).grid(row=2, column=0, pady=10)

        self.frame_label = ctk.CTkLabel(frm, text="Selected Frame: ", font=(ctk.CTkFont, 16))
        self.frame_label.grid(row=3, column=0, pady=(10, 0))
        self.upper_left_label = ctk.CTkLabel(frm, text="Upper Left: ", font=(ctk.CTkFont, 16))
        self.upper_left_label.grid(row=4, column=0, pady=(5, 0))
        self.lower_left_label = ctk.CTkLabel(frm, text="Lower Left: ", font=(ctk.CTkFont, 16))
        self.lower_left_label.grid(row=5, column=0, pady=(5, 0))
        self.upper_right_label = ctk.CTkLabel(frm, text="Upper Right: ", font=(ctk.CTkFont, 16))
        self.upper_right_label.grid(row=6, column=0, pady=(5, 0))
        self.lower_right_label = ctk.CTkLabel(frm, text="Lower Right: ", font=(ctk.CTkFont, 16))
        self.lower_right_label.grid(row=7, column=0, pady=(5, 0))

        ctk.CTkButton(frm, text="Rerun Tracker", font=(ctk.CTkFont, 16),
                      command=self.rerun).grid(row=8, column=0, pady=15)

    # ---------- handlers ---------- #

    def select_dir(self) -> None:
        path = filedialog.askdirectory()
        if not path:
            return
        self.data_dir = Path(path).resolve()
        self.selected_dir_label.configure(text=f"Selected Dir: {self.data_dir.name}")

        for side in ("vid0", "vid1"):
            images = self.data_dir / side / "images"
            video = self.data_dir / side / f"{0 if side == 'vid0' else 1}_queries_notrace.mp4"
            if not images.is_dir() and video.is_file():
                images.mkdir(parents=True)
                ffmpeg.run(
                    ["-i", str(video), str(images / "%04d.png")],
                    description=f"extract refiner frames {side}",
                )

    def display_plot(self) -> None:
        if self.data_dir is None:
            return
        dist_path = self.data_dir / "cotracker_3dist.txt"
        if not dist_path.exists():
            tk.messagebox.showerror("Error", f"No distance file at {dist_path}")
            return
        distances = np.loadtxt(dist_path)
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.plot(distances)
        ax.set_title("Upper-lower lip 3D distance")
        ax.set_xlabel("frames")
        ax.set_ylabel("3D Euclidean distance (mm)")
        if self.plot_canvas is not None:
            self.plot_canvas.get_tk_widget().destroy()
        self.plot_canvas = FigureCanvasTkAgg(fig, master=self.tab1)
        self.plot_canvas.get_tk_widget().grid(row=0, column=1, columnspan=2, rowspan=5, pady=(5, 0), sticky="nsew")
        fig.canvas.mpl_connect("button_press_event", self._plot_click)

    def _plot_click(self, event: object) -> None:
        try:
            self.selected_frame = round(event.xdata)  # type: ignore[attr-defined]
        except (TypeError, ValueError):
            return
        self.frame_label.configure(text=f"Selected Frame: {self.selected_frame}")
        self._show_frame_images(self.selected_frame)

    def _show_frame_images(self, frame_idx: int) -> None:
        if self.data_dir is None:
            return
        name = f"{frame_idx:04d}.png"
        for fig_attr, canvas_attr, side, click in (
            ("left_fig", "left_canvas", "vid0", self._left_click),
            ("right_fig", "right_canvas", "vid1", self._right_click),
        ):
            old_canvas = getattr(self, canvas_attr)
            old_fig = getattr(self, fig_attr)
            if old_canvas is not None:
                old_canvas.get_tk_widget().destroy()
            if old_fig is not None:
                plt.close(old_fig)
            fig = plt.figure()
            img_path = self.data_dir / side / "images" / name
            if not img_path.exists():
                tk.messagebox.showerror("Error", f"Frame image missing: {img_path}")
                return
            plt.imshow(mpimg.imread(img_path))
            plt.xlim(528, 176)
            plt.ylim(384, 128)
            canvas = FigureCanvasTkAgg(fig, master=self.tab1)
            canvas.get_tk_widget().grid(row=5, column=1 if side == "vid0" else 2, rowspan=7)
            fig.canvas.mpl_connect("button_press_event", click)
            setattr(self, fig_attr, fig)
            setattr(self, canvas_attr, canvas)

    def _left_click(self, event: object) -> None:
        x, y = round(event.xdata), round(event.ydata)  # type: ignore[attr-defined]
        plt.plot(event.xdata, event.ydata, ".", color="y", markersize=15)  # type: ignore[attr-defined]
        if self.left_fig is not None:
            self.left_fig.canvas.draw()
        if event.button == 1:  # type: ignore[attr-defined]
            self.upper_left_pt = [x, y]
            self.upper_left_label.configure(text=f"Upper Left: ({x}, {y})")
        elif event.button == 3:  # type: ignore[attr-defined]
            self.lower_left_pt = [x, y]
            self.lower_left_label.configure(text=f"Lower Left: ({x}, {y})")

    def _right_click(self, event: object) -> None:
        x, y = round(event.xdata), round(event.ydata)  # type: ignore[attr-defined]
        plt.plot(event.xdata, event.ydata, ".", color="y", markersize=15)  # type: ignore[attr-defined]
        if self.right_fig is not None:
            self.right_fig.canvas.draw()
        if event.button == 1:  # type: ignore[attr-defined]
            self.upper_right_pt = [x, y]
            self.upper_right_label.configure(text=f"Upper Right: ({x}, {y})")
        elif event.button == 3:  # type: ignore[attr-defined]
            self.lower_right_pt = [x, y]
            self.lower_right_label.configure(text=f"Lower Right: ({x}, {y})")

    def rerun(self) -> None:
        if not (self.upper_left_pt and self.lower_left_pt
                and self.upper_right_pt and self.lower_right_pt):
            tk.messagebox.showerror("Error", "Click upper + lower lip in both frames first.")
            return
        if self.data_dir is None or self.selected_frame is None:
            return

        main_dir = self.data_dir.parent.parent
        time_str = self.data_dir.name.split("_")[1]
        left_full = main_dir / "samples" / f"left_{time_str}.mp4"
        right_full = main_dir / "samples" / f"right_{time_str}.mp4"
        info = probe(left_full)
        fps = info.fps
        start_sec = round(self.selected_frame / fps, 3)

        refine_dir = self.data_dir / f"refine_frame{self.selected_frame}"
        if refine_dir.exists():
            shutil.rmtree(refine_dir)
        refine_dir.mkdir()

        left_clip = refine_dir / "left_video.mp4"
        right_clip = refine_dir / "right_video.mp4"
        ffmpeg.shift(left_full, left_clip, start_sec=start_sec)
        ffmpeg.shift(right_full, right_clip, start_sec=start_sec)

        # Save user-selected points for downstream tooling.
        with (refine_dir / "rerun_pts.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "upper_left": self.upper_left_pt,
                    "lower_left": self.lower_left_pt,
                    "upper_right": self.upper_right_pt,
                    "lower_right": self.lower_right_pt,
                },
                f,
                indent=2,
            )

        cfg = with_overrides(self._cfg, work_dir=refine_dir)
        pipeline = Pipeline(
            cfg,
            tracker_kind="spiga",
            cam_config_dir=main_dir,
            save_dir=refine_dir,
        )
        sample_name = f"rerun_{start_sec}_GlLp"
        pipeline.run(SampleSpec(name=sample_name, left_video=left_clip, right_video=right_clip))

        # Splice the rerun results into the original CSV from `selected_frame` onward.
        original_csv = self.data_dir / "cotracker_pts.csv"
        rerun_csv = refine_dir / "cotracker_out" / sample_name / "cotracker_pts.csv"
        if not (original_csv.exists() and rerun_csv.exists()):
            tk.messagebox.showerror(
                "Error",
                f"Could not splice rerun: {original_csv}, {rerun_csv}",
            )
            return
        original = pd.read_csv(original_csv)
        rerun = pd.read_csv(rerun_csv)
        combined = original.copy()
        end = self.selected_frame + len(rerun)
        combined.iloc[self.selected_frame : end] = rerun.iloc[: end - self.selected_frame].values
        combined_dir = refine_dir / "combined"
        combined_dir.mkdir(exist_ok=True)
        combined.to_csv(combined_dir / "cotracker_pts.csv", index=False)

        rerun_triangulate(
            points_csv=combined_dir / "cotracker_pts.csv",
            cam_config_dir=main_dir,
            save_dir=combined_dir,
            image_height=info.height,
        )
        self._draw_combined(main_dir, combined_dir, time_str)

    def _draw_combined(self, main_dir: Path, combined_dir: Path, time_str: str) -> None:
        df = pd.read_csv(combined_dir / "cotracker_pts.csv")
        # The legacy CSV used un-suffixed names for the first lip pair; alias them.
        for cam in (1, 2):
            for kind in ("upper", "lower"):
                df.rename(
                    columns={
                        f"f{cam}_{kind}_x": f"f{cam}_{kind}_x1",
                        f"f{cam}_{kind}_y": f"f{cam}_{kind}_y1",
                    },
                    inplace=True,
                )

        for cam, suffix in ((1, "0"), (2, "1")):
            video_in = main_dir / "samples" / f"left_{time_str}.mp4"
            video_out = combined_dir / f"combined_vid{suffix}.mp4"
            cap = cv2.VideoCapture(str(video_in))
            if not cap.isOpened():
                continue
            try:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                fps = float(cap.get(cv2.CAP_PROP_FPS)) or 10.0
                out = cv2.VideoWriter(str(video_out), fourcc, fps, (width, height))
                try:
                    i = 0
                    while True:
                        ok, frame = cap.read()
                        if not ok:
                            break
                        for z in range(1, NUM_LIP_PAIRS + 1):
                            try:
                                cv2.circle(
                                    frame,
                                    (round(df[f"f{cam}_lower_x{z}"][i]),
                                     round(df[f"f{cam}_lower_y{z}"][i])),
                                    radius=2, color=(233, 180, 86), thickness=2,
                                )
                                cv2.circle(
                                    frame,
                                    (round(df[f"f{cam}_upper_x{z}"][i]),
                                     round(df[f"f{cam}_upper_y{z}"][i])),
                                    radius=2, color=(233, 180, 86), thickness=2,
                                )
                            except (KeyError, IndexError):
                                pass
                        out.write(frame)
                        i += 1
                finally:
                    out.release()
            finally:
                cap.release()


def launch_refiner_gui(cfg: Config | None = None) -> None:
    if cfg is None:
        cfg = load_config()
    cfg.ensure_dirs()
    RefinerApp(cfg).mainloop()
