"""Offline canonical verifier for the frozen robot-cell benchmark."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from oscillink_safety_ops.benchmark import verify_benchmark

__all__ = ("verify_benchmark",)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path("benchmark/robot_cell_v1"),
        help="local benchmark directory",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="local repository containing the exact benchmark and generator source files",
    )
    args = parser.parse_args()
    result = verify_benchmark(args.root, repository_root=args.repository_root)
    print(json.dumps(asdict(result), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
