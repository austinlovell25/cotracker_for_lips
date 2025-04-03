import customtkinter as ctk
import json
import os
import subprocess
import tkinter as tk
import matplotlib.pyplot as plt
import numpy as np

from customtkinter import filedialog
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from audio import find_sync
from audio import compute_pcm
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
        self.is_running = False
        self.plt_canvas = None

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
        self.sync_label = ctk.CTkLabel(self.tab1, text="1. Choose directory with videos, select left and right video, enter FPS, and run.", fg_color="transparent", font=(ctk.CTkFont, 20), wraplength=300)
        self.sync_label.grid(row=0, column=0, pady=(20, 20), padx=40, sticky="nw")

        self.select_dir_button = ctk.CTkButton(self.tab1, text='Select Directory', command=self.select_dir, font=(ctk.CTkFont, 16))
        self.select_dir_button.grid(row=1, column=0, pady=(5, 0))

        self.select_left_vid_button = ctk.CTkButton(self.tab1, text='Select Left Video', command=self.select_left_video, font=(ctk.CTkFont, 16))
        self.select_left_vid_button.grid(row=2, column=0, pady=(5, 0))

        self.select_right_vid_button = ctk.CTkButton(self.tab1, text='Select Right Video', command=self.select_right_video, font=(ctk.CTkFont, 16))
        self.select_right_vid_button.grid(row=3, column=0, pady=(5, 0))

        self.label = ctk.CTkLabel(self.tab1, text="Enter FPS of Videos", fg_color="transparent", font=(ctk.CTkFont, 16))
        self.label.grid(row=4, column=0, pady=5)

        self.fps_entry = ctk.CTkEntry(self.tab1, placeholder_text='0', font=(ctk.CTkFont, 16))
        self.fps_entry.grid(row=5, column=0, pady=5)

        self.sync_button = ctk.CTkButton(self.tab1, text="Sync Videos", command=self.sync_videos,
                                         font=(ctk.CTkFont, 16))
        self.sync_button.grid(row=6, column=0, pady=5)


        # Tab 1 Column 2
        self.grid_label = ctk.CTkLabel(self.tab1, text="2. Enter the first frame and last frame that the checkerboard fully appears on in the videos.", fg_color="transparent", font=(ctk.CTkFont, 20), wraplength=300)
        self.grid_label.grid(row=0, column=1, pady=(20, 20), padx=40, sticky="nw")

        self.first_frame_label = ctk.CTkLabel(self.tab1, text="Enter First Frame", fg_color="transparent", font=(ctk.CTkFont, 16))
        self.first_frame_label.grid(row=1, column=1, pady=5)

        self.first_grid_frame_entry = ctk.CTkEntry(self.tab1, placeholder_text="0", font=(ctk.CTkFont, 16))
        self.first_grid_frame_entry.grid(row=2, column=1, pady=5)

        self.last_frame_label = ctk.CTkLabel(self.tab1, text="Enter Last Frame", fg_color="transparent", font=(ctk.CTkFont, 16))
        self.last_frame_label.grid(row=3, column=1, pady=5)

        self.last_grid_frame_entry = ctk.CTkEntry(self.tab1, placeholder_text="100", font=(ctk.CTkFont, 16))
        self.last_grid_frame_entry.grid(row=4, column=1, pady=5)

        self.grid_button = ctk.CTkButton(self.tab1, text="Extract Checkerboard Frames", command=self.checkerboard, font=(ctk.CTkFont, 16))
        self.grid_button.grid(row=6, column=1, pady=5)


        # Tab 1 Column 3
        self.grid_label = ctk.CTkLabel(self.tab1, text="3. Enter number of rows and columns on the checkerboard and the length of the squares in mm.",
                                       fg_color="transparent", font=(ctk.CTkFont, 20), wraplength=300)
        self.grid_label.grid(row=0, column=2, pady=(20, 20), padx=40, sticky="nw")

        self.rows_entry = ctk.CTkEntry(self.tab1, placeholder_text="17", font=(ctk.CTkFont, 16))
        self.rows_entry.grid(row=1, column=2, pady=5)

        self.columns_entry = ctk.CTkEntry(self.tab1, placeholder_text="24", font=(ctk.CTkFont, 16))
        self.columns_entry.grid(row=2, column=2, pady=5)

        self.scaling_entry = ctk.CTkEntry(self.tab1, placeholder_text="15", font=(ctk.CTkFont, 16))
        self.scaling_entry.grid(row=3, column=2, pady=5)

        self.calib_button = ctk.CTkButton(self.tab1, text="Calibrate Cameras", command=self.calibrate,
                                          font=(ctk.CTkFont, 16))
        self.calib_button.grid(row=6, column=2, pady=5)


        # Tab 2 Column 1
        self.times_label = ctk.CTkLabel(self.tab2, text="4. Create samples. For each sample, enter the sample start time and sample length in seconds in the format (1m35s, 2) (for a 2 second long snippet "
                                                       "starting at 1 min 35 seconds in the video) separating entries by line.", font=(ctk.CTkFont, 20), wraplength=300)
        self.times_label.grid(row=0, column=0, pady=(20, 20), sticky="nw", padx=(40, 0))

        self.times_textbox = ctk.CTkTextbox(self.tab2)
        self.times_textbox.grid(row=1, column=0, rowspan=7, columnspan=3, sticky="nsew", padx=(40, 0))

        self.trim_button = ctk.CTkButton(self.tab2, text="Trim Samples", command=self.trim, font=(ctk.CTkFont, 16))
        self.trim_button.grid(row=9, column=0, pady=5, padx=(40, 0))


        # Tab 3 Column 1
        self.experiment_title_label = ctk.CTkLabel(self.tab3, text="5. Enter the experiment details.\nOr, upload experiment from JSON file", font=(ctk.CTkFont, 20), wraplength=300)
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

    def select_left_video(self):
        self.left_video = filedialog.askopenfilename(initialdir=self.data_dir, filetypes=[("MP4 Files", ["*.mp4", "*.MP4"])])

    def select_right_video(self):
        self.right_video = filedialog.askopenfilename(initialdir=self.data_dir, filetypes=[("MP4 Files", ["*.mp4", "*.MP4"])])

    def sync_videos(self):
        fps = self.fps_entry.get()

        if not fps.isdigit():
            self.show_error("Error: FPS entry must be a valid positive integer")
        elif self.data_dir is None or self.left_video is None or self.right_video is None:
            self.show_error("Error: Make selections for the directory, left video, and right video")
        else:
            self.waiting(self.tab1, "Syncing videos...")
            find_sync(fps, self.left_video, self.right_video)
            self.finished()
            self.left_video = self.data_dir + "/left_sync.mp4"
            self.right_video = self.data_dir + "/right_sync.mp4"
            print(self.right_video)

    def show_error(self, error_message):
        messagebox.showerror("Error", error_message)

    def checkerboard(self):
        first_frame = int(self.first_grid_frame_entry.get())
        last_frame = int(self.last_grid_frame_entry.get())
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
            command = f"ffmpeg -ss 00:{time_str} -t 00:00:0{entry[1]} -i {self.left_video} -c:v copy -c:a copy {self.data_dir}/samples/left_{minute}m{second}s.mp4"
            subprocess.run(command, shell=True)
            command = f"ffmpeg -ss 00:{time_str} -t 00:00:0{entry[1]} -i {self.right_video} -c:v copy -c:a copy {self.data_dir}/samples/right_{minute}m{second}s.mp4"
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

    def toggle_message(self):
        if self.is_running:
            self.finished()
        else:
            self.waiting(self.tab1)
        self.is_running = not self.is_running

    def waiting(self, tab, message="Running... Please Wait."):
        self.running_message = ctk.CTkLabel(tab, text=message, font=(ctk.CTkFont, 30))
        if tab is self.tab1 or self.tab3:
            col = 1
        else:
            col = 0
        self.running_message.grid(row=100, column=col, pady=(40, 0))

    def finished(self):
        self.running_message.grid_forget()


if __name__ == "__main__":
    app = App()
    app.mainloop()
