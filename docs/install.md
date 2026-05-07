# Install

`cotracker-lips` targets **Linux** with **Python 3.10** and a **CUDA-capable
GPU**. macOS works for non-tracker pieces (sync, calibration), but CoTracker
is far slower on CPU.

## 1. Python environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Install PyTorch matching your CUDA version following the
[official selector](https://pytorch.org/get-started/locally/) before
proceeding. `pyproject.toml` only declares a soft `torch>=2.1` dependency to
avoid pinning users to a specific CUDA build.

## 2. Install the package and vendored dependencies

```bash
pip install -e .
pip install -e cotracker
pip install -e SPIGA
```

The vendored `cotracker/` and `SPIGA/` directories contain local
modifications and must be installed in-place; do **not** replace them with
PyPI versions.

## 3. CoTracker checkpoints

```bash
scripts/download_checkpoints.sh
```

This writes `cotracker2.pth` and `scaled_online.pth` into
`./checkpoints/`. To put them elsewhere, set
`COTRACKER_LIPS_CHECKPOINTS=/path/to/dir` before running the script and
mirror the path in your YAML config.

## 4. SPIGA model weights

Download `spiga_300wprivate.pt` from the
[SPIGA Google Drive](https://drive.google.com/drive/folders/1olrkoiDNK_NUCscaG9BbO3qsussbDi7I)
and place it at:

```
SPIGA/spiga/models/weights/spiga_300wprivate.pt
```

(create `weights/` if it does not exist).

## 5. (Optional) Sapiens

Sapiens is required only if you want to use `--tracker sapiens`. SPIGA alone
is sufficient for the headline pipeline.

1. Install [Sapiens Lite](https://github.com/facebookresearch/sapiens)
   following the upstream instructions.
2. Replace the modified files we ship under `sapiens_files/` into the
   matching paths in your Sapiens checkout. Keep the upstream directory
   layout intact.
3. Download the `sapiens-pose-1b` checkpoint
   (`sapiens_1b_goliath_best_goliath_AP_639_torchscript.pt2`).
4. Point the package at the Sapiens scripts directory:

```yaml
# in your config YAML
sapiens_scripts_dir: /path/to/sapiens/lite/scripts
sapiens_conda_env: sapiens_lite     # name of the conda env Sapiens runs in
```

## 6. Smoke-test

```bash
cotracker-lips --help
pytest tests/                       # the math + config suite, no GPU needed
```

If `cotracker-lips --help` prints the subcommand list and `pytest` is green,
you are ready to run [the GUI](gui.md) or the [CLI workflow](cli.md).
