"""Strict runtime contracts and pure authority-free records."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Annotated, Any, Literal, Self, TypeAlias, TypeVar

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    ValidationInfo,
    field_validator,
    model_validator,
)

Identifier = Annotated[
    StrictStr,
    Field(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$"),
]
Sha256 = Annotated[StrictStr, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
Ed25519Signature = Annotated[StrictStr, Field(pattern=r"^ed25519:[0-9a-f]{128}$")]
SequenceNumber = Annotated[StrictInt, Field(ge=0, le=9_007_199_254_740_991)]
FiniteNonNegative = Annotated[StrictFloat, Field(ge=0.0, allow_inf_nan=False)]
FinitePositive = Annotated[StrictFloat, Field(gt=0.0, allow_inf_nan=False)]
Summary = Annotated[StrictStr, Field(min_length=1, max_length=2048)]
_WIRE_DATETIME = re.compile(
    r"^(?:[0-9]{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]{1,6})?"
    r"(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])$"
)
MAX_OBSERVATION_BYTES = 1024 * 1024


def _parse_wire_datetime(value: Any, info: ValidationInfo) -> Any:
    if info.mode != "json":
        return value
    if type(value) is not str or _WIRE_DATETIME.fullmatch(value) is None:
        raise ValueError("timestamp must use the bounded RFC 3339 wire format")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed


def _json_array_to_tuple(value: Any, info: ValidationInfo) -> Any:
    if info.mode == "json" and type(value) is list:
        return tuple(value)
    return value


class RuntimeContract(BaseModel):
    """Base for strict, frozen runtime wire contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, validate_default=True)

    @model_validator(mode="before")
    @classmethod
    def reject_boolean_schema_version(cls, value: Any) -> Any:
        if isinstance(value, dict) and type(value.get("schema_version")) is bool:
            raise ValueError("schema_version must be integer 1, not boolean")
        return value


class RuntimeObservation(RuntimeContract):
    """Common provenance for an untrusted observation; never an authority grant."""

    schema_version: Literal[1] = 1
    observation_id: Identifier
    run_id: Identifier
    source_id: Identifier
    sequence_number: SequenceNumber
    observed_at: AwareDatetime
    received_at: AwareDatetime
    input_sha256: Sha256
    authority_state: Literal["untrusted_observation"] = "untrusted_observation"
    configuration_authority: Literal["none"] = "none"
    reset_authority: Literal["none"] = "none"
    output_authority: Literal["none"] = "none"
    evidence_suppression_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"
    content_treatment: Literal["untrusted_data"] = "untrusted_data"

    _parse_observed_at = field_validator("observed_at", mode="before")(_parse_wire_datetime)
    _parse_received_at = field_validator("received_at", mode="before")(_parse_wire_datetime)

    @model_validator(mode="after")
    def validate_observation_chronology(self) -> Self:
        if self.observed_at > self.received_at:
            raise ValueError("observed_at cannot be after received_at")
        return self


ObservationT = TypeVar("ObservationT", bound=RuntimeObservation)


def _observation_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate JSON object name: {name}")
        result[name] = value
    return result


