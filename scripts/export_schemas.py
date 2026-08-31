"""Export canonical JSON Schemas for portable adapter contracts."""

from __future__ import annotations

import json
from pathlib import Path

from oscillink_safety_ops.domain import AuditReport, ProposedPlan, SafetyMemoryPacket

SCHEMAS = {
    "audit-report.schema.json": AuditReport.model_json_schema(),
    "proposed-plan.schema.json": ProposedPlan.model_json_schema(),
    "safety-memory-packet.schema.json": SafetyMemoryPacket.model_json_schema(),
}


def render(schema: dict[str, object]) -> str:
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "schemas"
    root.mkdir(exist_ok=True)
    for name, schema in SCHEMAS.items():
        (root / name).write_text(render(schema), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
