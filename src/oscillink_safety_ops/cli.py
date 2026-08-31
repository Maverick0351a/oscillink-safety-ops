"""Command-line interface for deterministic offline audits."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .audit import audit_plan
from .io import FixtureIntegrityError, load_packet, load_plan, verify_manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="safety-ops")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    audit = subparsers.add_parser("audit", help="audit a proposed plan offline")
    audit.add_argument("--packet", type=Path, required=True)
    audit.add_argument("--plan", type=Path, required=True)
    audit.add_argument("--manifest", type=Path, required=True)
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    packet = load_packet(args.packet)
    verified_hashes = verify_manifest(args.manifest)
    missing = {source.sha256 for source in packet.sources} - verified_hashes
    if missing:
        raise FixtureIntegrityError("packet source hash is not pinned by manifest")
    plan = load_plan(args.plan)
    report = audit_plan(packet, plan)
    print(report.model_dump_json(indent=2))
    return 0


def main() -> None:
    raise SystemExit(run())
