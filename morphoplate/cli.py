"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from morphoplate.config import Settings
from morphoplate.pipeline import VideoPipeline
from morphoplate.watchlist import Watchlist


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="morphoplate",
        description="ALPR with morphological enhancement and watchlist overlays",
    )
    parser.add_argument(
        "video",
        type=Path,
        help="Path to input video (e.g. data/test1.mp4)",
    )
    parser.add_argument(
        "-w",
        "--watchlist",
        type=Path,
        default=None,
        help="Text file with one plate per line (see config/watchlist.example.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Optional output video path (mp4)",
    )
    parser.add_argument(
        "--model",
        default="yolo-v9-s-608-license-plate-end2end",
        help="fast-alpr detector model id",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable OpenCV preview window (useful with --output)",
    )
    return parser


def load_watchlist(args: argparse.Namespace) -> Watchlist:
    if args.watchlist is not None:
        return Watchlist.from_file(args.watchlist)
    return Watchlist.from_iterable([])


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.video.exists():
        print(f"Error: video not found: {args.video}", file=sys.stderr)
        return 1

    settings = Settings(
        video_path=args.video,
        watchlist_path=args.watchlist,
        detector_model=args.model,
        show_window=not args.no_display,
        output_path=args.output,
    )

    try:
        watchlist = load_watchlist(args)
        pipeline = VideoPipeline(settings, watchlist)
        pipeline.run()
    except (RuntimeError, FileNotFoundError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
