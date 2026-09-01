from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture_root = root / "tests" / "fixtures" / "synthetic_press"
memory = json.loads((fixture_root / "packet.json").read_text(encoding="utf-8"))
packet = {
    "schema_version": 1,
    "packet_id": memory["packet_id"],
    "packet_revision": "synthetic-v1",
    "context": {
        "jurisdiction": "synthetic-jurisdiction",
        "site": "synthetic-site",
        "asset_model": "SYN-PRESS-7",
        "asset_serial": "SP7-0042",
        "task_id": "task-maintenance-001",
        "task_phase": "pre-work-offline-review",
        "role": "synthetic-maintenance-role",
        "applicability_unknowns": ["worker_authorization_record"],
    },
    "memory": memory,
    "unresolved_evidence": [
        {
            "issue_id": "issue:unreadable-role",
            "state": "unreadable",
            "statement": "The responsible-role source field remains unreadable.",
            "related_source_ids": ["site-procedure-rev1"],
            "related_constraint_ids": ["s1-unreadable-role"],
        },
        {
            "issue_id": "issue:source-conflict",
            "state": "source_conflict",
            "statement": "The energy-classification conflict remains unresolved.",
            "related_source_ids": ["site-procedure-rev1", "manual-rev2"],
            "related_constraint_ids": ["s2-source-conflict", "m1-isolation-evidence"],
        },
        {
            "issue_id": "issue:stale-procedure",
            "state": "revision_stale",
            "statement": "A cited site-procedure revision has a recorded successor.",
            "related_source_ids": ["site-procedure-rev1", "site-procedure-rev2"],
            "related_constraint_ids": ["s3-stale-revision"],
        },
    ],
    "packet_config_sha256": "sha256:" + "f" * 64,
    "generated_at": "2026-09-01T00:00:00Z",
    "packet_state": "reviewable_evidence_packet",
    "interpretation_authority": "none",
    "applicability_authority": "none",
    "compliance_state": "no_conclusion",
    "operational_authority": "none",
}
(fixture_root / "safety-evidence-packet-v1.json").write_text(
    json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
)
