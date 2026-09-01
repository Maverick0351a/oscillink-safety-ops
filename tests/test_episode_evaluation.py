from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from oscillink_safety_ops.audit import evaluate_recorded_episode
from oscillink_safety_ops.cli import run
from oscillink_safety_ops.domain import (
    FindingState,
    PhysicalIntelligenceEvidenceEnvelope,
    RecordedEpisodeEvidence,
    SafetyEvidencePacket,
)
from scripts.export_schemas import SCHEMAS

ROOT = Path(__file__).parent / "fixtures" / "synthetic_press"
SHA = "sha256:" + "a" * 64


def _packet() -> SafetyEvidencePacket:
    return SafetyEvidencePacket.model_validate_json(
        (ROOT / "safety-evidence-packet-v1.json").read_text(encoding="utf-8")
    )


def _episode() -> RecordedEpisodeEvidence:
    return RecordedEpisodeEvidence(
        episode_id="episode-synthetic-001",
        task_id="task-maintenance-001",
        asset_model="SYN-PRESS-7",
        asset_serial="SP7-0042",
        observed_evidence_keys=("energy_isolation.main_disconnect",),
        source_record_sha256=(SHA,),
    )


def _envelope() -> PhysicalIntelligenceEvidenceEnvelope:
    return PhysicalIntelligenceEvidenceEnvelope(
        platform_id="synthetic-recorder",
        platform_version="1",
        adapter_id="offline-episode-json-reader",
        adapter_version="1",
        adapter_config_sha256=SHA,
        artifact_type="recorded_episode_evidence",
        source_ref="episode.json",
        source_revision="episode-revision-1",
        content_sha256=SHA,
        observed_at=datetime(2026, 9, 1, tzinfo=UTC),
        asset_ids=("asset:SYN-PRESS-7:SP7-0042",),
        task_id="task-maintenance-001",
        episode_id="episode-synthetic-001",
        payload_ref="episode.json",
    )


def test_offline_episode_evaluation_emits_cited_evidence_states_only() -> None:
    report = evaluate_recorded_episode(_packet(), _episode(), envelope=_envelope())

    by_id = {item.constraint_id: item.state for item in report.findings}
    assert by_id["m1-isolation-evidence"] is FindingState.MATCHED
    assert by_id["m2-verification-evidence"] is FindingState.MISSING_EVIDENCE
    assert by_id["s1-unreadable-role"] is FindingState.UNREADABLE
    assert by_id["s2-source-conflict"] is FindingState.SOURCE_CONFLICT
    assert by_id["s3-stale-revision"] is FindingState.REVISION_STALE
    assert report.evaluation_state == "evidence_findings_only"
    assert report.compliance_state == "no_conclusion"
    assert report.operational_authority == "none"


def test_episode_evaluation_rejects_wrong_task_or_episode_binding() -> None:
    with pytest.raises(ValueError, match="exact recorded episode"):
        evaluate_recorded_episode(
            _packet(),
            _episode(),
            envelope=_envelope().model_copy(update={"episode_id": "episode-other"}),
        )


def test_episode_evaluation_schema_exposes_no_action_surface() -> None:
    schema_text = str(SCHEMAS["episode-evaluation-report.schema.json"]).lower()

    assert "operational_authority" in schema_text
    for forbidden in ("command", "permit", "approved_to_operate", "compliant"):
        assert forbidden not in schema_text


def test_offline_episode_cli_verifies_payload_and_emits_report(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        run(
            [
                "episode-evaluate",
                "--packet",
                str(ROOT / "safety-evidence-packet-v1.json"),
                "--episode",
                str(ROOT / "episode.json"),
                "--envelope",
                str(ROOT / "episode-envelope.json"),
                "--root",
                str(ROOT),
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["episode_id"] == "episode-synthetic-001"
    assert report["evaluation_state"] == "evidence_findings_only"
    assert report["operational_authority"] == "none"
