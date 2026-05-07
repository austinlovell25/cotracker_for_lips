# Graphical workflow

```bash
cotracker-lips gui      # the main 3-tab wizard
cotracker-lips refine   # click-to-correct existing tracking results
```

Both windows share the same config resolution as the CLI (see
[install.md](install.md) and [cli.md](cli.md)).

## Main GUI (`cotracker-lips gui`)

### Tab 1 — Calibrate Cameras

1. **Select Directory.** Pick a folder containing your `left.mp4` and
   `right.mp4`. All intermediate and final files end up here.
2. **Select Left/Right Video.**
3. **FPS** + **clap search window**, then **Sync Videos**. The audio
   waveform appears with the suggested threshold; accept it or override.
4. **Inspect Video** (optional) prints FPS and resolution.
5. Enter **first / last second the checkerboard appears**, then
   **Extract Checkerboard Frames**.
6. Enter **rows × columns × square length (mm)**, then **Calibrate Cameras**.
   The per-camera RMSE is displayed when calibration finishes.

### Tab 2 — Create Samples

1. Enter sample tags one per line: `1m35s, 2` for a 2-second clip starting
   at 1:35. **Trim Samples** writes `samples/left_1m35s.mp4` and
   `samples/right_1m35s.mp4`.
2. (Optional) **Draw Black Box** opens the first frame of each side. Left-
   click the top-left corner, right-click the bottom-right corner, then
   **Block Selection** to write redacted copies of every sample. Originals
   are preserved under `samples/original/`.

### Tab 3 — Run Tracker

1. Either fill in **Experiment Name** + sample tags, or **Upload JSON**
   matching `examples/trial_example.json`.
2. Pick **Cotracker2** or **Cotracker3**, **Spiga** or **Sapiens**.
3. **Run Tracker.** Each sample takes a few minutes on a recent GPU. Final
   3D point clouds and per-frame upper-lip / lower-lip distance are written
   under `<save_dir>/{cotracker_out|sapiens_cotracker}/<exp_name>/`.

## Refiner (`cotracker-lips refine`)

After a `track` run completes, the refiner lets you fix individual frames
where CoTracker drifted:

1. **Select Tracking Samples Directory** — point at
   `<save_dir>/cotracker_out/<exp_name>/`.
2. **Display** plots the upper-lower lip distance over time. Click a frame
   on the plot to load it in both camera views.
3. Left-click the upper lip, right-click the lower lip in **each** view.
4. **Rerun Tracker** clips both source videos from that frame onward,
   re-runs CoTracker with the new query points, splices the result into
   the original CSV, re-triangulates, and writes overlay videos under
   `refine_frame<N>/combined/`.
