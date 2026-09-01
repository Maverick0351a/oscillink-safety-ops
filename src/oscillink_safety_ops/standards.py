"""Metadata-only registry contracts for licensed standards."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import AwareDatetime, model_validator

from .domain import ContractModel, NonEmptyStr


class LicensedStandardRecord(ContractModel):
    schema_version: Literal[1] = 1
    record_id: NonEmptyStr
    publisher: NonEmptyStr
    designation: NonEmptyStr
    title: NonEmptyStr
    edition: NonEmptyStr
    publication_month: NonEmptyStr | None = None
    metadata_source_url: NonEmptyStr
    metadata_observed_at: AwareDatetime
    superseded_by: NonEmptyStr | None = None
    content_access: Literal["not_supplied"] = "not_supplied"
    storage_rights: Literal["not_confirmed"] = "not_confirmed"
    processing_rights: Literal["not_confirmed"] = "not_confirmed"
    applicability_state: Literal["undetermined"] = "undetermined"
    review_state: Literal["not_reviewed"] = "not_reviewed"


class LicensedStandardRegistry(ContractModel):
    schema_version: Literal[1] = 1
    registry_id: NonEmptyStr
    records: tuple[LicensedStandardRecord, ...]
    authority_state: Literal["metadata_only"] = "metadata_only"
    interpretation_authority: Literal["none"] = "none"
    applicability_authority: Literal["none"] = "none"
    compliance_state: Literal["no_conclusion"] = "no_conclusion"
    operational_authority: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_lineage(self) -> Self:
        record_ids = [item.record_id for item in self.records]
        if not record_ids:
            raise ValueError("licensed standard registry must not be empty")
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("duplicate licensed standard record_id")
        known_ids = set(record_ids)
        for item in self.records:
            if item.superseded_by is not None and item.superseded_by not in known_ids:
                raise ValueError(f"record {item.record_id} has unknown superseded_by target")
            if item.superseded_by == item.record_id:
                raise ValueError(f"record {item.record_id} cannot supersede itself")
        return self
