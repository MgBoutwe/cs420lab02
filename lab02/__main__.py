from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .summarizer import summarize_directory, format_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="log-summarizer",
        description="Read .log files from a directory and print a summary report.",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing .log files",
    )
    args = parser.parse_args(argv)

    try:
        summary = summarize_directory(args.directory)
        print(format_report(args.directory, summary))
        return 0
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