def _reject_observation_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def bind_observation_bytes(raw: bytes, model: type[ObservationT]) -> ObservationT:
    """Parse one untrusted JSON object and bind it to its exact input bytes."""

    if type(raw) is not bytes:
        raise TypeError("observation input must be exact bytes")
    if not raw:
        raise ValueError("observation JSON is empty")
    if len(raw) > MAX_OBSERVATION_BYTES:
        raise ValueError(f"observation exceeds {MAX_OBSERVATION_BYTES} bytes")
    if not issubclass(model, RuntimeObservation):
        raise TypeError("model must be a RuntimeObservation type")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("observation is not valid UTF-8") from error
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_observation_object,
            parse_constant=_reject_observation_nonfinite,
        )
    except RecursionError as error:
        raise ValueError("observation is malformed JSON") from error
    except ValueError as error:
        if str(error).startswith(("duplicate JSON", "non-finite JSON")):
            raise
        raise ValueError("observation is malformed JSON") from error
    if not isinstance(parsed, dict):
        raise ValueError("observation JSON must be an object")
    if "input_sha256" in parsed:
        raise ValueError("input_sha256 is reserved for the trusted byte boundary")
    parsed["input_sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    wire = json.dumps(
        parsed,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return model.model_validate_json(wire)


class CommandObservation(RuntimeObservation):
    """Production-originated command intent, accepted only as untrusted observation."""

    source_domain: Literal["production_ai"] = "production_ai"
    command_id: Identifier
    command_kind: Literal["idle", "motion_requested", "motion_cancel_requested"]
    motion_requested: StrictBool
    program_id: Identifier | None = None
    frame_id: Identifier | None = None
    motion_direction: Literal["positive", "negative", "stationary", "unknown"] | None = None

    @model_validator(mode="after")
    def require_consistent_motion_intent(self) -> Self:
        expected = self.command_kind == "motion_requested"
        if self.motion_requested is not expected:
            raise ValueError("motion_requested contradicts command_kind")
        return self


class PhysicalObservation(RuntimeObservation):
    """Independently sourced represented zone and machine state."""

    source_domain: Literal["independent_physical_observation"] = "independent_physical_observation"
    zone_id: Identifier
    occupancy: Literal["clear", "present", "entering", "unknown", "contradictory"]
    motion_state: Literal["stopped", "moving", "unknown", "contradictory"]
    speed_mps: FiniteNonNegative | None
    acceleration_mps2: FiniteNonNegative | None = None
    quality: Literal["good", "degraded", "invalid", "missing", "contradictory"]
    calibration_sha256: Sha256
    program_id: Identifier | None = None
    frame_id: Identifier | None = None
    motion_direction: Literal["positive", "negative", "stationary", "unknown"] | None = None
    attributed_command_id: Identifier | None = None
    attributed_command_sequence: SequenceNumber | None = None

    @model_validator(mode="after")
    def preserve_unknown_and_contradictory_state(self) -> Self:
        if (self.attributed_command_id is None) is not (self.attributed_command_sequence is None):
            raise ValueError("command attribution identity and sequence must be supplied together")
        if self.motion_state == "stopped" and self.speed_mps not in (None, 0.0):
            raise ValueError("stopped motion_state requires zero or absent speed_mps")
        if self.motion_state == "moving" and self.speed_mps is None:
            raise ValueError("moving motion_state requires speed_mps")
        if self.quality == "good" and (
            self.occupancy in {"unknown", "contradictory"}
            or self.motion_state in {"unknown", "contradictory"}
        ):
            raise ValueError("good quality contradicts unknown or contradictory physical state")
        if self.quality in {"missing", "contradictory"} and (
            self.speed_mps is not None or self.acceleration_mps2 is not None
        ):
            raise ValueError("missing or contradictory quality cannot carry motion measurements")
        return self


class SourceHealthObservation(RuntimeObservation):
    """Independent monitor observation of one source and its clock."""

    source_domain: Literal["independent_source_health"] = "independent_source_health"
    monitored_source_id: Identifier
    source_state: Literal["healthy", "degraded", "failed", "missing", "contradictory"]
    clock_state: Literal["healthy", "degraded", "failed", "unknown", "contradictory"]
    last_source_sequence: SequenceNumber | None

    @model_validator(mode="after")
    def preserve_health_uncertainty(self) -> Self:
        if self.source_state == "healthy" and self.last_source_sequence is None:
            raise ValueError("healthy source requires last_source_sequence")
        if self.source_state == "missing" and self.last_source_sequence is not None:
            raise ValueError("missing source cannot claim a current sequence")
        return self


class SupervisorConfiguration(RuntimeContract):
    """Signed configuration values; file-byte authority is established by the loader."""

    schema_version: Literal[1] = 1
    configuration_id: Identifier
    revision: Annotated[StrictInt, Field(ge=1, le=9_007_199_254_740_991)]
    scope_id: Identifier
    valid_from: AwareDatetime
    valid_until: AwareDatetime
    required_source_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=64)]
    max_observation_age_seconds: FinitePositive
    max_receive_delay_seconds: FiniteNonNegative
    max_future_skew_seconds: FiniteNonNegative
    max_correlation_delay_seconds: FinitePositive
    approved_calibration_sha256: Annotated[tuple[Sha256, ...], Field(min_length=1, max_length=64)]
    max_speed_mps: FinitePositive
    max_acceleration_mps2: FinitePositive
    signer_id: Identifier
    signature_algorithm: Literal["ed25519"] = "ed25519"
    signature: Ed25519Signature
    authority_state: Literal["externally_signed_configuration"] = "externally_signed_configuration"
    operational_authority: Literal["simulated_evaluation_only"] = "simulated_evaluation_only"

    _parse_valid_from = field_validator("valid_from", mode="before")(_parse_wire_datetime)
    _parse_valid_until = field_validator("valid_until", mode="before")(_parse_wire_datetime)
    _parse_required_sources = field_validator("required_source_ids", mode="before")(
        _json_array_to_tuple
    )
    _parse_approved_calibrations = field_validator("approved_calibration_sha256", mode="before")(
        _json_array_to_tuple
    )

    @field_validator("revision", mode="before")
    @classmethod
    def reject_boolean_revision(cls, value: Any) -> Any:
        if type(value) is bool:
            raise ValueError("revision cannot be boolean")
        return value

    @model_validator(mode="after")
    def validate_configuration_invariants(self) -> Self:
        if self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from")
        if len(self.required_source_ids) != len(set(self.required_source_ids)):
            raise ValueError("duplicate required_source_ids")
        if tuple(sorted(self.required_source_ids)) != self.required_source_ids:
            raise ValueError("required_source_ids must be sorted")
        if len(self.approved_calibration_sha256) != len(set(self.approved_calibration_sha256)):
            raise ValueError("duplicate approved_calibration_sha256")
        if tuple(sorted(self.approved_calibration_sha256)) != self.approved_calibration_sha256:
            raise ValueError("approved_calibration_sha256 must be sorted")
        return self


