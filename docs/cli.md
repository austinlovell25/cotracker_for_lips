# Command-line workflow

The `cotracker-lips` console script exposes one subcommand per pipeline
stage. Stages are independent — you can re-run a single one without
repeating the rest.

```text
cotracker-lips [--config PATH] [--log-level LEVEL] <command> ...
```

## End-to-end example

```bash
WORK=/data/subject_42
cd $WORK   # left.mp4, right.mp4 live here

# 1. Audio-sync the two videos. Writes left_sync.mp4 + right_sync.mp4.
cotracker-lips sync --left left.mp4 --right right.mp4 --fps 60

# 2. Pull a 50-frame random sample of the checkerboard for calibration.
#    Use seconds-based or frame-based ranges interchangeably.
cotracker-lips frames \
  --left left_sync.mp4 --right right_sync.mp4 \
  --start-sec 11 --end-sec 27 --fps 60 \
  --out $WORK

# 3. Solve intrinsics + stereo extrinsics. Writes camera{1,2}.yml,
#    stereo_coeffs.yml, rmse.json.
cotracker-lips calibrate --rows 17 --cols 24 --scaling 15 --dir $WORK

# 4. Trim the samples you want tracked. The pipeline expects them under
#    $WORK/samples/{left,right}_<tag>.mp4 — for example left_1m35s.mp4.
mkdir -p samples
ffmpeg -ss 95 -i left_sync.mp4  -t 2 -c copy samples/left_1m35s.mp4
ffmpeg -ss 95 -i right_sync.mp4 -t 2 -c copy samples/right_1m35s.mp4

# 5. Run the full tracker on the samples.
cotracker-lips track \
  --exp-name subject_42 --video-dir $WORK \
  --times 1m35s 2m10s --tracker spiga
```

## Subcommand reference

### `sync`

| Flag | Meaning |
| --- | --- |
| `--left`, `--right` | Source videos. |
| `--fps` | Their frame rate. |
| `--range-end-sec` | Search window for the clap (default 60s). |
| `--threshold` | Override the auto threshold (advanced). |

Outputs `left_sync.mp4` / `right_sync.mp4` in `cfg.work_dir`.

### `frames`

| Flag | Meaning |
| --- | --- |
| `--start-frame` / `--end-frame` | Frame range, inclusive. |
| `--start-sec` / `--end-sec` / `--fps` | Equivalent in seconds. |
| `--out` | Destination dir; will contain `D2/`, `J2/`, `synced/`. |
| `--num-frames` | How many frames to sample (default 50). |
| `--seed` | RNG seed for reproducibility. |

### `calibrate`

| Flag | Meaning |
| --- | --- |
| `--dir` | Directory created by `frames`. |
| `--rows`, `--cols` | Inner-corner counts of the checkerboard. |
| `--scaling` | Square length in mm (default 15). |

Writes `camera1.yml`, `camera2.yml`, `stereo_coeffs.yml`, `rmse.json`.

### `track`

| Flag | Meaning |
| --- | --- |
| `--spec` | JSON spec — see `examples/trial_example.json`. |
| `--exp-name`, `--video-dir`, `--times` | Inline alternative to `--spec`. |
| `--cam-config-dir` | Where the calibration YAMLs live (defaults to video-dir). |
| `--save-dir` | Output root (defaults to video-dir). |
| `--tracker` | `spiga` (default) or `sapiens`. |
| `--grid-config` | One of the JSONs in `configs/grid_configs/`. |
| `--cotracker-version` | `2` or `3`. |
| `--snap-middle` | Snap upper-row lip queries to the nearest edge. |

Outputs are written under `<save-dir>/{cotracker_out|sapiens_cotracker}/<exp_name>/`.

### `gui` / `refine`

`gui` launches the full 3-tab wizard; `refine` launches the
manual-correction tool described in [gui.md](gui.md).

## Logging

`COTRACKER_LIPS_LOG=DEBUG` (or `--log-level DEBUG`) prints the exact ffmpeg
and SPIGA invocations. Useful when something fails — every subprocess error
includes its captured stderr.
