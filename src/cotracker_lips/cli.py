"""Unified ``cotracker-lips`` command-line interface.

Subcommands map one-to-one to pipeline stages so each one is independently
useful::

    cotracker-lips sync       --left L.mp4 --right R.mp4 --fps 60
    cotracker-lips frames     --start-sec 11 --end-sec 27 --fps 60 \
                              --left L.mp4 --right R.mp4 --out CALIB
    cotracker-lips calibrate  --rows 17 --cols 24 --scaling 15 --dir CALIB
    cotracker-lips track      --config trial.json --tracker spiga
    cotracker-lips gui
    cotracker-lips refine

All boolean flags are real ``--flag/--no-flag`` argparse flags — the legacy
``"True"/"true"/"t"`` string parsing is gone.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from cotracker_lips.calibration import extract_checkerboard_frames, run_calibration
from cotracker_lips.config import Config, load_config
from cotracker_lips.errors import CotrackerLipsError
from cotracker_lips.logging_setup import configure_logging
from cotracker_lips.pipeline import SampleSpec, run_pipeline
from cotracker_lips.sync import sync_videos
from cotracker_lips.trackers.base import TrackerKind

logger = logging.getLogger(__name__)


# ---------------- argument parser ---------------- #


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cotracker-lips",
        description="3D markerless lip tracking from synchronized stereo video.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a YAML config file. Overrides $COTRACKER_LIPS_CONFIG.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Logging level (DEBUG, INFO, WARNING). Default: INFO.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # sync
    p_sync = sub.add_parser("sync", help="Audio-sync a stereo pair using a clap.")
    p_sync.add_argument("--left", type=Path, required=True, help="Left video mp4.")
    p_sync.add_argument("--right", type=Path, required=True, help="Right video mp4.")
    p_sync.add_argument("--fps", type=int, required=True, help="Video frame rate.")
    p_sync.add_argument(
        "--range-end-sec", type=float, default=60.0,
        help="Search window for the clap, in seconds from the start (default 60).",
    )
    p_sync.add_argument(
        "--threshold", type=int, default=None,
        help="Override the auto-selected clap threshold.",
    )

    # frames
    p_frames = sub.add_parser(
        "frames", help="Sample checkerboard frames for calibration."
    )
    p_frames.add_argument("--left", type=Path, required=True)
    p_frames.add_argument("--right", type=Path, required=True)
    p_frames.add_argument(
        "--start-frame", type=int,
        help="First frame index. Either --start-frame or (--start-sec + --fps) required.",
    )
    p_frames.add_argument("--end-frame", type=int, help="Last frame index.")
    p_frames.add_argument("--start-sec", type=float, help="First second the board appears.")
    p_frames.add_argument("--end-sec", type=float, help="Last second the board appears.")
    p_frames.add_argument("--fps", type=int, help="Video frame rate (only with --start-sec).")
    p_frames.add_argument(
        "--out", type=Path, required=True,
        help="Output directory; will contain D2/, J2/, synced/.",
    )
    p_frames.add_argument("--num-frames", type=int, default=50)
    p_frames.add_argument("--seed", type=int, default=None)

    # calibrate
    p_calib = sub.add_parser(
        "calibrate", help="Calibrate camera intrinsics + stereo extrinsics."
    )
    p_calib.add_argument("--dir", type=Path, required=True,
                         help="Directory containing D2/, J2/, synced/ from `frames`.")
    p_calib.add_argument("--rows", type=int, required=True)
    p_calib.add_argument("--cols", type=int, required=True)
    p_calib.add_argument("--scaling", type=float, default=15.0,
                         help="Square length in mm (default 15).")

    # track
    p_track = sub.add_parser(
        "track", help="Run the full tracker pipeline on one or more sample pairs."
    )
    p_track.add_argument(
        "--spec", type=Path,
        help="JSON spec file (see examples/trial_example.json).",
    )
    p_track.add_argument("--exp-name", help="Experiment name (without --spec).")
    p_track.add_argument("--video-dir", type=Path,
                         help="Directory containing samples/<left|right>_<time>.mp4 pairs.")
    p_track.add_argument("--cam-config-dir", type=Path,
                         help="Directory holding camera{1,2}.yml + stereo_coeffs.yml.")
    p_track.add_argument("--save-dir", type=Path, help="Where to write final output.")
    p_track.add_argument("--times", nargs="*", default=[],
                         help="Sample time tags (e.g. 1m35s 2m10s).")
    p_track.add_argument("--tracker", choices=["spiga", "sapiens"], default="spiga")
    p_track.add_argument("--grid-config", default="global_lip.json",
                         help="Grid config JSON name (relative to grid_configs/).")
    p_track.add_argument("--cotracker-version", type=int, choices=[2, 3], default=None)
    p_track.add_argument("--snap-middle", action=argparse.BooleanOptionalAction, default=False,
                         help="Snap upper-row lip points to nearest edge.")

    # gui / refine
    sub.add_parser("gui", help="Launch the main 3-tab GUI.")
    sub.add_parser("refine", help="Launch the tracking-refiner GUI.")

    return parser


# ---------------- subcommand handlers ---------------- #


def _resolve_frame_range(args: argparse.Namespace) -> tuple[int, int]:
    if args.start_frame is not None and args.end_frame is not None:
        return args.start_frame, args.end_frame
    if args.start_sec is not None and args.end_sec is not None and args.fps is not None:
        return int(args.start_sec * args.fps), int(args.end_sec * args.fps)
    raise SystemExit(
        "Provide either --start-frame/--end-frame, "
        "or --start-sec/--end-sec/--fps."
    )


def _cmd_sync(args: argparse.Namespace, cfg: Config) -> int:
    sync_videos(
        cfg=cfg,
        fps=args.fps,
        left_video=args.left,
        right_video=args.right,
        range_end_sec=args.range_end_sec,
        threshold=args.threshold,
    )
    print(f"wrote {cfg.work_dir}/left_sync.mp4 and {cfg.work_dir}/right_sync.mp4")
    return 0


def _cmd_frames(args: argparse.Namespace, _cfg: Config) -> int:
    start, end = _resolve_frame_range(args)
    extract_checkerboard_frames(
        left_video=args.left,
        right_video=args.right,
        start_frame=start,
        end_frame=end,
        out_dir=args.out,
        num_frames=args.num_frames,
        seed=args.seed,
    )
    print(f"wrote calibration frames to {args.out}")
    return 0


def _cmd_calibrate(args: argparse.Namespace, _cfg: Config) -> int:
    calib = run_calibration(
        cam_config_dir=args.dir,
        rows=args.rows,
        cols=args.cols,
        world_scaling=args.scaling,
    )
    print(f"camera1 RMSE = {calib.left.rmse:.4f}")
    print(f"camera2 RMSE = {calib.right.rmse:.4f}")
    return 0


def _cmd_track(args: argparse.Namespace, cfg: Config) -> int:
    if args.spec:
        with args.spec.open("r", encoding="utf-8") as f:
            spec = json.load(f)
        exp_name = spec["experiment_name"]
        video_dir = Path(spec["source_data_directory"]).expanduser().resolve()
        save_dir = Path(spec.get("save_directory", video_dir)).expanduser().resolve()
        cam_config_dir = Path(spec.get("cam_config_directory", video_dir)).expanduser().resolve()
        times = spec["times"]
        snap = bool(spec.get("is_use_snap", args.snap_middle))
        cotracker_version = (
            3 if spec.get("is_cotracker_three", True) else 2
        )
    else:
        for required in ("exp_name", "video_dir"):
            if getattr(args, required) is None:
                raise SystemExit(f"--{required.replace('_', '-')} is required without --spec")
        exp_name = args.exp_name
        video_dir = args.video_dir.resolve()
        save_dir = (args.save_dir or video_dir).resolve()
        cam_config_dir = (args.cam_config_dir or video_dir).resolve()
        times = args.times
        snap = args.snap_middle
        cotracker_version = args.cotracker_version or cfg.cotracker_version

    if not times:
        raise SystemExit("no sample times provided (use --times or include `times` in --spec)")

    samples_dir = video_dir / "samples"
    samples = [
        SampleSpec(
            name=f"{exp_name}_{t}",
            left_video=samples_dir / f"left_{t}.mp4",
            right_video=samples_dir / f"right_{t}.mp4",
        )
        for t in times
    ]

    from cotracker_lips.config import with_overrides

    cfg = with_overrides(
        cfg,
        cotracker_version=cotracker_version,
        work_dir=video_dir,
    )
    cfg.ensure_dirs()
    results = run_pipeline(
        cfg=cfg,
        samples=samples,
        tracker=args.tracker,
        cam_config_dir=cam_config_dir,
        save_dir=save_dir,
        grid_config_name=args.grid_config,
        snap_middle=snap,
    )
    for r in results:
        print(f"{r.sample.name}: 3D output at {r.triangulation.output_dir}")
    return 0


def _cmd_gui(_args: argparse.Namespace, cfg: Config) -> int:
    from cotracker_lips.gui import launch_main_gui

    launch_main_gui(cfg)
    return 0


def _cmd_refine(_args: argparse.Namespace, cfg: Config) -> int:
    from cotracker_lips.gui import launch_refiner_gui

    launch_refiner_gui(cfg)
    return 0


_HANDLERS = {
    "sync": _cmd_sync,
    "frames": _cmd_frames,
    "calibrate": _cmd_calibrate,
    "track": _cmd_track,
    "gui": _cmd_gui,
    "refine": _cmd_refine,
}


# ---------------- entry point ---------------- #


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level)
    cfg = load_config(config_path=args.config)
    handler = _HANDLERS[args.command]

    try:
        return handler(args, cfg)
    except CotrackerLipsError as e:
        logger.error("%s", e)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