def _validate_hash_tuple(values: tuple[str, ...], *, field_name: str) -> None:
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {field_name}")
    if tuple(sorted(values)) != values:
        raise ValueError(f"{field_name} must be sorted")


class CommandAttributionRecord(RuntimeContract):
    """Bounded historical command identity used only for deterministic correlation."""

    schema_version: Literal[1] = 1
    command_id: Identifier
    sequence_number: SequenceNumber
    observed_at: AwareDatetime
    motion_requested: StrictBool
    input_sha256: Sha256
    operational_authority: Literal["none"] = "none"

    _parse_observed_at = field_validator("observed_at", mode="before")(_parse_wire_datetime)


SupervisorStateName: TypeAlias = Literal[
    "initializing",
    "monitoring_normal",
    "monitoring_degraded",
    "intervention_requested",
    "intervention_latched",
    "stopped_unverified",
    "reset_not_permitted",
    "reset_ready",
    "rearm_pending",
    "recovery_pending",
]


class SupervisorStateRecord(RuntimeContract):
    """Persistent deterministic intervention and recovery state; never a command."""

    schema_version: Literal[1] = 1
    state_id: Identifier
    run_id: Identifier
    evaluated_at: AwareDatetime
    supervisor_state: SupervisorStateName
    latched: StrictBool
    first_out_reason: Identifier
    reason_codes: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=64)]
    configuration_sha256: Sha256
    input_sha256: Annotated[tuple[Sha256, ...], Field(min_length=1, max_length=256)]
    active_request_sha256: Sha256 | None = None
    output_state: Literal[
        "not_requested",
        "request_pending",
        "acknowledged_unverified",
        "unresolved",
    ] = "not_requested"
    reset_sequence: SequenceNumber = 0
    fresh_start_required: StrictBool = False
    command_history: Annotated[tuple[CommandAttributionRecord, ...], Field(max_length=256)] = ()
    consumed_command_attributions: Annotated[tuple[Identifier, ...], Field(max_length=256)] = ()
    authority_state: Literal["deterministic_supervisor_state"] = "deterministic_supervisor_state"
    motion_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"

    _parse_evaluated_at = field_validator("evaluated_at", mode="before")(_parse_wire_datetime)
    _parse_reason_codes = field_validator("reason_codes", mode="before")(_json_array_to_tuple)
    _parse_input_hashes = field_validator("input_sha256", mode="before")(_json_array_to_tuple)
    _parse_command_history = field_validator("command_history", mode="before")(_json_array_to_tuple)
    _parse_consumed_attributions = field_validator("consumed_command_attributions", mode="before")(
        _json_array_to_tuple
    )

    @model_validator(mode="after")
    def validate_state_record(self) -> Self:
        _validate_hash_tuple(self.input_sha256, field_name="input_sha256")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("duplicate reason_codes")
        if self.reason_codes != tuple(sorted(self.reason_codes)):
            raise ValueError("reason_codes must be sorted")
        if self.first_out_reason not in self.reason_codes:
            raise ValueError("first_out_reason must be present in reason_codes")
        history_identities = tuple(
            (item.command_id, item.sequence_number) for item in self.command_history
        )
        if history_identities != tuple(sorted(history_identities)) or len(
            history_identities
        ) != len(set(history_identities)):
            raise ValueError("command_history must have unique sorted command identities")
        history_keys = {
            f"{command_id}:sequence:{sequence}" for command_id, sequence in history_identities
        }
        if self.consumed_command_attributions != tuple(
            sorted(set(self.consumed_command_attributions))
        ):
            raise ValueError("consumed command attributions must be unique and sorted")
        if not set(self.consumed_command_attributions).issubset(history_keys):
            raise ValueError("consumed command attribution must exist in command_history")
        nonlatched = {"initializing", "monitoring_normal", "monitoring_degraded"}
        if (self.supervisor_state not in nonlatched) is not self.latched:
            raise ValueError("latched flag contradicts supervisor_state")
        if self.supervisor_state in nonlatched and (
            self.active_request_sha256 is not None
            or self.output_state != "not_requested"
            or self.fresh_start_required
        ):
            raise ValueError("nonlatched state cannot retain intervention or recovery state")
        if self.supervisor_state == "intervention_requested" and (
            self.active_request_sha256 is not None or self.output_state != "not_requested"
        ):
            raise ValueError("intervention_requested cannot predate its action request")
        if self.supervisor_state == "intervention_latched" and (
            self.active_request_sha256 is None
            or self.output_state not in {"request_pending", "unresolved"}
        ):
            raise ValueError("intervention_latched requires an unresolved action request")
        if self.supervisor_state == "stopped_unverified" and (
            self.active_request_sha256 is None or self.output_state != "acknowledged_unverified"
        ):
            raise ValueError("stopped_unverified requires an unverified acknowledgment")
        if self.supervisor_state == "reset_not_permitted" and self.active_request_sha256 is None:
            raise ValueError("reset_not_permitted requires an existing intervention request")
        if self.supervisor_state in {"reset_ready", "rearm_pending", "recovery_pending"} and (
            self.active_request_sha256 is None or self.output_state != "acknowledged_unverified"
        ):
            raise ValueError("recovery state requires an acknowledged intervention request")
        if self.fresh_start_required and self.supervisor_state != "recovery_pending":
            raise ValueError("fresh_start_required is only valid while recovery is pending")
        return self


