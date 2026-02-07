from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Iterable, Optional

# Example line:
# 2026-02-06 13:45:01 [INFO] Something happened
LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[(?P<level>INFO|WARNING|ERROR)\]\s+(?P<msg>.*)$"
)

TS_FORMAT = "%Y-%m-%d %H:%M:%S"
LEVELS = ("INFO", "WARNING", "ERROR")


@dataclass
class Summary:
    files_processed: int = 0
    lines_seen: int = 0
    lines_matched: int = 0
    lines_skipped: int = 0
    info: int = 0
    warning: int = 0
    error: int = 0
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None

    def update_time_bounds(self, ts: datetime) -> None:
        if self.earliest is None or ts < self.earliest:
            self.earliest = ts
        if self.latest is None or ts > self.latest:
            self.latest = ts

    def bump_level(self, level: str) -> None:
        if level == "INFO":
            self.info += 1
        elif level == "WARNING":
            self.warning += 1
        elif level == "ERROR":
            self.error += 1


def iter_log_files(directory: Path) -> Iterable[Path]:
    # Only .log files in that directory (not recursive). Adjust if you want recursion.
    yield from sorted(p for p in directory.iterdir() if p.is_file() and p.suffix == ".log")


def parse_line(line: str) -> Optional[tuple[datetime, str]]:
    """
    Returns (timestamp, level) if the line matches; otherwise None.
    """
    m = LINE_RE.match(line.rstrip("\n"))
    if not m:
        return None
    ts = datetime.strptime(m.group("ts"), TS_FORMAT)
    level = m.group("level")
    return ts, level


def summarize_directory(directory: Path) -> Summary:
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    summary = Summary()

    for log_path in iter_log_files(directory):
        summary.files_processed += 1

        # Read robustly: allow odd encodings without crashing.
        with log_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                summary.lines_seen += 1
                parsed = parse_line(line)
                if parsed is None:
                    summary.lines_skipped += 1
                    continue

                ts, level = parsed
                summary.lines_matched += 1
                summary.bump_level(level)
                summary.update_time_bounds(ts)

    return summary


def format_report(directory: Path, summary: Summary) -> str:
    earliest = summary.earliest.strftime(TS_FORMAT) if summary.earliest else "N/A"
    latest = summary.latest.strftime(TS_FORMAT) if summary.latest else "N/A"

    # Nice aligned output
    return (
        "\n"
        "==================== Log Summary ====================\n"
        f"Directory:          {directory.resolve()}\n"
        f"Files processed:    {summary.files_processed}\n"
        "-----------------------------------------------------\n"
        f"Lines seen:         {summary.lines_seen}\n"
        f"Lines matched:      {summary.lines_matched}\n"
        f"Lines skipped:      {summary.lines_skipped}\n"
        "-----------------------------------------------------\n"
        "Log Levels:\n"
        f"  INFO:            {summary.info}\n"
        f"  WARNING:         {summary.warning}\n"
        f"  ERROR:           {summary.error}\n"
        "-----------------------------------------------------\n"
        f"Earliest timestamp: {earliest}\n"
        f"Latest timestamp:   {latest}\n"
        "=====================================================\n"
    )
