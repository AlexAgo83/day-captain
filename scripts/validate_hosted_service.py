#!/usr/bin/env python3
"""Validate a hosted Day Captain service from shell automation."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["validate-hosted-service", *sys.argv[1:]]))