class RecoveryEvent(RuntimeContract):
    """Exact recovery event from a separate external safety authority."""

    schema_version: Literal[1] = 1
    event_id: Identifier
    run_id: Identifier
    observed_at: AwareDatetime
    event_kind: Literal["reset", "rearm", "recovery_confirmed", "fresh_start"]
    actor_domain: Literal["independent_safety_authority"]
    authorization_state: Literal["externally_authorized"]
    configuration_sha256: Sha256
    input_sha256: Sha256
    configuration_authority: Literal["none"] = "none"
    output_authority: Literal["none"] = "none"
    evidence_suppression_authority: Literal["none"] = "none"
    motion_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"

    _parse_observed_at = field_validator("observed_at", mode="before")(_parse_wire_datetime)


class SupervisorDecision(RuntimeContract):
    """Deterministic decision record bound to exact configuration and input hashes."""

    schema_version: Literal[1] = 1
    decision_id: Identifier
    run_id: Identifier
    evaluated_at: AwareDatetime
    supervisor_state: SupervisorStateName
    action: Literal["none", "advisory_warning", "inhibit_request", "protective_stop_request"]
    first_out_reason: Identifier
    reason_codes: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=64)]
    configuration_sha256: Sha256
    input_sha256: Annotated[tuple[Sha256, ...], Field(min_length=1, max_length=256)]
    authority_state: Literal["deterministic_supervisor_record"] = "deterministic_supervisor_record"
    operational_authority: Literal["simulated_request_only"] = "simulated_request_only"

    _parse_evaluated_at = field_validator("evaluated_at", mode="before")(_parse_wire_datetime)
    _parse_reason_codes = field_validator("reason_codes", mode="before")(_json_array_to_tuple)
    _parse_input_hashes = field_validator("input_sha256", mode="before")(_json_array_to_tuple)

    @model_validator(mode="after")
    def validate_ordered_provenance(self) -> Self:
        _validate_hash_tuple(self.input_sha256, field_name="input_sha256")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("duplicate reason_codes")
        if tuple(sorted(self.reason_codes)) != self.reason_codes:
            raise ValueError("reason_codes must be sorted")
        if self.first_out_reason not in self.reason_codes:
            raise ValueError("first_out_reason must be present in reason_codes")
        return self


