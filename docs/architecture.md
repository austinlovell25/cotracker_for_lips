# Architecture

The package is layered from low-level I/O up to user-facing entry points.
Each layer depends only on the layers below it.

```
                               ┌──────────────────────────┐
                               │  cli.py        gui/      │  user-facing
                               └─────────────┬────────────┘
                                             │
                               ┌─────────────▼────────────┐
                               │   pipeline/orchestrator  │  full-run glue
                               └─────────────┬────────────┘
                                             │
       ┌───────────────┬─────────────────────┼───────────────────┐
       ▼               ▼                     ▼                   ▼
   sync/audio    calibration/             trackers/         postprocess/
       │             ├ checkerboard         ├ base.py           ├ crop.py
       │             ├ stereo               ├ spiga.py          ├ snap.py
       │             └ triangulate          ├ sapiens.py
       │                                    └ cotracker_runner.py
       └─────────────────────┬───────────────────────────────────┘
                             ▼
                       ┌────────────┐
                       │   io/      │  ffmpeg, video, csv schemas, paths
                       └─────┬──────┘
                             ▼
                       ┌────────────┐
                       │  config /  │  Config dataclass, errors, logging
                       │  errors    │
                       └────────────┘
```

## Key abstractions

* **`Config`** — frozen dataclass with every tunable path or knob. Loaded
  once via `load_config()` from CLI > env > YAML > defaults.
* **`Tracker`** ABC — one method, `detect_landmarks(left, right, out_dir) →
  LandmarkResult`. Implementations: `SpigaTracker`, `SapiensTracker`. The
  pipeline never branches on tracker type.
* **`Pipeline`** — instantiated with a `Config`, a `Tracker`, calibration
  dir, save dir, and a grid-config name. `pipeline.run(SampleSpec)` is the
  one public entry point.
* **`io/ffmpeg`** — every shell-out goes through this module. `shell=False`,
  argument lists, captured stderr, raises `FFmpegError` on non-zero exit.
* **`io/csv_schema`** — single source of truth for column names exchanged
  between stages.

## Why no shell scripts?

The legacy pipeline was driven by `spiga_pipeline.sh`,
`sapiens_cotracker.sh`, and `rerun_pipeline.sh`. They:

* Hardcoded the user's home-directory paths.
* Duplicated 80% of their logic across the three files.
* Mixed control flow (e.g. crop-shift loops) with subprocess plumbing.
* Used positional arguments with no validation.

`pipeline/orchestrator.py` replaces all three. Each former bash variable
becomes a typed parameter; each former `mv` becomes a `Path` operation;
each former tracker branch becomes a polymorphic dispatch through
`Tracker`.

## Vendored libraries

`cotracker/`, `SPIGA/`, and `sapiens_files/` are intentionally kept inside
the repo. They contain local modifications relative to upstream
(particularly the visualizer's `upper_pts.csv` / `lower_pts.csv` emission)
and the package depends on those modifications. They are imported via
`pip install -e cotracker` and `pip install -e SPIGA`; see
[install.md](install.md).

## Testing strategy

The `tests/` suite covers the parts that have honest math:

* `test_config.py` — load order, env precedence, coercion, immutability.
* `test_audio_sync.py` — threshold and clap-frame detection algebra.
* `test_crop.py` — crop-offset anchoring math.
* `test_triangulate.py` — DLT recovery against synthetic stereo geometry.

Runs without a GPU and without the vendored model weights, so CI can stay
cheap.
