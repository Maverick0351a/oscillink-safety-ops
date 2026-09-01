from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.standards import LicensedStandardRegistry
from scripts.export_schemas import SCHEMAS

FIXTURE = Path(__file__).parent / "fixtures" / "licensed_standards_metadata.json"


def test_metadata_registry_preserves_current_and_superseded_licensed_editions() -> None:
    registry = LicensedStandardRegistry.model_validate_json(FIXTURE.read_text(encoding="utf-8"))

    assert len(registry.records) == 4
    nfpa_2024 = next(item for item in registry.records if item.record_id == "nfpa-70e-2024")
    assert nfpa_2024.superseded_by == "nfpa-70e-2027"
    assert all(item.content_access == "not_supplied" for item in registry.records)
    assert all(item.storage_rights == "not_confirmed" for item in registry.records)
    assert registry.authority_state == "metadata_only"
    assert registry.compliance_state == "no_conclusion"


def test_metadata_registry_rejects_licensed_content_or_storage_path() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["records"][0]["content_text"] = "copyrighted standard text must not enter metadata"

    with pytest.raises(ValidationError):
        LicensedStandardRegistry.model_validate(payload)


def test_metadata_registry_rejects_unknown_supersession_target() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["records"][0]["superseded_by"] = "missing-edition"

    with pytest.raises(ValidationError, match="unknown superseded_by"):
        LicensedStandardRegistry.model_validate(payload)


def test_licensed_standard_registry_schema_fixes_metadata_only_authority() -> None:
    schema = SCHEMAS["licensed-standard-registry.schema.json"]

    assert schema["additionalProperties"] is False
    assert schema["properties"]["authority_state"]["const"] == "metadata_only"
    assert schema["properties"]["operational_authority"]["const"] == "none"
