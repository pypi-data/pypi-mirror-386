"""Video post-processing helpers."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Minimal stats for a single optimization pass."""

    success: bool
    source: Path
    output: Path
    original_bytes: int
    optimized_bytes: int
    frames_removed: Optional[int] = None
    size_reduction_bytes: int = 0
    command: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0

    @property
    def size_reduction_percent(self) -> float:
        if self.original_bytes == 0:
            return 0.0
        return (self.size_reduction_bytes / self.original_bytes) * 100


class MpdecimateOptimizer:
    """Thin wrapper around ffmpeg's mpdecimate filter."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", threshold: float = 0.01):
        if threshold <= 0 or threshold > 1:
            raise ValueError("threshold must be between 0 and 1")
        self.ffmpeg_path = ffmpeg_path
        self.threshold = threshold
        hi = int(64 * 64 * threshold)
        self._filter = f"mpdecimate=hi={hi}:lo={int(hi * 0.5)}:frac=0.33"

    def optimize(self, segment_path: Path, *, replace_original: bool = True) -> OptimizationResult:
        """Run mpdecimate against a segment."""
        segment_path = Path(segment_path)
        if not segment_path.exists():
            raise FileNotFoundError(segment_path)

        output_path = segment_path.with_name(f"{segment_path.stem}_optimized{segment_path.suffix}")
        temp_path = output_path.with_suffix(".tmp" + segment_path.suffix)

        cmd = [
            self.ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(segment_path),
            "-vf",
            self._filter,
            "-vsync",
            "vfr",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "28",
            "-pix_fmt",
            "yuv420p",
            "-y",
            str(temp_path),
        ]

        logger.debug("Optimizing %s via %s", segment_path.name, " ".join(cmd))
        start = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start

        if proc.returncode != 0 or not temp_path.exists():
            logger.warning("ffmpeg optimization failed for %s: %s", segment_path, proc.stderr.strip())
            return OptimizationResult(
                success=False,
                source=segment_path,
                output=temp_path,
                original_bytes=segment_path.stat().st_size if segment_path.exists() else 0,
                optimized_bytes=temp_path.stat().st_size if temp_path.exists() else 0,
                command=cmd,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=duration,
            )

        original_bytes = segment_path.stat().st_size
        optimized_bytes = temp_path.stat().st_size
        size_delta = original_bytes - optimized_bytes

        try:
            frames_removed = self._probe_frames(segment_path) - self._probe_frames(temp_path)
        except Exception as probe_error:  # pragma: no cover - fire-and-forget metric
            logger.debug("Skipping frame delta probe: %s", probe_error)
            frames_removed = None

        if replace_original:
            temp_path.replace(segment_path)
            final_output = segment_path
        else:
            final_output = output_path
            if output_path.exists():
                output_path.unlink()
            temp_path.replace(output_path)

        return OptimizationResult(
            success=True,
            source=segment_path,
            output=final_output,
            original_bytes=original_bytes,
            optimized_bytes=optimized_bytes,
            frames_removed=frames_removed,
            size_reduction_bytes=size_delta,
            command=cmd,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_seconds=duration,
        )

    def _probe_frames(self, video_path: Path) -> int:
        """Return the total frame count for the target video."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "json",
            str(video_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout or "{}")
        streams = data.get("streams") or []
        if not streams:
            return 0
        value = streams[0].get("nb_read_frames")
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
