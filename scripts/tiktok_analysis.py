#!/usr/bin/env python3
"""Analyze local video files for TikTok readiness.

Inspects one or more video files with ffprobe and reports whether each
one meets TikTok's baseline publishing requirements, most importantly
that the video is in vertical (portrait) format.

Usage:
    tiktok_analysis.py VIDEO [VIDEO ...]
    tiktok_analysis.py --dir ./videos
    tiktok_analysis.py --dir ./videos --json report.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
import subprocess
import sys
from pathlib import Path

# TikTok publishing guidelines (as of 2026).
TARGET_ASPECT_RATIO = 9 / 16  # width / height
ASPECT_RATIO_TOLERANCE = 0.02
MIN_RESOLUTION_HEIGHT = 960
RECOMMENDED_RESOLUTION = (1080, 1920)
MIN_DURATION_SECONDS = 3.0
MAX_DURATION_SECONDS = 600.0
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}


@dataclasses.dataclass
class VideoReport:
    path: str
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    fps: float | None = None
    codec: str | None = None
    errors: list[str] = dataclasses.field(default_factory=list)
    warnings: list[str] = dataclasses.field(default_factory=list)

    @property
    def is_vertical(self) -> bool:
        return bool(self.width and self.height and self.height > self.width)

    @property
    def passed(self) -> bool:
        return not self.errors


def probe_video(path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,codec_name",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def parse_frame_rate(rate: str | None) -> float | None:
    if not rate:
        return None
    if "/" in rate:
        num, _, den = rate.partition("/")
        try:
            den_f = float(den)
            return float(num) / den_f if den_f else None
        except ValueError:
            return None
    try:
        return float(rate)
    except ValueError:
        return None


def analyze_video(path: Path) -> VideoReport:
    report = VideoReport(path=str(path))

    if not path.exists():
        report.errors.append("File not found")
        return report

    try:
        data = probe_video(path)
    except FileNotFoundError:
        report.errors.append("ffprobe is not installed or not on PATH")
        return report
    except subprocess.CalledProcessError as exc:
        report.errors.append(f"ffprobe failed: {exc.stderr.strip()}")
        return report

    streams = data.get("streams") or []
    if not streams:
        report.errors.append("No video stream found")
        return report

    stream = streams[0]
    fmt = data.get("format") or {}

    report.width = stream.get("width")
    report.height = stream.get("height")
    report.fps = parse_frame_rate(stream.get("r_frame_rate"))
    report.codec = stream.get("codec_name")
    duration = fmt.get("duration")
    report.duration = float(duration) if duration is not None else None

    if report.width is None or report.height is None:
        report.errors.append("Could not determine video dimensions")
        return report

    if not report.is_vertical:
        report.errors.append(
            f"Video is not vertical ({report.width}x{report.height}); "
            "TikTok requires height > width"
        )
    else:
        ratio = report.width / report.height
        if abs(ratio - TARGET_ASPECT_RATIO) > ASPECT_RATIO_TOLERANCE:
            report.warnings.append(
                f"Aspect ratio {report.width}:{report.height} deviates from "
                "the recommended 9:16"
            )
        if report.height < MIN_RESOLUTION_HEIGHT:
            report.warnings.append(
                f"Height {report.height}px is below the recommended minimum "
                f"of {MIN_RESOLUTION_HEIGHT}px (target {RECOMMENDED_RESOLUTION[0]}x"
                f"{RECOMMENDED_RESOLUTION[1]})"
            )

    if report.duration is not None:
        if report.duration < MIN_DURATION_SECONDS:
            report.errors.append(
                f"Duration {report.duration:.1f}s is below the {MIN_DURATION_SECONDS:.0f}s minimum"
            )
        elif report.duration > MAX_DURATION_SECONDS:
            report.errors.append(
                f"Duration {report.duration:.1f}s exceeds the {MAX_DURATION_SECONDS:.0f}s maximum"
            )

    return report


def collect_paths(files: list[str], directory: str | None) -> list[Path]:
    paths: list[Path] = [Path(f) for f in files]
    if directory:
        dir_path = Path(directory)
        paths.extend(
            sorted(p for p in dir_path.rglob("*") if p.suffix.lower() in VIDEO_EXTENSIONS)
        )
    return paths


def print_report(report: VideoReport) -> None:
    status = "PASS" if report.passed else "FAIL"
    print(f"[{status}] {report.path}")
    if report.width and report.height:
        orientation = "vertical" if report.is_vertical else "horizontal/square"
        print(f"  {report.width}x{report.height} ({orientation})", end="")
        if report.fps:
            print(f", {report.fps:.2f} fps", end="")
        if report.duration is not None:
            print(f", {report.duration:.1f}s", end="")
        if report.codec:
            print(f", codec={report.codec}", end="")
        print()
    for error in report.errors:
        print(f"  ERROR: {error}")
    for warning in report.warnings:
        print(f"  WARNING: {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="Video files to analyze")
    parser.add_argument("--dir", help="Directory to scan recursively for video files")
    parser.add_argument("--json", help="Write the full report as JSON to this path")
    args = parser.parse_args(argv)

    paths = collect_paths(args.files, args.dir)
    if not paths:
        parser.error("No video files given (pass files or --dir)")

    if shutil.which("ffprobe") is None:
        print("ERROR: ffprobe is required but was not found on PATH.", file=sys.stderr)
        print("Install ffmpeg (which provides ffprobe) and try again.", file=sys.stderr)
        return 2

    reports = [analyze_video(path) for path in paths]

    for report in reports:
        print_report(report)
        print()

    passed = sum(1 for r in reports if r.passed)
    print(f"{passed}/{len(reports)} videos passed TikTok format checks")

    if args.json:
        Path(args.json).write_text(
            json.dumps([dataclasses.asdict(r) for r in reports], indent=2)
        )
        print(f"Wrote JSON report to {args.json}")

    return 0 if passed == len(reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
