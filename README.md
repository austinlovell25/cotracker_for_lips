# cotracker-lips

**3D markerless tracking of lip movements from synchronized stereo video**, built on
Meta's [CoTracker](https://co-tracker.github.io/) and either
[SPIGA](https://github.com/andresprados/SPIGA) or
[Sapiens](https://github.com/facebookresearch/sapiens) for facial landmark detection.

Given a left and right camera recording the same speaker, the pipeline:

1. **Synchronizes** the two videos using a shared clapperboard impulse.
2. **Calibrates** the stereo pair from a checkerboard sequence.
3. **Detects** 2D lip landmarks per frame using SPIGA or Sapiens.
4. **Tracks** dense lip points through the cropped video with CoTracker.
5. **Triangulates** matched left/right tracks into a 3D point cloud and
   reports the upper-to-lower-lip distance over time with sub-millimeter
   precision.

## Quickstart

```bash
git clone https://github.com/austinlovell25/cotracker_for_lips.git
cd cotracker_for_lips

# Python 3.10 venv. PyTorch + a CUDA-capable GPU is recommended.
python -m venv .venv && source .venv/bin/activate

pip install -e .
pip install -e cotracker  # vendored CoTracker (Meta) — local mods preserved
pip install -e SPIGA      # vendored SPIGA (UAM)     — local mods preserved

scripts/download_checkpoints.sh
# also fetch SPIGA model weights from the Drive link in docs/install.md

cotracker-lips gui
```

For first-time setup details (CUDA matrix, SPIGA weights, optional Sapiens
install), see [docs/install.md](docs/install.md).

## Usage

### Graphical workflow

```bash
cotracker-lips gui
```

A 3-tab wizard covers the full pipeline:

| Tab | Purpose |
| --- | --- |
| **Calibrate Cameras** | Sync the videos via clap detection; sample checkerboard frames; run stereo calibration. |
| **Create Samples**    | Trim the synchronized footage into the short clips you want analyzed; optionally black-box regions you want hidden from the tracker. |
| **Run Tracker**       | Choose SPIGA or Sapiens, enter sample timestamps (or upload a JSON spec), and run the pipeline. |

A second window (`cotracker-lips refine`) lets you click-correct individual
frames and re-run CoTracker over only the trailing portion of a clip.

### Command-line workflow

Each subcommand maps to one stage so you can script the pipeline piece by
piece:

```bash
# Stereo audio sync.
cotracker-lips sync --left left.mp4 --right right.mp4 --fps 60

# Sample 50 random checkerboard frames into D2/, J2/, synced/.
cotracker-lips frames \
  --left left_sync.mp4 --right right_sync.mp4 \
  --start-sec 11 --end-sec 27 --fps 60 \
  --out ./calibration_data

# Solve intrinsics + stereo extrinsics.
cotracker-lips calibrate --rows 17 --cols 24 --scaling 15 --dir ./calibration_data

# Trim each sample with ffmpeg before this step (see docs/cli.md). Then:
cotracker-lips track --spec examples/trial_example.json --tracker spiga
```

`cotracker-lips <subcommand> --help` documents every flag.

### JSON spec for `track`

The full pipeline can be driven by a single JSON file (the GUI's
"Upload JSON" button uses the same format):

```jsonc
{
  "experiment_name": "subject_42",
  "source_data_directory": "/data/subject_42",
  "save_directory":        "/data/subject_42/out",
  "cam_config_directory":  "/data/subject_42",
  "trimmed_or_overlay":    "trimmed",
  "is_use_snap":           false,
  "is_crop_shift":         false,
  "is_cotracker_three":    true,
  "times": ["1m35s", "2m10s"]
}
```

See [examples/trial_example.json](examples/trial_example.json).

## Configuration

Runtime settings live in YAML and resolve in this order:

1. CLI flags (highest priority)
2. `COTRACKER_LIPS_*` environment variables
3. The YAML file at `--config` or `$COTRACKER_LIPS_CONFIG`
4. Bundled [`configs/default.yaml`](configs/default.yaml)

Edit a copy of the default to set portable paths:

```bash
cp configs/default.yaml my_config.yaml
$EDITOR my_config.yaml
cotracker-lips track --config my_config.yaml --spec examples/trial_example.json
```

## Project layout

```
src/cotracker_lips/        # the installable package
  cli.py                   # `cotracker-lips` entry point
  config.py                # Config dataclass + YAML loader
  pipeline/                # full-pipeline orchestrator (replaces shell scripts)
  trackers/                # SpigaTracker, SapiensTracker, CoTrackerRunner
  calibration/             # checkerboard sampling, stereo calibration, triangulation
  postprocess/             # crop offsets, edge-snap helpers
  sync/                    # audio clap detection
  gui/                     # customtkinter front-end (app + refiner)
  io/                      # ffmpeg, video, CSV, path helpers
configs/                   # default.yaml + grid_configs/*.json
examples/                  # trial_example.json + sample CSV data
tests/                     # pytest suite (math/config; no GPU required)
docs/                      # install / CLI / GUI / architecture
scripts/                   # download_checkpoints.sh
cotracker/                 # vendored CoTracker (Meta, with local mods)
SPIGA/                     # vendored SPIGA (UAM, with local mods)
sapiens_files/             # patches applied during Sapiens install
```

## Citing

If this work supports a publication, please cite the upstream projects:
**CoTracker** (Karaev et al., Meta), **SPIGA** (Prados-Torreblanca et al.),
and **Sapiens** (Khirodkar et al., Meta).

## License

MIT. See [LICENSE](LICENSE) (vendored libraries retain their own licenses).
