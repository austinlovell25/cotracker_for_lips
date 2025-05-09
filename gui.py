import shutil

import customtkinter as ctk
import json
import os
import subprocess
import tkinter as tk

import cv2
import matplotlib.pyplot as plt
import numpy as np
import time

from customtkinter import filedialog
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from audio import compute_pcm, find_sync_with_threshold, create_videos
from grid_frames import extract_checkerboard
from calibration import run_calibration
from run_tests import run_tracking


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.data_dir = None
        self.left_video = None
        self.right_video = None
        self.json_run = None
        self.running_message = None
        self.plt_canvas = None
        self.rmse_label = None
        self.left_img_pts = [0, 0, 0, 0]
        self.right_img_pts = [0, 0, 0, 0]
        self.left_image_fig = None
        self.right_image_fig = None


        self.title("CoTracker for lips")
        self.geometry("1200x1200")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)

        # Create Tab View
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Create Tabs
        self.tab1 = self.tabview.add("Calibrate Cameras")
        self.tab2 = self.tabview.add("Create Samples")
        self.tab3 = self.tabview.add("Run Tracker")

        # Make tab buttons and font larger
        for button in self.tabview._segmented_button._buttons_dict.values():
            button.configure(width=100, height=50, font=(ctk.CTkFont, 16))


        # Tab 1 Column 1
        self.sync_label = ctk.CTkLabel(self.tab1,
                                       text="1. Choose directory with videos, select left and right video, enter FPS, end of range to search for the board clap, and run.",
                                       fg_color="transparent", font=(ctk.CTkFont, 20), wraplength=300)
        self.sync_label.grid(row=0, column=0, pady=(20, 20), padx=40, sticky="nw")

        self.select_dir_button = ctk.CTkButton(self.tab1, text='Select Directory', command=self.select_dir,
                                               font=(ctk.CTkFont, 16))
        self.select_dir_button.grid(row=1, column=0, pady=(5, 0))

        self.selected_dir_label = ctk.CTkLabel(self.tab1, text="Selected Dir: ", font=(ctk.CTkFont, 16))
        self.selected_dir_label.grid(row=2, column=0, pady=(0, 2))

        self.select_left_vid_button = ctk.CTkButton(self.tab1, text='Select Left Video', command=self.select_left_video,
                                                    font=(ctk.CTkFont, 16))
        self.select_left_vid_button.grid(row=3, column=0, pady=(5, 0))

        self.selected_left_vid_label = ctk.CTkLabel(self.tab1, text=f"Selected Video: ", font=(ctk.CTkFont, 16))
        self.selected_left_vid_label.grid(row=4, column=0, pady=(0, 2))

        self.select_right_vid_button = ctk.CTkButton(self.tab1, text='Select Right Video',
                                                     command=self.select_right_video, font=(ctk.CTkFont, 16))
        self.select_right_vid_button.grid(row=5, column=0, pady=(5, 0))

        self.selected_right_vid_label = ctk.CTkLabel(self.tab1, text="Selected Video: ", font=(ctk.CTkFont, 16))
        self.selected_right_vid_label.grid(row=6, column=0, pady=(0, 2))

        self.label = ctk.CTkLabel(self.tab1, text="Enter FPS of Videos", fg_color="transparent", font=(ctk.CTkFont, 16))
        self.label.grid(row=7, column=0, pady=5)

        self.fps_entry = ctk.CTkEntry(self.tab1, placeholder_text='0', font=(ctk.CTkFont, 16))
        self.fps_entry.grid(row=8, column=0, pady=5)

        self.clapperboard_label = ctk.CTkLabel(self.tab1,
                                               text="Enter the number of seconds after the start of the video that the program should end the search for the clapperboard",
                                               font=(ctk.CTkFont, 16), wraplength=300)
        self.clapperboard_label.grid(row=9, column=0, pady=10)

        self.clapperboard_entry = ctk.CTkEntry(self.tab1, placeholder_text='0', font=(ctk.CTkFont, 16))
        self.clapperboard_entry.grid(row=10, column=0, pady=10)

        self.sync_button = ctk.CTkButton(self.tab1, text="Sync Videos", command=self.sync_videos,
                                         font=(ctk.CTkFont, 16))
        self.sync_button.grid(row=11, column=0, pady=5)


        # Tab 1 Column 2
        self.grid_label = ctk.CTkLabel(self.tab1,
                                       text="2. Enter the first second and last second that the checkerboard fully appears on in the videos.",
                                       fg_color="transparent", font=(ctk.CTkFont, 20), wraplength=300)
        self.grid_label.grid(row=0, column=1, pady=(20, 20), padx=40)

        self.first_second_label = ctk.CTkLabel(self.tab1, text="Enter First Second", fg_color="transparent",
                                              font=(ctk.CTkFont, 16))
        self.first_second_label.grid(row=1, column=1, pady=5)

        self.first_grid_second_entry = ctk.CTkEntry(self.tab1, placeholder_text="0", font=(ctk.CTkFont, 16))
        self.first_grid_second_entry.grid(row=2, column=1, pady=5)

        self.last_second_label = ctk.CTkLabel(self.tab1, text="Enter Last Second", fg_color="transparent",
                                             font=(ctk.CTkFont, 16))
        self.last_second_label.grid(row=3, column=1, pady=5)

        self.last_grid_second_entry = ctk.CTkEntry(self.tab1, placeholder_text="100", font=(ctk.CTkFont, 16))
        self.last_grid_second_entry.grid(row=4, column=1, pady=5)

        self.grid_button = ctk.CTkButton(self.tab1, text="Extract Checkerboard Frames", command=self.checkerboard,
                                         font=(ctk.CTkFont, 16))
        self.grid_button.grid(row=6, column=1, pady=5)


        # Tab 1 Column 3
        self.grid_label = ctk.CTkLabel(self.tab1,
                                       text="3. Enter number of rows and columns on the checkerboard and the length of the squares in mm.",
                                       fg_color="transparent", font=(ctk.CTkFont, 20), wraplength=300)
        self.grid_label.grid(row=0, column=2, pady=(20, 20), padx=40)

        self.rows_entry = ctk.CTkEntry(self.tab1, placeholder_text="rows", font=(ctk.CTkFont, 16))
        self.rows_entry.grid(row=1, column=2, pady=5)

        self.columns_entry = ctk.CTkEntry(self.tab1, placeholder_text="columns", font=(ctk.CTkFont, 16))
        self.columns_entry.grid(row=2, column=2, pady=5)

        self.scaling_entry = ctk.CTkEntry(self.tab1, placeholder_text="length", font=(ctk.CTkFont, 16))
        self.scaling_entry.grid(row=3, column=2, pady=5)

        self.calib_button = ctk.CTkButton(self.tab1, text="Calibrate Cameras", command=self.calibrate,
                                          font=(ctk.CTkFont, 16))
        self.calib_button.grid(row=6, column=2, pady=5)


        # Tab 2 Column 1
        self.times_label = ctk.CTkLabel(self.tab2,
                                        text="4. Create samples. For each sample, enter the sample start time and sample length in seconds in the format (1m35s, 2) (for a 2 second long snippet "
                                             "starting at 1 min 35 seconds in the video) separating entries by line.",
                                        font=(ctk.CTkFont, 20), wraplength=300)
        self.times_label.grid(row=0, column=0, pady=(20, 20), rowspan=2, sticky="nw", padx=(40, 0))

        self.times_textbox = ctk.CTkTextbox(self.tab2)
        self.times_textbox.grid(row=2, column=0, rowspan=7, sticky="nsew", padx=(40, 0))

        self.trim_button = ctk.CTkButton(self.tab2, text="Trim Samples", command=self.trim, font=(ctk.CTkFont, 16))
        self.trim_button.grid(row=10, column=0, pady=5, padx=(40, 0))


        # Tab 2 Column 2
        self.block_label = ctk.CTkLabel(self.tab2, text="(Optional) Select coordinates of video to erase.", font=(ctk.CTkFont, 20), wraplength=300)
        self.block_label.grid(row=0, column=1, pady=(20, 20), padx=(40, 0))

        self.block_open_button = ctk.CTkButton(self.tab2, text="Draw Black Box", command=self.open_block_video, font=(ctk.CTkFont, 16))
        self.block_open_button.grid(row=1, column=1, pady=5, padx=(40, 0))

        self.block_info_label = ctk.CTkLabel(self.tab2, text="Choose two points to erase a rectangle from the sample videos. "
                                                             "Left click to select the top left point of the rectangle. "
                                                             "Right click to select the bottom right point of the rectangle. ",
                                             font=(ctk.CTkFont, 16), wraplength=300)
        self.block_info_label.grid(row=10, column=1, pady=5, padx=(40, 0))

        self.left_pt1_label = ctk.CTkLabel(self.tab2, text="Top Left Point: ", font=(ctk.CTkFont, 16))
        self.left_pt1_label.grid(row=11, column=1, pady=5, padx=(40, 0))

        self.left_pt2_label = ctk.CTkLabel(self.tab2, text="Bottom Right Point: ", font=(ctk.CTkFont, 16))
        self.left_pt2_label.grid(row=12, column=1, pady=5, padx=(40, 0))

        self.run_block_button = ctk.CTkButton(self.tab2, text="Block Selection", command=self.run_block,
                                               font=(ctk.CTkFont, 16))
        self.run_block_button.grid(row=13, column=1, pady=5, padx=(40, 0))


        # Tab 2 Column 3
        self.right_pt1_label = ctk.CTkLabel(self.tab2, text="Top Left Point: ", font=(ctk.CTkFont, 16))
        self.right_pt1_label.grid(row=11, column=3, pady=5, padx=(40, 0))

        self.right_pt2_label = ctk.CTkLabel(self.tab2, text="Bottom Right Point: ", font=(ctk.CTkFont, 16))
        self.right_pt2_label.grid(row=12, column=3, pady=5, padx=(40, 0))


        # Tab 3 Column 1
        self.experiment_title_label = ctk.CTkLabel(self.tab3,
                                                   text="5. Enter the experiment details. Experiment name and sample start times in line-separated XmXs format (ex. 1m35s) required\nOr, upload experiment from JSON file",
                                                   font=(ctk.CTkFont, 20), wraplength=300)
        self.experiment_title_label.grid(row=0, column=1, pady=(20, 20), sticky="nw", padx=(40, 0))

        self.json_button = ctk.CTkButton(self.tab3, text="Upload JSON", command=self.open_json, font=(ctk.CTkFont, 16))
        self.json_button.grid(row=1, column=1, pady=5, padx=(40, 0))

        self.experiment_name_label = ctk.CTkLabel(self.tab3, text="Enter Experiment Name", fg_color="transparent",
                                                  font=(ctk.CTkFont, 20))
        self.experiment_name_label.grid(row=2, column=1, pady=(2, 0), padx=(40, 0))

        self.experiment_entry = ctk.CTkEntry(self.tab3, font=(ctk.CTkFont, 16))
        self.experiment_entry.grid(row=3, column=1, pady=5, padx=(40, 0))

        self.run_textbox = ctk.CTkTextbox(self.tab3)
        self.run_textbox.grid(row=4, column=1, rowspan=7, sticky="nsew", padx=(40, 0))

        self.run_button = ctk.CTkButton(self.tab3, text="Run Tracker", command=self.track, font=(ctk.CTkFont, 16))
        self.run_button.grid(row=12, column=1, pady=10, padx=(40, 0))


    def on_enter(self, event):
        self.tab2.configure(cursor="hand2")


    def on_leave(self, event):
        self.tab2.configure(cursor="")


    def run_block(self):
        if not (self.left_img_pts[0] and self.left_img_pts[2] and self.right_img_pts[0] and self.right_img_pts[2]):
            tk.messagebox.showerror("Error", "Please select two points for the rectangle.")
        else:
            self.waiting(self.tab2, "Blocking parts of videos...")
            os.makedirs(f"{self.data_dir}/samples/original", exist_ok=True)
            videos = [f for f in os.listdir(f"{self.data_dir}/samples") if os.path.isfile(os.path.join(f"{self.data_dir}/samples", f))]
            for video in videos:
                if not os.path.exists(f"{self.data_dir}/samples/original{video}"):
                    shutil.move(f"{self.data_dir}/samples/{video}", f"{self.data_dir}/samples/original/{video}")
                cap = cv2.VideoCapture(f"{self.data_dir}/samples/original/{video}")
                output_path = f"{self.data_dir}/samples/{video}"

                # Get video properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')

                # Create VideoWriter object
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                while True:
                    success, frame = cap.read()
                    if not success:
                        break
                    if video.startswith("left"):
                        frame[self.left_img_pts[1]:self.left_img_pts[3], self.left_img_pts[0]:self.left_img_pts[2]] = 0
                    elif video.startswith("right"):
                        frame[self.right_img_pts[1]:self.right_img_pts[3], self.right_img_pts[0]:self.right_img_pts[2]] = 0
                    out.write(frame)

                cap.release()
                out.release()
            self.finished()


    def left_image_click(self, event):
        x_select = round(event.xdata)
        y_select = round(event.ydata)
        plt.plot(event.xdata, event.ydata, '.', color="y", markersize=15)
        self.left_image_fig.canvas.draw()
        # Left Click
        if event.button == 1:
            self.left_img_pts[0:2] = [x_select, y_select]
            self.left_pt1_label.configure(text=f"Top Left Point: ({x_select}, {y_select})")
        # Right Click
        elif event.button == 3:
            self.left_img_pts[2:4] = [x_select, y_select]
            self.left_pt2_label.configure(text=f"Bottom Right Point: ({x_select}, {y_select})")


    def right_image_click(self, event):
        x_select = round(event.xdata)
        y_select = round(event.ydata)
        plt.plot(event.xdata, event.ydata, '.', color="y", markersize=15)
        self.right_image_fig.canvas.draw()
        # Left Click
        if event.button == 1:
            self.right_img_pts[0:2] = [x_select, y_select]
            self.right_pt1_label.configure(text=f"Top Left Point: ({x_select}, {y_select})")
        # Right Click
        elif event.button == 3:
            self.right_img_pts[2:4] = [x_select, y_select]
            self.right_pt2_label.configure(text=f"Bottom Right Point: ({x_select}, {y_select})")


    def open_block_video(self):
        videos = [f for f in os.listdir(f"{self.data_dir}/samples") if
                  os.path.isfile(os.path.join(f"{self.data_dir}/samples", f))]
        left_video = next((s for s in videos if s.startswith("left")), None)
        right_video = next((s for s in videos if s.startswith("right")), None)
        left_video = os.path.join(f"{self.data_dir}/samples", left_video)
        right_video = os.path.join(f"{self.data_dir}/samples", right_video)

        left_cap = cv2.VideoCapture(left_video)
        success, left_frame = left_cap.read()
        left_cap.release()
        if not success:
            print("Reading failure")
        self.left_image_fig = plt.figure()
        left_frame = cv2.cvtColor(left_frame, cv2.COLOR_BGR2RGB)
        plt.imshow(left_frame)
        left_img_canvas = FigureCanvasTkAgg(self.left_image_fig, master=self.tab2)
        left_img_canvas.get_tk_widget().grid(row=2, column=1, rowspan=7, columnspan=2, pady=5, padx=(40, 0))
        self.left_image_fig.canvas.mpl_connect('button_press_event', self.left_image_click)
        self.left_image_fig.canvas.mpl_connect("figure_enter_event", self.on_enter)
        self.left_image_fig.canvas.mpl_connect("figure_leave_event", self.on_leave)

        right_cap = cv2.VideoCapture(right_video)
        success, right_frame = right_cap.read()
        right_cap.release()
        if not success:
            print("Reading failure")
        self.right_image_fig = plt.figure()
        right_frame = cv2.cvtColor(right_frame, cv2.COLOR_BGR2RGB)
        plt.imshow(right_frame)
        right_img_canvas = FigureCanvasTkAgg(self.right_image_fig, master=self.tab2)
        right_img_canvas.get_tk_widget().grid(row=2, column=3, rowspan=7, columnspan=2, pady=5, padx=(40, 0))
        self.right_image_fig.canvas.mpl_connect('button_press_event', self.right_image_click)
        self.right_image_fig.canvas.mpl_connect("figure_enter_event", self.on_enter)
        self.right_image_fig.canvas.mpl_connect("figure_leave_event", self.on_leave)


    def open_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.json_run = json.load(file)  # Load JSON data into a Python dictionary
                    print("JSON data loaded successfully!")
            except json.JSONDecodeError:
                print("Error: Failed to decode the JSON file.")
            except Exception as e:
                print(f"An error occurred: {e}")

    def select_dir(self):
        self.data_dir = filedialog.askdirectory()
        self.selected_dir_label.configure(text=f"Selected Dir: {os.path.basename(self.data_dir)}")

    def select_left_video(self):
        self.left_video = filedialog.askopenfilename(initialdir=self.data_dir,
                                                     filetypes=[("MP4 Files", ["*.mp4", "*.MP4"])])
        self.selected_left_vid_label.configure(text=f"Selected Video: {os.path.basename(self.left_video)}")

    def select_right_video(self):
        self.right_video = filedialog.askopenfilename(initialdir=self.data_dir,
                                                      filetypes=[("MP4 Files", ["*.mp4", "*.MP4"])])
        self.selected_right_vid_label.configure(text=f"Selected Video: {os.path.basename(self.right_video)}")

    def sync_videos(self):
        try:
            fps = int(self.fps_entry.get())
            clapperboard_time = int(self.clapperboard_entry.get())
        except Exception as e:
            self.show_error("Error: FPS and Clapperboard time entries must be valid positive integers")

        if self.data_dir is None or self.left_video is None or self.right_video is None:
            self.show_error("Error: Make selections for the directory, left video, and right video")
        else:
            self.waiting(self.tab1, "Syncing videos...")
            self.compute_sync(fps, self.left_video, self.right_video, clapperboard_time)
            self.finished()
            self.left_video = self.data_dir + "/left_sync.mp4"
            self.right_video = self.data_dir + "/right_sync.mp4"
            self.selected_left_vid_label.configure(text=f"Selected Video: {os.path.basename(self.left_video)}")
            self.selected_right_vid_label.configure(text=f"Selected Video: {os.path.basename(self.right_video)}")

    def show_error(self, error_message):
        messagebox.showerror("Error", error_message)

    def checkerboard(self):
        first_frame = int(self.first_grid_second_entry.get()) * int(self.fps_entry.get())
        last_frame = int(self.last_grid_second_entry.get()) * int(self.fps_entry.get())
        self.waiting(self.tab1, "Extracting checkerboard frames...")
        extract_checkerboard(self.left_video, self.right_video, first_frame, last_frame)
        self.finished()

    def calibrate(self):
        rows = int(self.rows_entry.get())
        columns = int(self.columns_entry.get())
        scaling = float(self.scaling_entry.get())
        self.waiting(self.tab1, "Calibrating cameras...")
        run_calibration(rows, columns, scaling, self.data_dir)
        self.finished()
        self.display_rmse()

    def display_rmse(self):
        with open(f"{self.data_dir}/rmse.json", "r") as file:
            data = json.load(file)
        camera1_rmse = float(data["camera1_rmse"])
        camera2_rmse = float(data["camera2_rmse"])

        self.rmse_label = ctk.CTkLabel(self.tab1, text=f"Left Camera RMSE: {camera1_rmse:.3f}\nRight Camera RMSE: {camera2_rmse:.3f} ", font=(ctk.CTkFont, 16))
        self.rmse_label.grid(row=7, column=2, pady=5)


    def trim(self):
        self.waiting(self.tab2, "Trimming samples...")
        times_str = self.times_textbox.get("1.0", tk.END)
        times_array = [line.split(', ') for line in times_str.split('\n')]
        samples_dir = "samples"
        path = os.path.join(self.data_dir, samples_dir)
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        for entry in times_array:
            if entry[0] == "":
                break
            time_str = entry[0].replace('m', ':').replace('s', '')
            minute, second = time_str.split(":")
            command = f"ffmpeg -nostats -loglevel 0 -ss 00:{time_str} -t 00:00:0{entry[1]} -i {self.left_video} -c:v copy -c:a copy {self.data_dir}/samples/left_{minute}m{second}s.mp4"
            subprocess.run(command, shell=True)
            command = f"ffmpeg -nostats -loglevel 0 -ss 00:{time_str} -t 00:00:0{entry[1]} -i {self.right_video} -c:v copy -c:a copy {self.data_dir}/samples/right_{minute}m{second}s.mp4"
            subprocess.run(command, shell=True)
        self.finished()

    def track(self):
        self.waiting(self.tab3, "Running tracker... This may take a while")
        if self.json_run:
            exp_name = self.json_run["experiment_name"]
            video_dir = self.json_run["source_directory"]
            times = self.json_run["times"]
            run_tracking(exp_name=exp_name, video_dir=video_dir, times=times)
        else:
            exp_name = self.experiment_entry.get()
            times_str = self.run_textbox.get("1.0", tk.END)
            times_array = times_str.split('\n')
            times_array = [item for item in times_array if item != '']
            run_tracking(exp_name=exp_name, video_dir=self.data_dir, times=times_array)
        self.finished()


    def waiting(self, tab, message="Running... Please Wait."):
        self.running_message = ctk.CTkLabel(tab, text=message, font=(ctk.CTkFont, 30), text_color="DodgerBlue4")
        col = 1
        self.running_message.grid(row=14, column=col, pady=(40, 0))
        self.tabview.update()

    def finished(self):
        self.running_message.configure(text="Finished.")
        self.tabview.update()
        time.sleep(1)
        self.running_message.grid_forget()

    def compute_sync(self, fps, left_video, right_video, range_end):
        left_pcm16_signed_integers = compute_pcm(left_video, "LEFT", range_end)
        right_pcm16_signed_integers = compute_pcm(right_video, "RIGHT", range_end)

        left_ints = np.asarray(left_pcm16_signed_integers)
        right_ints = np.asarray(right_pcm16_signed_integers)

        threshold = self.display_threshold(left_ints, right_ints, range_end)
        left_frame, right_frame = find_sync_with_threshold(fps, left_ints, right_ints, threshold)
        create_videos(fps, left_video, right_video, left_frame, right_frame)

    def display_threshold(self, left_ints, right_ints, range_end):
        fig, ax = plt.subplots(figsize=(5, 4))
        x_vals = np.linspace(0, range_end, left_ints.size)

        ax.plot(x_vals, left_ints)
        ax.plot(x_vals, right_ints)

        # Add a title and labels
        ax.set_title("Audio Plot")
        ax.set_xlabel("Seconds")
        ax.set_ylabel("Amplitude")

        # Create a canvas to display the plot in tkinter
        self.plt_canvas = FigureCanvasTkAgg(fig, master=self.tab1)
        self.plt_canvas.get_tk_widget().grid(row=12, column=1, columnspan=2, padx=10, pady=10)

        threshold = int((np.max(left_ints) + np.max(right_ints)) * (6 / 16))
        combobox_choice = ctk.StringVar()

        check_label = ctk.CTkLabel(self.tab1, text=f"Threshold selected to be y={threshold}. Is this value ok?",
                                   font=(ctk.CTkFont, 24), text_color="Red", wraplength=300)
        check_label.grid(row=11, column=1, columnspan=2, pady=2)

        combobox = ctk.CTkComboBox(self.tab1, values=["Yes", "No"], variable=combobox_choice, font=(ctk.CTkFont, 16))
        combobox.grid(row=10, column=1, columnspan=2, pady=2)

        check_label.waitvar(combobox_choice)

        check_label.destroy()
        combobox.destroy()

        if combobox_choice.get() == "No":
            threshold_label = ctk.CTkLabel(self.tab1, text=f"Enter your desired y threshold value", font=(ctk.CTkFont, 24))
            threshold_label.grid(row=10, column=1, columnspan=2, pady=2)

            threshold_entry = ctk.CTkEntry(self.tab1, font=(ctk.CTkFont, 24))
            threshold_entry.grid(row=11, column=1, columnspan=1, pady=2)

            var = tk.IntVar()
            button = ctk.CTkButton(self.tab1, text="Run", command=lambda: var.set(1))
            button.grid(row=11, column=2, columnspan=1, pady=2)

            button.wait_variable(var)
            threshold = int(threshold_entry.get())

            threshold_label.destroy()
            threshold_entry.destroy()
            button.destroy()

        self.plt_canvas.get_tk_widget().destroy()
        return threshold


if __name__ == "__main__":
    app = App()
    app.mainloop()
