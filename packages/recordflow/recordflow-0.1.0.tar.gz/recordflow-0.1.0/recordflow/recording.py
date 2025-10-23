"""Segmented recorder implementation."""

from __future__ import annotations

import logging
import re
import signal
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import RecorderConfig
from .optimization import MpdecimateOptimizer, OptimizationResult

logger = logging.getLogger(__name__)


class SegmentedRecorder:
    """Continuously capture the screen into fixed-length segments."""

    def __init__(
        self,
        config: RecorderConfig,
        *,
        optimizer: Optional[MpdecimateOptimizer] = None,
        session_id: Optional[str] = None,
    ):
        self.config = config
        self.config.validate()
        self.optimizer = optimizer
        self.session_id = session_id or self._generate_session_id()
        self.session_dir = (config.output_root / self.session_id).resolve()
        self.segments_dir = self.session_dir / "segments"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.segments_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._recording_thread: Optional[threading.Thread] = None
        self._current_process: Optional[subprocess.Popen] = None
        self._current_segment = -1
        self._cached_screen_index: Optional[str] = None

        self._setup_logging()
        logger.info("Session %s → %s", self.session_id, self.session_dir)

    # --------------------------------------------------------------------- API
    @property
    def is_running(self) -> bool:
        return self._recording_thread is not None and self._recording_thread.is_alive()

    @property
    def current_segment(self) -> int:
        return self._current_segment

    def start(self) -> None:
        """Spawn the background recording loop."""
        if self.is_running:
            logger.warning("Recorder already running")
            return
        logger.info(
            "Recording at %s fps, %s, %s minute segments",
            self.config.fps,
            self.config.resolution,
            self.config.segment_minutes,
        )
        self._stop_event.clear()
        self._recording_thread = threading.Thread(
            target=self._recording_loop, daemon=True
        )
        self._recording_thread.start()

    def stop(self) -> None:
        """Stop recording and wait for the background thread to exit."""
        if not self.is_running:
            return

        logger.info("Stopping recorder…")
        self._stop_event.set()

        with self._lock:
            process = self._current_process

        if process and process.poll() is None:
            try:
                process.send_signal(signal.SIGINT)
                process.wait(timeout=self.config.finalize_timeout)
            except subprocess.TimeoutExpired:
                logger.warning("Force killing ffmpeg process")
                process.kill()
                process.wait()

        if self._recording_thread:
            self._recording_thread.join(timeout=self.config.finalize_timeout + 5)
            self._recording_thread = None

        logger.info("Recorder stopped")

    def run_sync(self) -> None:
        """Run recording loop in the foreground until interrupted."""
        self.start()
        try:
            while self.is_running:
                time.sleep(0.5)
        except KeyboardInterrupt:  # pragma: no cover - manual stop
            logger.info("Interrupted by user")
        finally:
            self.stop()

    # ----------------------------------------------------------------- internals
    def _recording_loop(self) -> None:
        segment_idx = 0
        while not self._stop_event.is_set():
            success = self._record_segment(segment_idx)
            if success:
                self._current_segment = segment_idx
                segment_idx += 1
            else:
                logger.warning("Segment %s failed; retrying in 5 seconds", segment_idx)
                time.sleep(5)
        logger.info("Recording loop exited after %s segments", segment_idx)

    def _record_segment(self, segment_idx: int) -> bool:
        segment_path = self._segment_path(segment_idx)
        temp_path = segment_path.with_suffix(segment_path.suffix + ".partial")
        if segment_path.exists():
            logger.warning("Overwriting existing segment at %s", segment_path)
            segment_path.unlink()
        if temp_path.exists():
            temp_path.unlink()

        command = self._build_ffmpeg_command(temp_path)
        logger.info("Segment %04d → %s", segment_idx, segment_path.name)

        process: Optional[subprocess.Popen] = None
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            with self._lock:
                self._current_process = process

            time.sleep(self.config.segment_seconds())

            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                try:
                    process.communicate(timeout=self.config.finalize_timeout)
                except subprocess.TimeoutExpired:
                    logger.warning("Finalization timeout; killing ffmpeg")
                    process.kill()
                    process.communicate()

            if not temp_path.exists() or temp_path.stat().st_size == 0:
                stderr_snippet = ""
                if process:
                    stderr_snippet = ""
                    if process.stderr:
                        try:
                            stderr_data = process.stderr.read()
                        except ValueError:
                            stderr_data = b""
                        stderr_snippet = (stderr_data or b"").decode("utf-8", errors="replace")[:500]
                        if "Invalid device index" in stderr_snippet:
                            logger.warning("Invalid device index detected; refreshing screen selection")
                            self._cached_screen_index = None
                logger.error("Segment %04d failed: %s", segment_idx, stderr_snippet)
                return False

            try:
                temp_path.replace(segment_path)
            except OSError as exc:
                logger.error("Failed to finalize segment %04d: %s", segment_idx, exc)
                return False

            logger.info(
                "Saved segment %s (%.1f MB)",
                segment_path.name,
                segment_path.stat().st_size / (1024 * 1024),
            )
            if self.optimizer:
                threading.Thread(
                    target=self._optimize_segment,
                    args=(segment_path,),
                    daemon=True,
                    name=f"optimize-{segment_idx:04d}",
                ).start()
            return True
        except Exception as exc:  # pragma: no cover - durable logging
            logger.exception("Error while recording segment %04d: %s", segment_idx, exc)
            return False
        finally:
            with self._lock:
                self._current_process = None
            if temp_path.exists() and not segment_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    logger.warning("Could not clean up %s", temp_path)

    def _build_ffmpeg_command(self, output_path: Path) -> list[str]:
        screen_index = self._resolve_screen_index()
        cursor_flag = "1" if self.config.capture_cursor else "0"
        click_flag = "1" if self.config.capture_clicks else "0"

        return [
            self.config.ffmpeg_path,
            "-hide_banner",
            "-f",
            "avfoundation",
            "-framerate",
            "30",
            "-capture_cursor",
            cursor_flag,
            "-capture_mouse_clicks",
            click_flag,
            "-i",
            str(screen_index),
            "-c:v",
            "libx265",
            "-preset",
            "fast",
            "-crf",
            str(self.config.crf),
            "-tag:v",
            "hvc1",
            "-vf",
            f"fps={self.config.fps},scale={self.config.resolution},format=yuv420p",
            "-an",
            "-f",
            "mp4",
            str(output_path),
        ]

    def _resolve_screen_index(self) -> str:
        if self.config.screen_index != "auto":
            return str(self.config.screen_index)
        if self._cached_screen_index:
            return self._cached_screen_index

        cmd = [
            self.config.ffmpeg_path,
            "-f",
            "avfoundation",
            "-list_devices",
            "true",
            "-i",
            "",
        ]
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
        except Exception as exc:  # pragma: no cover - just fallback
            logger.warning("Screen detection failed (%s); defaulting to '4'", exc)
            self._cached_screen_index = "4"
            return self._cached_screen_index

        stderr = proc.stderr or ""
        candidates = self._extract_screen_candidates(stderr)
        chosen = self._select_screen_index(candidates)
        if chosen:
            self._cached_screen_index = chosen
            logger.info("Detected screen index %s", self._cached_screen_index)
        else:
            logger.warning("Falling back to screen index '4'")
            self._cached_screen_index = "4"

        return self._cached_screen_index

    @staticmethod
    def _extract_screen_candidates(stderr: str) -> list[tuple[str, str]]:
        candidates: list[tuple[str, str]] = []
        for line in stderr.splitlines():
            match = re.search(r"\[(\d+)\]\s+(.+)", line)
            if not match:
                continue
            index, label = match.group(1), match.group(2).strip()
            if "capture screen" in label.lower():
                candidates.append((index, label))
        return candidates

    @staticmethod
    def _select_screen_index(candidates: list[tuple[str, str]]) -> Optional[str]:
        if not candidates:
            return None

        def is_iphonescreen(label: str) -> bool:
            lowered = label.lower()
            return any(token in lowered for token in ("iphone", "ipad", "ipod"))

        for index, label in candidates:
            if not is_iphonescreen(label):
                return index

        return None

    def _segment_path(self, segment_idx: int) -> Path:
        return self.segments_dir / f"segment_{segment_idx:04d}.mp4"

    # Backwards compatibility shim for older tests/utilities
    def _get_segment_path(self, segment_idx: int) -> Path:
        return self._segment_path(segment_idx)

    def _setup_logging(self) -> None:
        log_path = self.session_dir / "session.log"
        if any(
            isinstance(handler, logging.FileHandler)
            and getattr(handler, "baseFilename", None) == str(log_path)
            for handler in logger.handlers
        ):
            return
        file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def _generate_session_id(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{ts}"

    def _optimize_segment(self, segment_path: Path) -> None:
        if not self.optimizer:
            return
        try:
            result: OptimizationResult = self.optimizer.optimize(segment_path)
            if result.success:
                logger.info(
                    "Optimized %s (%.1f%% smaller)",
                    segment_path.name,
                    result.size_reduction_percent,
                )
            else:
                logger.warning("Optimization failed for %s", segment_path.name)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Optimizer raised for %s: %s", segment_path, exc)
