"""Command-line interface for deterministic offline audits."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from .audit import audit_plan
from .governance import build_operational_impact_report
from .io import (
    FixtureIntegrityError,
    load_envelope,
    load_operational_jsonl,
    load_operational_review_ledger,
    load_packet,
    load_plan,
    sha256_file,
    store_operational_export,
    verify_envelope_payload,
    verify_manifest,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="safety-ops")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    audit = subparsers.add_parser("audit", help="audit a proposed plan offline")
    audit.add_argument("--packet", type=Path, required=True)
    audit.add_argument("--plan", type=Path, required=True)
    audit.add_argument("--manifest", type=Path, required=True)
    audit.add_argument("--envelope", type=Path, required=True)
    audit.add_argument("--root", type=Path, required=True)
    envelope = subparsers.add_parser("envelope", help="work with evidence envelopes")
    envelope_actions = envelope.add_subparsers(dest="envelope_action", required=True)
    validate = envelope_actions.add_parser("validate", help="validate a read-only envelope")
    validate.add_argument("--envelope", type=Path, required=True)
    validate.add_argument("--root", type=Path, required=True)
    operational = subparsers.add_parser("operational", help="work with operational evidence")
    operational_actions = operational.add_subparsers(dest="operational_action", required=True)
    normalize = operational_actions.add_parser(
        "normalize", help="normalize and store a read-only JSONL export"
    )
    normalize.add_argument("--input", type=Path, required=True)
    normalize.add_argument("--batch-id", required=True)
    normalize.add_argument("--source-revision", required=True)
    normalize.add_argument("--adapter-config-sha256", required=True)
    normalize.add_argument("--store-root", type=Path, required=True)
    review_validate = operational_actions.add_parser(
        "review-validate", help="validate a bounded external review ledger"
    )
    review_validate.add_argument("--ledger", type=Path, required=True)
    impact = operational_actions.add_parser(
        "impact", help="assess reviewed candidates against a current JSONL export"
    )
    impact.add_argument("--ledger", type=Path, required=True)
    impact.add_argument("--current-input", type=Path, required=True)
    impact.add_argument("--batch-id", required=True)
    impact.add_argument("--source-revision", required=True)
    impact.add_argument("--adapter-config-sha256", required=True)
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.subcommand == "envelope":
        envelope = load_envelope(args.envelope)
        verify_envelope_payload(envelope, root=args.root)
        print(envelope.model_dump_json(indent=2))
        return 0
    if args.subcommand == "operational":
        if args.operational_action == "review-validate":
            ledger = load_operational_review_ledger(args.ledger)
            print(ledger.model_dump_json(indent=2))
            return 0
        if args.operational_action == "impact":
            ledger = load_operational_review_ledger(args.ledger)
            current_batch = load_operational_jsonl(
                args.current_input,
                batch_id=args.batch_id,
                source_revision=args.source_revision,
                adapter_config_sha256=args.adapter_config_sha256,
            )
            impact_report = build_operational_impact_report(
                ledger,
                review_ledger_sha256=sha256_file(args.ledger),
                current_batch=current_batch,
            )
            print(impact_report.model_dump_json(indent=2))
            return 0
        batch = load_operational_jsonl(
            args.input,
            batch_id=args.batch_id,
            source_revision=args.source_revision,
            adapter_config_sha256=args.adapter_config_sha256,
        )
        artifact = store_operational_export(args.input, root=args.store_root)
        result = {
            "schema_version": 1,
            "batch": batch.model_dump(mode="json"),
            "stored_artifact": asdict(artifact),
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    packet = load_packet(args.packet)
    verified_hashes = verify_manifest(args.manifest)
    missing = {source.sha256 for source in packet.sources} - verified_hashes
    if missing:
        raise FixtureIntegrityError("packet source hash is not pinned by manifest")
    plan = load_plan(args.plan)
    envelope = load_envelope(args.envelope)
    verify_envelope_payload(envelope, root=args.root)
    report = audit_plan(packet, plan, envelope=envelope)
    print(report.model_dump_json(indent=2))
    return 0


def main() -> None:
    raise SystemExit(run())
