import json
import shutil
import time
import customtkinter as ctk
import os
import tkinter as tk

import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import mpl_interactions
import numpy as np
import subprocess
import pandas as pd

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog

from calibration import rerun_triangulate




class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.data_dir = None
        self.plt_canvas = None
        self.left_img_canvas = None
        self.right_img_canvas = None
        self.selected_frame = None
        self.upper_left_pt = None
        self.lower_left_pt = None
        self.upper_right_pt = None
        self.lower_right_pt = None
        self.left_fig = None
        self.right_fig = None

        self.title("Tracking Refiner")
        self.geometry("2000x1400")

        # Create Tab View
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack()

        # Create Tabs
        self.tab1 = self.tabview.add("Refine")

        self.tab1.rowconfigure(0, weight=1)
        self.tab1.columnconfigure(1, minsize=600, weight=1)
        # self.tab1.columnconfigure(0, minsize=600, weight=0)

        # Make tab buttons and font larger
        for button in self.tabview._segmented_button._buttons_dict.values():
            button.configure(width=100, height=50, font=(ctk.CTkFont, 16))

        self.frm_buttons = ctk.CTkFrame(self.tab1, fg_color="burlywood3")
        self.frm_buttons.grid(row=0, column=0, rowspan=12, sticky="ns")

        self.select_dir_button = ctk.CTkButton(self.frm_buttons, text='Select Tracking Samples Directory', command=self.select_dir,
                                               font=(ctk.CTkFont, 16))
        self.select_dir_button.grid(row=0, column=0, pady=(5, 0))

        self.selected_dir_label = ctk.CTkLabel(self.frm_buttons, text="Selected Dir: ", font=(ctk.CTkFont, 16))
        self.selected_dir_label.grid(row=1, column=0, pady=(5, 0))

        self.display_btn = ctk.CTkButton(self.frm_buttons, text="Display", font=(ctk.CTkFont, 16), command=self.display_plot)
        self.display_btn.grid(row=2, column=0, pady=10)

        self.selected_frame_label = ctk.CTkLabel(self.frm_buttons, text="Selected Frame: ", font=(ctk.CTkFont, 16))
        self.selected_frame_label.grid(row=3, column=0, pady=(10, 0))

        self.left_upper_pt_label = ctk.CTkLabel(self.frm_buttons, text="Upper Left Point: ", font=(ctk.CTkFont, 16))
        self.left_upper_pt_label.grid(row=4, column=0, pady=(5, 0))

        self.left_lower_pt_label = ctk.CTkLabel(self.frm_buttons, text="Lower Left Point: ", font=(ctk.CTkFont, 16))
        self.left_lower_pt_label.grid(row=5, column=0, pady=(5, 0))

        self.right_upper_pt_label = ctk.CTkLabel(self.frm_buttons, text="Upper Right Point: ", font=(ctk.CTkFont, 16))
        self.right_upper_pt_label.grid(row=6, column=0, pady=(5, 0))

        self.right_lower_pt_label = ctk.CTkLabel(self.frm_buttons, text="Lower Right Point: ", font=(ctk.CTkFont, 16))
        self.right_lower_pt_label.grid(row=7, column=0, pady=(5, 0))

        self.rerun_button = ctk.CTkButton(self.frm_buttons, text="Rerun Tracker", font=(ctk.CTkFont, 16), command=self.rerun_cotracker)
        self.rerun_button.grid(row=8, column=0, pady=15)

    def rerun_cotracker(self):
        if not (self.upper_left_pt and self.lower_left_pt and self.upper_right_pt and self.lower_right_pt):
            tk.messagebox.showerror("Error", "Please select upper and lower lip points for both images before rerunning the tracker")
        else:
            print("rerun")
            pts_dict = {
                "upper_left": self.upper_left_pt,
                "lower_left": self.lower_left_pt,
                "upper_right": self.upper_right_pt,
                "lower_right": self.lower_right_pt,
            }
            with open("tmp/rerun_pts.json", "w") as f:
                json.dump(pts_dict, f)

            refine_dir = f"{self.data_dir}/refine_frame{self.selected_frame}"
            # Delete if exists
            if os.path.exists(refine_dir):
                shutil.rmtree(refine_dir)
            os.mkdir(refine_dir)
            main_dir = os.path.dirname(os.path.dirname(self.data_dir))
            time_string = os.path.basename(self.data_dir).split("_")[1]
            left_snippet = f"{main_dir}/samples/left_{time_string}.mp4"
            right_snippet = f"{main_dir}/samples/right_{time_string}.mp4"

            cam = cv2.VideoCapture(left_snippet)
            fps = round(cam.get(cv2.CAP_PROP_FPS))
            cam.release()
            second_start = round(self.selected_frame / fps, 3)

            command = f"ffmpeg -nostats -loglevel 0 -ss {second_start} -i {left_snippet} -c:v copy -c:a copy {refine_dir}/left_video.mp4"
            subprocess.run(command, shell=True)
            command = f"ffmpeg -nostats -loglevel 0 -ss {second_start} -i {right_snippet} -c:v copy -c:a copy {refine_dir}/right_video.mp4"
            subprocess.run(command, shell=True)

            configs = {
                "GlLp": "global_lip.json",
            }
            vid1 = f"{refine_dir}/left_video.mp4"
            vid2 = f"{refine_dir}/right_video.mp4"

            for key, value in configs.items():
                command = f"bash rerun_pipeline.sh {vid1} {vid2} rerun_{second_start}_{key} {value} {refine_dir} {main_dir} false"
                print(command)
                subprocess.run(command, shell=True)

            # Assumes GlLp
            refine_out_dir = f"{refine_dir}/cotracker_out/rerun_{second_start}_GlLp"
            combined_dir = f"{refine_dir}/combined"
            os.mkdir(combined_dir)
            self.combine_data(refine_out_dir, refine_dir, combined_dir)
            rerun_triangulate(main_dir, combined_dir)
            self.draw_pts(main_dir, combined_dir, time_string)

    def draw_pts(self, main_dir, combined_dir, time_string):
        df = pd.read_csv(f"{combined_dir}/cotracker_pts.csv")
        df.rename(columns={"f1_lower_x": "f1_lower_x1", "f1_lower_y": "f1_lower_y1", "f1_upper_x": "f1_upper_x1",
                           "f1_upper_y": "f1_upper_y1", "f2_lower_x": "f2_lower_x1", "f2_lower_y": "f2_lower_y1",
                           "f2_upper_x": "f2_upper_x1", "f2_upper_y": "f2_upper_y1"}, inplace=True)

        cap = cv2.VideoCapture(f"{main_dir}/samples/left_{time_string}.mp4")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(f'{combined_dir}/combined_vid0.mp4', fourcc, 10, (width, height))
        i = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            for z in range(1, 6):
                try:
                    cv2.circle(frame, (round(df[f"f1_lower_x{z}"][i]), round(df[f"f1_lower_y{z}"][i])), radius=2,
                               color=(233, 180, 86), thickness=2)
                    cv2.circle(frame, (round(df[f"f1_upper_x{z}"][i]), round(df[f"f1_upper_y{z}"][i])), radius=2,
                               color=(233, 180, 86), thickness=2)
                except Exception as e:
                    print(f"out of range: {i}")
            out.write(frame)
            i += 1
        cap.release()
        out.release()

        cap = cv2.VideoCapture(f"{main_dir}/samples/left_{time_string}.mp4")
        out = cv2.VideoWriter(f'{combined_dir}/combined_vid1.mp4', fourcc, 10, (width, height))
        i = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            for z in range(1, 6):
                try:
                    cv2.circle(frame, (round(df[f"f2_lower_x{z}"][i]), round(df[f"f2_lower_y{z}"][i])), radius=2,
                               color=(233, 180, 86), thickness=2)
                    cv2.circle(frame, (round(df[f"f2_upper_x{z}"][i]), round(df[f"f2_upper_y{z}"][i])), radius=2,
                               color=(233, 180, 86), thickness=2)
                except Exception as e:
                    print(f"out of range: {i}")
            out.write(frame)
            i += 1
        cap.release()
        out.release()
        cv2.destroyAllWindows()

    def combine_data(self, refine_out_dir, refine_dir, combined_dir):
        original_pts = pd.read_csv(f"{self.data_dir}/cotracker_pts.csv")
        rerun_pts = pd.read_csv(f"{refine_out_dir}/cotracker_pts.csv")
        combined_pts = original_pts.copy()
        combined_pts[self.selected_frame:] = rerun_pts
        combined_pts.to_csv(f"{combined_dir}/cotracker_pts.csv")
        combined_pts.to_csv(f"tmp/cotracker_pts.csv")


    def select_dir(self):
        self.data_dir = filedialog.askdirectory()
        self.selected_dir_label.configure(text=f"Selected Dir: {os.path.basename(self.data_dir)}")
        if not os.path.isdir(f"{self.data_dir}/vid0/images"):
            try:
                os.mkdir(f"{self.data_dir}/vid0/images")
                command = f"ffmpeg -hide_banner -nostats -loglevel 0 -i {self.data_dir}/vid0/0_queries_notrace.mp4 {self.data_dir}/vid0/images/%04d.png"
                subprocess.run(command, shell=True)

                os.mkdir(f"{self.data_dir}/vid1/images")
                command = f"ffmpeg -hide_banner -nostats -loglevel 0 -i {self.data_dir}/vid1/1_queries_notrace.mp4 {self.data_dir}/vid1/images/%04d.png"
                subprocess.run(command, shell=True)
            except FileNotFoundError:
                tk.messagebox.showerror("Error", "Please select a valid experiment directory.")

    def left_image_click(self, event):
        x_select = round(event.xdata)
        y_select = round(event.ydata)
        plt.plot(event.xdata, event.ydata, '.', color="y", markersize=15)
        self.left_fig.canvas.draw()
        # Left Click
        if event.button == 1:
            self.upper_left_pt = [x_select, y_select]
            self.left_upper_pt_label.configure(text=f"Upper Left Point: ({x_select}, {y_select})")
        # Right Click
        elif event.button == 3:
            self.lower_left_pt = [x_select, y_select]
            self.left_lower_pt_label.configure(text=f"Lower Left Point: ({x_select}, {y_select})")

    def right_image_click(self, event):
        x_select = round(event.xdata)
        y_select = round(event.ydata)
        plt.plot(event.xdata, event.ydata, '.', color="y", markersize=15)
        self.right_fig.canvas.draw()
        # Left Click
        if event.button == 1:
            self.upper_right_pt = [x_select, y_select]
            self.right_upper_pt_label.configure(text=f"Upper Right Point: ({x_select}, {y_select})")
        # Right Click
        elif event.button == 3:
            self.lower_right_pt = [x_select, y_select]
            self.right_lower_pt_label.configure(text=f"Lower Right Point: ({x_select}, {y_select})")

    def display_image(self, frame):
        if self.left_img_canvas:
            plt.close(self.left_fig)
            plt.close(self.right_fig)
            self.left_img_canvas.get_tk_widget().destroy()
            self.right_img_canvas.get_tk_widget().destroy()
        file_name = str(frame).zfill(4) + ".png"

        self.left_fig = plt.figure()
        left_image = mpimg.imread(f"{self.data_dir}/vid0/images/{file_name}")
        plt.imshow(left_image)
        plt.xlim(528, 176)
        plt.ylim(384, 128)
        self.left_img_canvas = FigureCanvasTkAgg(self.left_fig, master=self.tab1)
        self.left_img_canvas.get_tk_widget().grid(row=5, column=1, rowspan=7)
        # self.left_img_canvas.get_tk_widget().pack()
        left_cid = self.left_fig.canvas.mpl_connect('button_press_event', self.left_image_click)
        self.left_fig.canvas.mpl_connect("figure_enter_event", self.on_enter)
        self.left_fig.canvas.mpl_connect("figure_leave_event", self.on_leave)

        self.right_fig = plt.figure()
        right_image = mpimg.imread(f"{self.data_dir}/vid1/images/{file_name}")
        plt.imshow(right_image)
        plt.xlim(528, 176)
        plt.ylim(384, 128)
        self.right_img_canvas = FigureCanvasTkAgg(self.right_fig, master=self.tab1)
        self.right_img_canvas.get_tk_widget().grid(row=5, column=2, rowspan=7)
        # self.right_img_canvas.get_tk_widget().pack()
        right_cid = self.right_fig.canvas.mpl_connect('button_press_event', self.right_image_click)
        self.right_fig.canvas.mpl_connect("figure_enter_event", self.on_enter)
        self.right_fig.canvas.mpl_connect("figure_leave_event", self.on_leave)

        click_info_label = ctk.CTkLabel(self.tab1, text="Left-click to choose upper lip point. Right click to choose lower lip point.", font=(ctk.CTkFont, 16))
        click_info_label.grid(row=12, column=1, columnspan=2)


    def plot_click(self, event):
        try:
            self.selected_frame = round(event.xdata)
            self.selected_frame_label.configure(text=f"Selected Frame: {self.selected_frame}")
            self.display_image(round(event.xdata))
        except FileNotFoundError:
            print("Error: Select point on plot.")

    def on_enter(self, event):
        self.tab1.configure(cursor="hand2")

    def on_leave(self, event):
        self.tab1.configure(cursor="")

    def display_plot(self):
        fig, ax = plt.subplots(figsize=(5, 4))

        with open(f"{self.data_dir}/cotracker_3dist.txt", "r") as file:
            lines = file.readlines()
        dist_array = np.array([float(line.strip()) for line in lines])

        ax.plot(dist_array)

        # Add a title and labels
        ax.set_title("Difference between upper lip and lower lip point estimation")
        ax.set_xlabel("Frames")
        ax.set_ylabel("3D Euclidean Distance (mm)")

        # Create a canvas to display the plot in tkinter
        self.plt_canvas = FigureCanvasTkAgg(fig, master=self.tab1)
        self.plt_canvas.get_tk_widget().grid(row=0, column=1, columnspan=2, rowspan=5, pady=(5, 0), sticky="nsew")

        cid = fig.canvas.mpl_connect('button_press_event', self.plot_click)
        fig.canvas.mpl_connect("figure_enter_event", self.on_enter)
        fig.canvas.mpl_connect("figure_leave_event", self.on_leave)


if __name__ == "__main__":
    app = App()
    app.mainloop()