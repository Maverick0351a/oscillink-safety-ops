"""Portable release-verification contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

ArtifactName = Annotated[StrictStr, Field(pattern=r"^[^/\\]+$")]
Sha256Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
GitCommit = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{40}$")]
PackageVersion = Annotated[StrictStr, Field(min_length=1)]


class ReleaseContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReleaseArtifact(ReleaseContract):
    name: ArtifactName
    sha256: Sha256Digest
    size_bytes: Annotated[StrictInt, Field(ge=1)]


class ReleaseVerification(ReleaseContract):
    schema_version: Literal[1]
    package_name: Literal["oscillink-safety-ops"]
    package_version: PackageVersion
    candidate_commit: GitCommit
    artifacts: Annotated[tuple[ReleaseArtifact, ...], Field(min_length=1)]
