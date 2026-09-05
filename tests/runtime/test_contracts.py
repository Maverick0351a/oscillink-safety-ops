"""Strict provenance and authority-boundary runtime contract tests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import BaseModel, ValidationError

from oscillink_safety_ops.runtime import (
    ActionAcknowledgment,
    ActionRequest,
    CommandObservation,
    IncidentEvent,
    IncidentTimeline,
    PhysicalObservation,
    RecoveryEvent,
    RuntimeObservation,
    SourceHealthObservation,
    SupervisorConfiguration,
    SupervisorDecision,
    SupervisorStateRecord,
    bind_observation_bytes,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SIGNATURE = "ed25519:" + "ab" * 64


def command_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "observation_id": "command:001",
        "run_id": "run:001",
        "source_id": "production-ai:planner",
        "sequence_number": 0,
        "observed_at": NOW,
        "received_at": NOW,
        "input_sha256": SHA_A,
        "command_id": "command-id:001",
        "command_kind": "motion_requested",
        "motion_requested": True,
        "program_id": "program:synthetic",
        "frame_id": "frame:synthetic-world",
    }


def physical_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "observation_id": "physical:001",
        "run_id": "run:001",
        "source_id": "independent-zone-sensor:a",
        "sequence_number": 0,
        "observed_at": NOW,
        "received_at": NOW,
        "input_sha256": SHA_B,
        "zone_id": "zone:synthetic-protected",
        "occupancy": "clear",
        "motion_state": "stopped",
        "speed_mps": 0.0,
        "quality": "good",
        "calibration_sha256": SHA_C,
    }


def health_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "observation_id": "health:001",
        "run_id": "run:001",
        "source_id": "independent-health-monitor:a",
        "sequence_number": 0,
        "observed_at": NOW,
        "received_at": NOW,
        "input_sha256": SHA_C,
        "monitored_source_id": "independent-zone-sensor:a",
        "source_state": "healthy",
        "clock_state": "healthy",
        "last_source_sequence": 0,
    }


def configuration_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "configuration_id": "configuration:robot-cell:001",
        "revision": 1,
        "scope_id": "SCOPE-ROBOT-CELL-001",
        "valid_from": NOW,
        "valid_until": datetime(2026, 9, 4, 12, 0, tzinfo=UTC),
        "required_source_ids": (
            "independent-health-monitor:a",
            "independent-zone-sensor:a",
            "production-ai:planner",
        ),
        "max_observation_age_seconds": 0.5,
        "max_receive_delay_seconds": 0.2,
        "max_future_skew_seconds": 0.0,
        "max_correlation_delay_seconds": 0.25,
        "approved_calibration_sha256": (SHA_C,),
        "max_speed_mps": 1.0,
        "max_acceleration_mps2": 2.0,
        "signer_id": "safety-config-signer:001",
        "signature_algorithm": "ed25519",
        "signature": SIGNATURE,
        "authority_state": "externally_signed_configuration",
        "operational_authority": "simulated_evaluation_only",
    }


def decision_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "decision_id": "decision:001",
        "run_id": "run:001",
        "evaluated_at": NOW,
        "supervisor_state": "monitoring_degraded",
        "action": "inhibit_request",
        "first_out_reason": "source_state_unverifiable",
        "reason_codes": ("source_state_unverifiable",),
        "configuration_sha256": SHA_A,
        "input_sha256": (SHA_B, SHA_C),
        "authority_state": "deterministic_supervisor_record",
        "operational_authority": "simulated_request_only",
    }


def state_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "state_id": "state:001",
        "run_id": "run:001",
        "evaluated_at": NOW,
        "supervisor_state": "initializing",
        "latched": False,
        "first_out_reason": "initializing",
        "reason_codes": ("initializing",),
        "configuration_sha256": SHA_A,
        "input_sha256": (SHA_B,),
    }


def recovery_event_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_id": "recovery:001",
        "run_id": "run:001",
        "observed_at": NOW,
        "event_kind": "reset",
        "actor_domain": "independent_safety_authority",
        "authorization_state": "externally_authorized",
        "configuration_sha256": SHA_A,
        "input_sha256": SHA_B,
    }


def request_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "request_id": "action-request:001",
        "run_id": "run:001",
        "created_at": NOW,
        "action": "inhibit_request",
        "decision_sha256": SHA_A,
        "configuration_sha256": SHA_B,
        "input_sha256": (SHA_C,),
        "delivery_mode": "local_closed_file_simulation",
        "authority_state": "simulated_request_artifact",
        "operational_authority": "none",
    }


def acknowledgment_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "acknowledgment_id": "ack:001",
        "run_id": "run:001",
        "observed_at": NOW,
        "request_sha256": SHA_A,
        "configuration_sha256": SHA_B,
        "input_sha256": (SHA_C,),
        "source_domain": "simulated_fixture",
        "status": "received_by_simulated_fixture",
        "authority_state": "untrusted_observation",
        "stopping_claim": "not_established",
        "reset_authority": "none",
        "operational_authority": "none",
    }


@pytest.mark.parametrize(
    ("model", "factory"),
    (
        (CommandObservation, command_data),
        (PhysicalObservation, physical_data),
        (SourceHealthObservation, health_data),
        (SupervisorConfiguration, configuration_data),
        (SupervisorDecision, decision_data),
        (SupervisorStateRecord, state_data),
        (RecoveryEvent, recovery_event_data),
        (ActionRequest, request_data),
        (ActionAcknowledgment, acknowledgment_data),
    ),
)
def test_runtime_contracts_are_strict_frozen_and_reject_extra_fields(
    model: type[BaseModel], factory: Callable[[], dict[str, object]]
) -> None:
    data = factory()
    instance = model.model_validate(data)

    with pytest.raises(ValidationError):
        model.model_validate({**data, "reset": True})
    with pytest.raises(ValidationError):
        setattr(instance, next(iter(data)), "changed")


@pytest.mark.parametrize(
    "changes",
    (
        {"active_request_sha256": SHA_C, "output_state": "request_pending"},
        {"supervisor_state": "intervention_latched", "latched": True},
        {
            "supervisor_state": "stopped_unverified",
            "latched": True,
            "active_request_sha256": SHA_C,
            "output_state": "request_pending",
        },
        {
            "supervisor_state": "reset_ready",
            "latched": True,
            "active_request_sha256": SHA_C,
            "output_state": "unresolved",
        },
        {"fresh_start_required": True},
    ),
)
def test_supervisor_state_rejects_impossible_request_and_recovery_combinations(
    changes: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        SupervisorStateRecord.model_validate({**state_data(), **changes})


@pytest.mark.parametrize("factory", (command_data, physical_data, health_data))
def test_production_facing_observations_reject_administrative_authority(
    factory: Callable[[], dict[str, object]],
) -> None:
    data = factory()
    models: dict[Callable[[], dict[str, object]], type[RuntimeObservation]] = {
        command_data: CommandObservation,
        physical_data: PhysicalObservation,
        health_data: SourceHealthObservation,
    }
    model = models[factory]

    for forbidden in (
        "policy",
        "threshold",
        "configuration",
        "reset",
        "rearm",
        "admin",
        "suppress_evidence",
        "scope_override",
    ):
        with pytest.raises(ValidationError):
            model.model_validate({**data, forbidden: "untrusted"})

    instance = model.model_validate(data)
    assert instance.authority_state == "untrusted_observation"
    assert instance.configuration_authority == "none"
    assert instance.reset_authority == "none"
    assert instance.output_authority == "none"
    assert instance.evidence_suppression_authority == "none"


@pytest.mark.parametrize(
    ("model", "factory", "field"),
    (
        (CommandObservation, command_data, "sequence_number"),
        (PhysicalObservation, physical_data, "sequence_number"),
        (SourceHealthObservation, health_data, "last_source_sequence"),
        (SupervisorConfiguration, configuration_data, "revision"),
    ),
)
def test_booleans_are_not_numbers(
    model: type[BaseModel], factory: Callable[[], dict[str, object]], field: str
) -> None:
    data = factory()
    data[field] = True

    with pytest.raises(ValidationError):
        model.model_validate(data)


@pytest.mark.parametrize("value", (float("nan"), float("inf"), float("-inf"), True))
def test_physical_numeric_values_must_be_finite_real_numbers(value: object) -> None:
    data = physical_data()
    data["speed_mps"] = value

    with pytest.raises(ValidationError):
        PhysicalObservation.model_validate(data)


def test_physical_command_attribution_identity_and_sequence_are_atomic() -> None:
    for field, value in (
        ("attributed_command_id", "command-id:0"),
        ("attributed_command_sequence", 0),
    ):
        data = physical_data()
        data[field] = value
        with pytest.raises(ValidationError, match="supplied together"):
            PhysicalObservation.model_validate(data)


@pytest.mark.parametrize("factory", (command_data, physical_data, health_data))
@pytest.mark.parametrize("field", ("observed_at", "received_at"))
def test_observation_timestamps_must_be_timezone_aware(
    factory: Callable[[], dict[str, object]], field: str
) -> None:
    data = factory()
    data[field] = NOW.replace(tzinfo=None)
    models: dict[Callable[[], dict[str, object]], type[RuntimeObservation]] = {
        command_data: CommandObservation,
        physical_data: PhysicalObservation,
        health_data: SourceHealthObservation,
    }
    model = models[factory]

    with pytest.raises(ValidationError):
        model.model_validate(data)


@pytest.mark.parametrize("field", ("valid_from", "valid_until"))
def test_configuration_timestamps_must_be_timezone_aware(field: str) -> None:
    data = configuration_data()
    data[field] = NOW.replace(tzinfo=None)

    with pytest.raises(ValidationError):
        SupervisorConfiguration.model_validate(data)


def test_approved_calibration_hashes_must_be_nonempty_unique_and_sorted() -> None:
    for value in ((), (SHA_C, SHA_C), (SHA_C, SHA_A)):
        data = configuration_data()
        data["approved_calibration_sha256"] = value
        with pytest.raises(ValidationError):
            SupervisorConfiguration.model_validate(data)


def test_supervisor_state_rejects_malformed_attribution_history() -> None:
    command = {
        "schema_version": 1,
        "command_id": "command-id:0",
        "sequence_number": 0,
        "observed_at": NOW,
        "motion_requested": True,
        "input_sha256": SHA_A,
        "operational_authority": "none",
    }
    for history, consumed in (
        ((command, command), ()),
        ((command,), ("command-id:missing:sequence:0",)),
    ):
        data = state_data()
        data["command_history"] = history
        data["consumed_command_attributions"] = consumed
        with pytest.raises(ValidationError):
            SupervisorStateRecord.model_validate(data)


@pytest.mark.parametrize(
    ("model", "factory", "field"),
    (
        (CommandObservation, command_data, "input_sha256"),
        (PhysicalObservation, physical_data, "calibration_sha256"),
        (SupervisorDecision, decision_data, "configuration_sha256"),
        (ActionRequest, request_data, "decision_sha256"),
        (ActionAcknowledgment, acknowledgment_data, "request_sha256"),
    ),
)
@pytest.mark.parametrize("malformed", ("a" * 64, "sha256:ABC", "sha1:" + "a" * 40))
def test_hashes_require_prefixed_lowercase_sha256(
    model: type[object], factory: object, field: str, malformed: str
) -> None:
    data = factory()  # type: ignore[operator]
    data[field] = malformed

    with pytest.raises(ValidationError):
        model.model_validate(data)  # type: ignore[attr-defined]


def test_configuration_rejects_invalid_chronology_duplicate_sources_and_thresholds() -> None:
    data = configuration_data()
    data["valid_until"] = NOW
    with pytest.raises(ValidationError, match="valid_until"):
        SupervisorConfiguration.model_validate(data)

    data = configuration_data()
    data["required_source_ids"] = ("production-ai:planner", "production-ai:planner")
    with pytest.raises(ValidationError, match="duplicate"):
        SupervisorConfiguration.model_validate(data)

    for field in (
        "max_observation_age_seconds",
        "max_receive_delay_seconds",
        "max_future_skew_seconds",
        "max_correlation_delay_seconds",
        "approved_calibration_sha256",
        "max_speed_mps",
        "max_acceleration_mps2",
    ):
        data = configuration_data()
        data[field] = float("inf")
        with pytest.raises(ValidationError):
            SupervisorConfiguration.model_validate(data)


def test_provenance_hash_collections_are_nonempty_unique_and_sorted() -> None:
    for model, factory in (
        (SupervisorDecision, decision_data),
        (ActionRequest, request_data),
        (ActionAcknowledgment, acknowledgment_data),
    ):
        data = factory()
        data["input_sha256"] = ()
        with pytest.raises(ValidationError, match="input_sha256"):
            model.model_validate(data)

        data = factory()
        data["input_sha256"] = (SHA_C, SHA_C)
        with pytest.raises(ValidationError, match="duplicate"):
            model.model_validate(data)

        data = factory()
        data["input_sha256"] = (SHA_C, SHA_B)
        with pytest.raises(ValidationError, match="sorted"):
            model.model_validate(data)


def test_incident_timeline_binds_ordered_events_to_exact_provenance() -> None:
    event_a = IncidentEvent(
        event_id="event:001",
        occurred_at=NOW,
        event_kind="decision_recorded",
        record_sha256=SHA_A,
        summary="Synthetic decision recorded; no physical stop claim.",
    )
    event_b = IncidentEvent(
        event_id="event:002",
        occurred_at=datetime(2026, 9, 3, 12, 0, 1, tzinfo=UTC),
        event_kind="request_recorded",
        record_sha256=SHA_B,
        summary="Local closed-file request recorded.",
    )
    timeline = IncidentTimeline(
        timeline_id="timeline:001",
        run_id="run:001",
        created_at=event_b.occurred_at,
        configuration_sha256=SHA_A,
        input_sha256=(SHA_B, SHA_C),
        decision_sha256=(SHA_A,),
        request_sha256=(SHA_B,),
        events=(event_a, event_b),
    )

    assert timeline.operational_authority == "none"
    with pytest.raises(ValidationError, match="chronological"):
        IncidentTimeline(
            timeline_id="timeline:001",
            run_id="run:001",
            created_at=event_b.occurred_at,
            configuration_sha256=SHA_A,
            input_sha256=(SHA_B, SHA_C),
            decision_sha256=(SHA_A,),
            request_sha256=(SHA_B,),
            events=(event_b, event_a),
        )


def test_acknowledgment_cannot_claim_stopping_or_reset_authority() -> None:
    for field, value in (("stopping_claim", "stopped"), ("reset_authority", "granted")):
        data = acknowledgment_data()
        data[field] = value
        with pytest.raises(ValidationError):
            ActionAcknowledgment.model_validate(data)


def test_untrusted_observation_bytes_are_hash_bound_by_the_trusted_boundary() -> None:
    data = command_data()
    del data["input_sha256"]
    data["observed_at"] = NOW.isoformat()
    data["received_at"] = NOW.isoformat()
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()

    observation = bind_observation_bytes(raw, CommandObservation)

    assert observation.input_sha256 == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert observation.authority_state == "untrusted_observation"


def test_untrusted_observation_cannot_supply_its_own_byte_hash() -> None:
    raw = json.dumps(command_data(), default=str).encode()

    with pytest.raises(ValueError, match="input_sha256 is reserved"):
        bind_observation_bytes(raw, CommandObservation)


@pytest.mark.parametrize("raw", (b"\xff", b"{", b"[]", b'{"x":1,"x":2}'))
def test_observation_byte_boundary_rejects_malformed_input(raw: bytes) -> None:
    with pytest.raises(ValueError, match=r"UTF-8|JSON|object|duplicate"):
        bind_observation_bytes(raw, CommandObservation)


def test_observation_byte_boundary_rejects_excessive_json_nesting() -> None:
    raw = b"[" * 1100 + b"]" * 1100

    with pytest.raises(ValueError, match="malformed JSON"):
        bind_observation_bytes(raw, CommandObservation)


def test_runtime_schema_export_is_complete_canonical_and_current() -> None:
    from scripts.export_runtime_schemas import RUNTIME_SCHEMAS, render

    expected_names = {
        "action-acknowledgment.schema.json",
        "action-request.schema.json",
        "command-observation.schema.json",
        "dependency-binding.schema.json",
        "incident-timeline.schema.json",
        "physical-observation.schema.json",
        "recovery-event.schema.json",
        "shared-dependency-observation.schema.json",
        "source-health-observation.schema.json",
        "supervisor-configuration.schema.json",
        "supervisor-decision.schema.json",
        "supervisor-state-record.schema.json",
    }
    assert set(RUNTIME_SCHEMAS) == expected_names
    root = Path(__file__).resolve().parents[2] / "schemas" / "runtime"
    for name, schema in RUNTIME_SCHEMAS.items():
        actual = (root / name).read_bytes()
        assert actual == render(schema)
        assert actual.endswith(b"\n")


def test_observation_schemas_fix_untrusted_nonadministrative_authority() -> None:
    from scripts.export_runtime_schemas import RUNTIME_SCHEMAS

    for name in (
        "command-observation.schema.json",
        "physical-observation.schema.json",
        "shared-dependency-observation.schema.json",
        "source-health-observation.schema.json",
    ):
        schema = RUNTIME_SCHEMAS[name]
        properties = cast(dict[str, dict[str, Any]], schema["properties"])
        assert properties["authority_state"]["const"] == "untrusted_observation"
        assert properties["configuration_authority"]["const"] == "none"
        assert properties["reset_authority"]["const"] == "none"
        assert properties["output_authority"]["const"] == "none"
        assert properties["evidence_suppression_authority"]["const"] == "none"
        assert schema["additionalProperties"] is False
        assert (
            not {
                "policy",
                "threshold",
                "configuration",
                "reset",
                "rearm",
                "admin",
                "suppress_evidence",
                "scope_override",
            }
            & properties.keys()
        )


def test_recovery_schema_excludes_production_ai_and_motion_authority() -> None:
    from scripts.export_runtime_schemas import RUNTIME_SCHEMAS

    schema = RUNTIME_SCHEMAS["recovery-event.schema.json"]
    properties = cast(dict[str, dict[str, Any]], schema["properties"])
    assert properties["actor_domain"]["const"] == "independent_safety_authority"
    assert properties["motion_authority"]["const"] == "none"
    assert properties["configuration_authority"]["const"] == "none"
    assert properties["output_authority"]["const"] == "none"
    assert properties["evidence_suppression_authority"]["const"] == "none"


def test_canonical_verifier_detects_runtime_schema_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.verify as verifier
    from scripts.export_runtime_schemas import RUNTIME_SCHEMAS, render

    schema_root = tmp_path / "schemas" / "runtime"
    schema_root.mkdir(parents=True)
    for name, schema in RUNTIME_SCHEMAS.items():
        (schema_root / name).write_bytes(render(schema))
    stale_name = sorted(RUNTIME_SCHEMAS)[0]
    (schema_root / stale_name).write_bytes(b"{}\n")
    monkeypatch.setattr(verifier, "ROOT", tmp_path)

    with pytest.raises(SystemExit, match=f"schema is stale: schemas/runtime/{stale_name}"):
        verifier.check_runtime_schemas()