class ActionRequest(RuntimeContract):
    """One-way local simulated request artifact; never a machine command."""

    schema_version: Literal[1] = 1
    request_id: Identifier
    run_id: Identifier
    created_at: AwareDatetime
    action: Literal["inhibit_request", "protective_stop_request"]
    decision_sha256: Sha256
    configuration_sha256: Sha256
    input_sha256: Annotated[tuple[Sha256, ...], Field(min_length=1, max_length=256)]
    delivery_mode: Literal["local_closed_file_simulation"] = "local_closed_file_simulation"
    authority_state: Literal["simulated_request_artifact"] = "simulated_request_artifact"
    operational_authority: Literal["none"] = "none"

    _parse_created_at = field_validator("created_at", mode="before")(_parse_wire_datetime)
    _parse_input_hashes = field_validator("input_sha256", mode="before")(_json_array_to_tuple)

    @model_validator(mode="after")
    def validate_ordered_provenance(self) -> Self:
        _validate_hash_tuple(self.input_sha256, field_name="input_sha256")
        return self


class ActionAcknowledgment(RuntimeContract):
    """Untrusted fixture acknowledgment; it proves neither stopping nor reset authority."""

    schema_version: Literal[1] = 1
    acknowledgment_id: Identifier
    run_id: Identifier
    observed_at: AwareDatetime
    request_sha256: Sha256
    configuration_sha256: Sha256
    input_sha256: Annotated[tuple[Sha256, ...], Field(min_length=1, max_length=256)]
    status: Literal[
        "received_by_simulated_fixture",
        "rejected_by_simulated_fixture",
        "unknown",
    ]
    authority_state: Literal["untrusted_observation"] = "untrusted_observation"
    stopping_claim: Literal["not_established"] = "not_established"
    reset_authority: Literal["none"] = "none"
    operational_authority: Literal["none"] = "none"

    _parse_observed_at = field_validator("observed_at", mode="before")(_parse_wire_datetime)
    _parse_input_hashes = field_validator("input_sha256", mode="before")(_json_array_to_tuple)

    @model_validator(mode="after")
    def validate_ordered_provenance(self) -> Self:
        _validate_hash_tuple(self.input_sha256, field_name="input_sha256")
        return self


class IncidentEvent(RuntimeContract):
    """One immutable, non-authoritative timeline entry."""

    schema_version: Literal[1] = 1
    event_id: Identifier
    occurred_at: AwareDatetime
    event_kind: Literal[
        "observation_recorded",
        "decision_recorded",
        "request_recorded",
        "acknowledgment_observed",
        "configuration_fault",
        "source_fault",
    ]
    record_sha256: Sha256
    summary: Summary
    operational_authority: Literal["none"] = "none"

    _parse_occurred_at = field_validator("occurred_at", mode="before")(_parse_wire_datetime)


class IncidentTimeline(RuntimeContract):
    """Ordered incident evidence bound to exact configuration, inputs, and outputs."""

    schema_version: Literal[1] = 1
    timeline_id: Identifier
    run_id: Identifier
    created_at: AwareDatetime
    configuration_sha256: Sha256
    input_sha256: Annotated[tuple[Sha256, ...], Field(min_length=1, max_length=256)]
    decision_sha256: Annotated[tuple[Sha256, ...], Field(min_length=1, max_length=256)]
    request_sha256: tuple[Sha256, ...] = ()
    events: Annotated[tuple[IncidentEvent, ...], Field(min_length=1, max_length=1024)]
    authority_state: Literal["incident_evidence_only"] = "incident_evidence_only"
    stopping_claim: Literal["not_established"] = "not_established"
    operational_authority: Literal["none"] = "none"

    _parse_created_at = field_validator("created_at", mode="before")(_parse_wire_datetime)
    _parse_inputs = field_validator("input_sha256", mode="before")(_json_array_to_tuple)
    _parse_decisions = field_validator("decision_sha256", mode="before")(_json_array_to_tuple)
    _parse_requests = field_validator("request_sha256", mode="before")(_json_array_to_tuple)
    _parse_events = field_validator("events", mode="before")(_json_array_to_tuple)

    @model_validator(mode="after")
    def validate_timeline(self) -> Self:
        _validate_hash_tuple(self.input_sha256, field_name="input_sha256")
        _validate_hash_tuple(self.decision_sha256, field_name="decision_sha256")
        if self.request_sha256:
            _validate_hash_tuple(self.request_sha256, field_name="request_sha256")
        event_ids = tuple(event.event_id for event in self.events)
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("duplicate event_id")
        timestamps = tuple(event.occurred_at for event in self.events)
        if timestamps != tuple(sorted(timestamps)):
            raise ValueError("events must be chronological")
        if self.created_at < timestamps[-1]:
            raise ValueError("created_at cannot predate the final event")
        return self
