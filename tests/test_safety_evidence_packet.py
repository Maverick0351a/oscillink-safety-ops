from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.domain import SafetyEvidencePacket
from scripts.export_schemas import SCHEMAS

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_press" / "safety-evidence-packet-v1.json"


def test_frozen_safety_evidence_packet_v1_preserves_context_unknowns_and_issues() -> None:
    packet = SafetyEvidencePacket.model_validate_json(FIXTURE.read_text(encoding="utf-8"))

    assert packet.schema_version == 1
    assert packet.context.asset_model == "SYN-PRESS-7"
    assert packet.context.asset_serial == "SP7-0042"
    assert packet.context.applicability_unknowns == ("worker_authorization_record",)
    assert {issue.state for issue in packet.unresolved_evidence} == {
        "revision_stale",
        "source_conflict",
        "unreadable",
    }
    assert packet.packet_state == "reviewable_evidence_packet"
    assert packet.compliance_state == "no_conclusion"
    assert packet.operational_authority == "none"
    assert packet.content_sha256().startswith("sha256:")


def test_safety_evidence_packet_rejects_issue_references_outside_exact_memory() -> None:
    payload = SafetyEvidencePacket.model_validate_json(
        FIXTURE.read_text(encoding="utf-8")
    ).model_dump()
    issue = payload["unresolved_evidence"][0]
    issue["related_source_ids"] = ("source:not-in-packet",)

    with pytest.raises(ValidationError, match="unknown source"):
        SafetyEvidencePacket.model_validate(payload)


def test_safety_evidence_packet_schema_fixes_all_authority_boundaries() -> None:
    schema = SCHEMAS["safety-evidence-packet-v1.schema.json"]

    assert schema["additionalProperties"] is False
    assert schema["properties"]["packet_state"]["const"] == "reviewable_evidence_packet"
    assert schema["properties"]["compliance_state"]["const"] == "no_conclusion"
    assert schema["properties"]["operational_authority"]["const"] == "none"
