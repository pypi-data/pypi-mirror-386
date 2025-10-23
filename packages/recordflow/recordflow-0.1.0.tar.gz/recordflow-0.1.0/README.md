# recordflow

Convenience helpers for recording segmented screen captures on macOS using `ffmpeg`.

## Installation

Build and install locally while iterating:

```bash
python -m pip install --upgrade build
python -m build        # creates dist/*.tar.gz and dist/*.whl
python -m pip install dist/recordflow-0.1.0-py3-none-any.whl
```

After publishing a release to PyPI the package can be installed with:

```bash
python -m pip install recordflow
```

## Quickstart

Record the screen for a fixed duration and return the created session directory:

```python
from recordflow import record_screen

session_dir = record_screen(duration_seconds=30, fps=5, resolution="1440x900")
print("Segments stored in:", session_dir)
```

Run ad-hoc recordings with custom logic inside a `with` block:

```python
from time import sleep
from recordflow import recording_session

with recording_session(fps=2, segment_minutes=1) as recorder:
    sleep(10)
    print("Current segment:", recorder.current_segment)
```

Use the bundled CLI to keep capturing until interrupted:

```bash
recordflow live --fps 5 --segment-minutes 2
```

## Development

Run the lightweight unit test suite with:

```bash
python -m unittest discover -s tests -p "test*.py"
```

## Publishing

1. Update the version in `pyproject.toml`.
2. Build fresh distributions with `python -m build`.
3. Upload with `python -m twine upload dist/*`.
