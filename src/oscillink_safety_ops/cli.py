"""Command-line interface for deterministic offline audits."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from .audit import audit_plan, evaluate_recorded_episode
from .benchmark import verify_benchmark
from .governance import build_operational_impact_report
from .io import (
    FixtureIntegrityError,
    load_envelope,
    load_operational_jsonl,
    load_operational_review_ledger,
    load_packet,
    load_regulatory_section_snapshot,
    load_regulatory_source_evidence,
    load_safety_evidence_packet,
    load_verified_envelope_episode,
    load_verified_envelope_plan,
    sha256_file,
    store_operational_export,
    verify_envelope_payload,
    verify_manifest,
)
from .regulatory_artifacts import (
    compare_cfr_section_snapshots,
    extract_regulatory_section_xml,
    verify_regulatory_artifact,
)
from .runtime.outputs import publish_local_output
from .runtime.replay import replay_closed_files


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="safety-ops")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    audit = subparsers.add_parser("audit", help="audit a proposed plan offline")
    audit.add_argument("--packet", type=Path, required=True)
    audit.add_argument("--plan", type=Path, required=True)
    audit.add_argument("--manifest", type=Path, required=True)
    audit.add_argument("--envelope", type=Path, required=True)
    audit.add_argument("--root", type=Path, required=True)
    episode_evaluate = subparsers.add_parser(
        "episode-evaluate", help="evaluate recorded episode evidence offline"
    )
    episode_evaluate.add_argument("--packet", type=Path, required=True)
    episode_evaluate.add_argument("--episode", type=Path, required=True)
    episode_evaluate.add_argument("--envelope", type=Path, required=True)
    episode_evaluate.add_argument("--root", type=Path, required=True)
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
    regulatory = subparsers.add_parser("regulatory", help="work with regulatory source evidence")
    regulatory_actions = regulatory.add_subparsers(dest="regulatory_action", required=True)
    artifact_verify = regulatory_actions.add_parser(
        "artifact-verify", help="verify exact bounded regulatory artifact bytes"
    )
    artifact_verify.add_argument("--evidence", type=Path, required=True)
    artifact_verify.add_argument("--artifact-ref", required=True)
    artifact_verify.add_argument("--root", type=Path, required=True)
    section_extract = regulatory_actions.add_parser(
        "section-extract", help="extract one source-bound regulatory XML section candidate"
    )
    section_extract.add_argument("--evidence", type=Path, required=True)
    section_extract.add_argument("--artifact-ref", required=True)
    section_extract.add_argument("--root", type=Path, required=True)
    section_extract.add_argument("--citation", required=True)
    section_extract.add_argument("--parser-config-sha256", required=True)
    section_compare = regulatory_actions.add_parser(
        "section-compare", help="compare annual-CFR and dated-eCFR section candidates"
    )
    section_compare.add_argument("--annual", type=Path, required=True)
    section_compare.add_argument("--ecfr", type=Path, required=True)
    runtime = subparsers.add_parser("runtime", help="run deterministic closed-file simulation")
    runtime_actions = runtime.add_subparsers(dest="runtime_action", required=True)
    replay = runtime_actions.add_parser("replay", help="replay signed configuration and JSONL")
    replay.add_argument("--configuration", type=Path, required=True)
    replay.add_argument("--input", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument(
        "--authority",
        type=Path,
        help="public authority file (defaults to authority.json beside configuration)",
    )
    benchmark = subparsers.add_parser("benchmark", help="work with frozen synthetic benchmarks")
    benchmark_actions = benchmark.add_subparsers(dest="benchmark_action", required=True)
    benchmark_verify = benchmark_actions.add_parser(
        "verify", help="verify a frozen benchmark offline"
    )
    benchmark_verify.add_argument("--root", type=Path, required=True)
    benchmark_verify.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="local repository whose HEAD is bound by the benchmark manifest",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.subcommand == "benchmark":
        benchmark_verification = verify_benchmark(args.root, repository_root=args.repository_root)
        print(json.dumps(asdict(benchmark_verification), sort_keys=True, separators=(",", ":")))
        return 0
    if args.subcommand == "runtime":
        root = Path.cwd()
        authority_path = args.authority or (args.configuration.parent / "authority.json")
        runtime_result = replay_closed_files(
            root=root,
            configuration=args.configuration,
            input_path=args.input,
            authority_path=authority_path,
        )
        output_artifact = publish_local_output(
            runtime_result.canonical_bytes,
            root=root,
            relative_path=args.output,
        )
        print(json.dumps(asdict(output_artifact), default=str, sort_keys=True))
        return 0
    if args.subcommand == "episode-evaluate":
        episode_packet = load_safety_evidence_packet(args.packet)
        envelope = load_envelope(args.envelope)
        episode = load_verified_envelope_episode(
            envelope,
            root=args.root,
            requested_path=args.episode,
        )
        episode_report = evaluate_recorded_episode(episode_packet, episode, envelope=envelope)
        print(episode_report.model_dump_json(indent=2))
        return 0
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
        operational_artifact = store_operational_export(args.input, root=args.store_root)
        operational_result = {
            "schema_version": 1,
            "batch": batch.model_dump(mode="json"),
            "stored_artifact": asdict(operational_artifact),
        }
        print(json.dumps(operational_result, indent=2, sort_keys=True))
        return 0
    if args.subcommand == "regulatory":
        if args.regulatory_action == "section-compare":
            comparison = compare_cfr_section_snapshots(
                load_regulatory_section_snapshot(args.annual),
                load_regulatory_section_snapshot(args.ecfr),
            )
            print(comparison.model_dump_json(indent=2))
            return 0
        evidence = load_regulatory_source_evidence(args.evidence)
        if args.regulatory_action == "section-extract":
            snapshot = extract_regulatory_section_xml(
                evidence,
                artifact_ref=args.artifact_ref,
                root=args.root,
                citation=args.citation,
                parser_config_sha256=args.parser_config_sha256,
            )
            print(snapshot.model_dump_json(indent=2))
            return 0
        verification = verify_regulatory_artifact(
            evidence,
            artifact_ref=args.artifact_ref,
            root=args.root,
        )
        print(verification.model_dump_json(indent=2))
        return 0
    packet = load_packet(args.packet)
    verified_hashes = verify_manifest(args.manifest)
    missing = {source.sha256 for source in packet.sources} - verified_hashes
    if missing:
        raise FixtureIntegrityError("packet source hash is not pinned by manifest")
    envelope = load_envelope(args.envelope)
    plan = load_verified_envelope_plan(
        envelope,
        root=args.root,
        requested_path=args.plan,
    )
    report = audit_plan(packet, plan, envelope=envelope)
    print(report.model_dump_json(indent=2))
    return 0


def main() -> None:
    raise SystemExit(run())
