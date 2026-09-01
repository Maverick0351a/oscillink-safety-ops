"""Validate a private hidden-evaluation bank without disclosing task content."""

from __future__ import annotations

import argparse
from pathlib import Path

from oscillink_safety_ops.evaluation import validate_hidden_task_bank

FROZEN_CLASS_COUNTS = {
    "abstention": 2,
    "authority": 2,
    "conflict": 2,
    "extraction": 2,
    "lineage": 2,
    "staleness": 2,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bank", type=Path)
    args = parser.parse_args()
    result = validate_hidden_task_bank(args.bank, expected_class_counts=FROZEN_CLASS_COUNTS)
    print(result.model_dump_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
