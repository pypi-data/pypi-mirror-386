"""High-level helpers for one-line recording workflows."""

from __future__ import annotations

import contextlib
import time
from pathlib import Path
from typing import Generator, Optional

from .config import RecorderConfig
from .optimization import MpdecimateOptimizer
from .recording import SegmentedRecorder


@contextlib.contextmanager
def recording_session(
    *,
    config: Optional[RecorderConfig] = None,
    segment_minutes: float = 5.0,
    fps: float = 1.0,
    resolution: str = "1126x732",
    crf: int = 30,
    output_root: Path | str = Path("sessions"),
    screen_index: str | int = "auto",
    capture_cursor: bool = True,
    capture_clicks: bool = False,
    ffmpeg_path: str = "ffmpeg",
    optimize: bool = True,
    optimizer_threshold: Optional[float] = 0.01,
    session_id: Optional[str] = None,
) -> Generator[SegmentedRecorder, None, None]:
    """Context manager that starts recording on enter and stops on exit.

    Parameters mirror :class:`RecorderConfig` and default to reasonable values so
    callers can simply do ``with recording_session():`` and control the duration
    inside the ``with`` block. Providing a pre-built ``config`` bypasses the
    individual keyword arguments.
    """

    if config is None:
        config = RecorderConfig(
            segment_minutes=segment_minutes,
            fps=fps,
            resolution=resolution,
            crf=crf,
            output_root=Path(output_root),
            screen_index=screen_index,
            capture_cursor=capture_cursor,
            capture_clicks=capture_clicks,
            ffmpeg_path=ffmpeg_path,
            optimizer_threshold=optimizer_threshold,
        )

    optimizer = None
    if optimize and config.optimizer_threshold:
        optimizer = MpdecimateOptimizer(
            ffmpeg_path=config.ffmpeg_path, threshold=config.optimizer_threshold
        )

    recorder = SegmentedRecorder(config, optimizer=optimizer, session_id=session_id)
    recorder.start()
    try:
        yield recorder
    finally:
        recorder.stop()


def record_screen(
    duration_seconds: float,
    *,
    segment_minutes: float = 5.0,
    fps: float = 1.0,
    resolution: str = "1126x732",
    crf: int = 30,
    output_root: Path | str = Path("sessions"),
    screen_index: str | int = "auto",
    capture_cursor: bool = True,
    capture_clicks: bool = False,
    ffmpeg_path: str = "ffmpeg",
    optimize: bool = True,
    optimizer_threshold: Optional[float] = 0.01,
    session_id: Optional[str] = None,
) -> Path:
    """Record the screen for ``duration_seconds`` and return the session folder."""
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")

    config = RecorderConfig(
        segment_minutes=segment_minutes,
        fps=fps,
        resolution=resolution,
        crf=crf,
        output_root=Path(output_root),
        screen_index=screen_index,
        capture_cursor=capture_cursor,
        capture_clicks=capture_clicks,
        ffmpeg_path=ffmpeg_path,
        optimizer_threshold=optimizer_threshold if optimize else None,
    )

    optimizer = None
    if optimize and config.optimizer_threshold:
        optimizer = MpdecimateOptimizer(
            ffmpeg_path=config.ffmpeg_path, threshold=config.optimizer_threshold
        )

    recorder = SegmentedRecorder(config, optimizer=optimizer, session_id=session_id)
    recorder.start()
    try:
        time.sleep(duration_seconds)
    finally:
        recorder.stop()

    return recorder.session_dir
