"""Configuration dataclasses used by the recorder."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _default_sessions_root() -> Path:
    return Path("sessions")


@dataclass
class RecorderConfig:
    """Runtime knobs for the segmented recorder."""

    segment_minutes: float = 5.0
    fps: float = 1.0
    resolution: str = "1126x732"
    crf: int = 30
    output_root: Path = field(default_factory=_default_sessions_root)
    screen_index: str | int = "auto"
    capture_cursor: bool = True
    capture_clicks: bool = False
    ffmpeg_path: str = "ffmpeg"
    finalize_timeout: int = 60
    optimizer_threshold: Optional[float] = 0.01

    def segment_seconds(self) -> float:
        """Duration (seconds) for an individual segment."""
        return max(self.segment_minutes * 60, 1)

    def validate(self) -> None:
        """Fail fast on invalid configuration."""
        if self.segment_minutes <= 0:
            raise ValueError("segment_minutes must be > 0")
        if not (0.01 <= self.fps <= 120):
            raise ValueError("fps must be between 0.01 and 120")
        if not (0 <= self.crf <= 51):
            raise ValueError("crf must be between 0 and 51 for x265")
        if "x" not in self.resolution:
            raise ValueError("resolution must look like 'WIDTHxHEIGHT'")
