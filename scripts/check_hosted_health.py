#!/usr/bin/env python3
"""Check or warm a hosted Day Captain service from shell automation."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["check-hosted-health", *sys.argv[1:]]))
