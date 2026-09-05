"""Export stable canonical bytes for runtime JSON Schemas."""

from __future__ import annotations

import json
from pathlib import Path

from oscillink_safety_ops.runtime.contracts import (
    ActionAcknowledgment,
    ActionRequest,
    CommandObservation,
    DependencyBinding,
    IncidentTimeline,
    PhysicalObservation,
    RecoveryEvent,
    SharedDependencyObservation,
    SourceHealthObservation,
    SupervisorConfiguration,
    SupervisorDecision,
    SupervisorStateRecord,
)

RUNTIME_SCHEMAS: dict[str, dict[str, object]] = {
    "action-acknowledgment.schema.json": ActionAcknowledgment.model_json_schema(),
    "action-request.schema.json": ActionRequest.model_json_schema(),
    "command-observation.schema.json": CommandObservation.model_json_schema(),
    "dependency-binding.schema.json": DependencyBinding.model_json_schema(),
    "incident-timeline.schema.json": IncidentTimeline.model_json_schema(),
    "physical-observation.schema.json": PhysicalObservation.model_json_schema(),
    "recovery-event.schema.json": RecoveryEvent.model_json_schema(),
    "shared-dependency-observation.schema.json": SharedDependencyObservation.model_json_schema(),
    "source-health-observation.schema.json": SourceHealthObservation.model_json_schema(),
    "supervisor-configuration.schema.json": SupervisorConfiguration.model_json_schema(),
    "supervisor-decision.schema.json": SupervisorDecision.model_json_schema(),
    "supervisor-state-record.schema.json": SupervisorStateRecord.model_json_schema(),
}


def render(schema: dict[str, object]) -> bytes:
    """Render one schema as sorted stable UTF-8 bytes with one final LF."""

    return (json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "schemas" / "runtime"
    root.mkdir(parents=True, exist_ok=True)
    expected = set(RUNTIME_SCHEMAS)
    for stale in sorted(root.glob("*.schema.json")):
        if stale.name not in expected:
            stale.unlink()
    for name, schema in sorted(RUNTIME_SCHEMAS.items()):
        (root / name).write_bytes(render(schema))


if __name__ == "__main__":
    main()
