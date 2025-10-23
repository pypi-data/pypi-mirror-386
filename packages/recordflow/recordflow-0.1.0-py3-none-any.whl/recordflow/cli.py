"""Minimal command-line interface for the segmented recorder."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from .config import RecorderConfig
from .optimization import MpdecimateOptimizer
from .recording import SegmentedRecorder

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recordflow",
        description="Record the screen into time-bounded segments.",
    )
    sub = parser.add_subparsers(dest="command")

    live = sub.add_parser("live", help="Start recording and write segments into sessions/.")
    _attach_recorder_args(live)
    live.add_argument("--segments", type=int, default=0, help="Stop after N segments (0 = run until interrupted).")
    live.add_argument("--duration", type=float, default=0.0, help="Stop after N seconds (0 = indefinite).")
    live.set_defaults(func=_cmd_live)

    return parser


def _attach_recorder_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--segment-minutes", type=float, default=5.0, help="Length of each segment in minutes.")
    parser.add_argument("--fps", type=float, default=1.0, help="Frames per second to sample from the capture stream.")
    parser.add_argument("--resolution", type=str, default="1126x732", help="Scaled output resolution (WxH).")
    parser.add_argument("--crf", type=int, default=30, help="ffmpeg CRF quality for libx265.")
    parser.add_argument("--output-root", type=Path, default=Path("sessions"), help="Root directory for session folders.")
    parser.add_argument("--screen-index", type=str, default="auto", help="Target screen index or 'auto'.")
    parser.add_argument("--no-cursor", action="store_true", help="Disable cursor capture.")
    parser.add_argument("--capture-clicks", action="store_true", help="Highlight mouse clicks in the capture.")
    parser.add_argument("--ffmpeg", type=str, default="ffmpeg", help="Path to the ffmpeg binary.")
    parser.add_argument("--disable-optimizer", action="store_true", help="Skip mpdecimate optimization pass.")
    parser.add_argument(
        "--optimizer-threshold",
        type=float,
        default=0.01,
        help="mpdecimate threshold when optimization is enabled.",
    )


def _cmd_live(args: argparse.Namespace) -> int:
    config = RecorderConfig(
        segment_minutes=args.segment_minutes,
        fps=args.fps,
        resolution=args.resolution,
        crf=args.crf,
        output_root=args.output_root,
        screen_index=args.screen_index,
        capture_cursor=not args.no_cursor,
        capture_clicks=args.capture_clicks,
        ffmpeg_path=args.ffmpeg,
        optimizer_threshold=None if args.disable_optimizer else args.optimizer_threshold,
    )

    optimizer = None
    if not args.disable_optimizer and config.optimizer_threshold:
        optimizer = MpdecimateOptimizer(ffmpeg_path=args.ffmpeg, threshold=config.optimizer_threshold)

    recorder = SegmentedRecorder(config, optimizer=optimizer)

    stop_event = threading.Event()

    def _handle_signal(_sig, _frame):
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    recorder.start()

    start_time = time.time()
    target_segment = args.segments - 1 if args.segments > 0 else None

    try:
        while not stop_event.is_set():
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                stop_event.set()
                break

            if target_segment is not None and recorder.current_segment >= target_segment:
                stop_event.set()
                break

            time.sleep(0.5)
    finally:
        stop_event.set()
        recorder.stop()

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
