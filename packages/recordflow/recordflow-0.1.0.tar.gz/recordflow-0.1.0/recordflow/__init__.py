"""Public surface for the trimmed recorder package."""

from .api import record_screen, recording_session  # noqa: F401
from .config import RecorderConfig  # noqa: F401
from .optimization import MpdecimateOptimizer, OptimizationResult  # noqa: F401
from .recording import SegmentedRecorder  # noqa: F401

__all__ = [
    "RecorderConfig",
    "SegmentedRecorder",
    "MpdecimateOptimizer",
    "OptimizationResult",
    "record_screen",
    "recording_session",
]
