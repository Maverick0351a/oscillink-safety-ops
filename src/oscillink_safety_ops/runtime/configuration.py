"""Exact-byte, locally verified immutable runtime configuration authority."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PureWindowsPath
from types import MappingProxyType
from typing import Any, Self

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import ValidationError

from .contracts import SupervisorConfiguration

DEFAULT_MAX_CONFIGURATION_BYTES = 65_536


class ConfigurationError(ValueError):
    """Raised when configuration bytes or authority checks fail closed."""


def _require_finite_nonnegative(value: float, name: str, *, positive: bool = False) -> None:
    if type(value) is not float or not (float("-inf") < value < float("inf")):
        raise TypeError(f"{name} must be a finite float")
    if (positive and value <= 0.0) or (not positive and value < 0.0):
        raise ValueError(f"{name} is outside its permitted domain")


@dataclass(frozen=True, slots=True)
class ConfigurationConstraints:
    """Independent authority ceilings that a signed configuration cannot widen."""

    max_observation_age_seconds: float
    max_receive_delay_seconds: float
    max_future_skew_seconds: float
    max_correlation_delay_seconds: float
    max_speed_mps: float
    max_acceleration_mps2: float
    mandatory_source_ids: frozenset[str]

    def __post_init__(self) -> None:
        _require_finite_nonnegative(
            self.max_observation_age_seconds,
            "max_observation_age_seconds",
            positive=True,
        )
        _require_finite_nonnegative(self.max_receive_delay_seconds, "max_receive_delay_seconds")
        _require_finite_nonnegative(self.max_future_skew_seconds, "max_future_skew_seconds")
        _require_finite_nonnegative(
            self.max_correlation_delay_seconds,
            "max_correlation_delay_seconds",
            positive=True,
        )
        _require_finite_nonnegative(self.max_speed_mps, "max_speed_mps", positive=True)
        _require_finite_nonnegative(
            self.max_acceleration_mps2, "max_acceleration_mps2", positive=True
        )
        if not self.mandatory_source_ids:
            raise ValueError("mandatory_source_ids must not be empty")
        if any(type(item) is not str or not item for item in self.mandatory_source_ids):
            raise TypeError("mandatory_source_ids must contain nonempty plain strings")


@dataclass(frozen=True, slots=True)
class ConfigurationAuthority:
    """Immutable trust, scope, revision, exact-byte, and ceiling authority."""

    root: Path
    scope_id: str
    signer_public_keys: Mapping[str, bytes]
    approved_configuration_sha256: Mapping[tuple[str, int], str]
    constraints: ConfigurationConstraints
    revoked_signer_ids: frozenset[str] = frozenset()
    revoked_revisions: frozenset[tuple[str, int]] = frozenset()
    minimum_revision: int = 1
    max_configuration_bytes: int = DEFAULT_MAX_CONFIGURATION_BYTES

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path):
            raise TypeError("root must be a Path")
        if type(self.scope_id) is not str or not self.scope_id:
            raise TypeError("scope_id must be a nonempty plain string")
        if type(self.minimum_revision) is not int or self.minimum_revision < 1:
            raise ValueError("minimum_revision must be a positive integer")
        if (
            type(self.max_configuration_bytes) is not int
            or self.max_configuration_bytes < 1
            or self.max_configuration_bytes > 1024 * 1024
        ):
            raise ValueError("max_configuration_bytes is outside the permitted domain")

        keys: dict[str, bytes] = {}
        for signer_id, public_key in self.signer_public_keys.items():
            if type(signer_id) is not str or not signer_id:
                raise TypeError("signer identity must be a nonempty plain string")
            if type(public_key) is not bytes or len(public_key) != 32:
                raise ValueError("Ed25519 public keys must be exactly 32 bytes")
            keys[signer_id] = bytes(public_key)

        approved: dict[tuple[str, int], str] = {}
        for identity, digest in self.approved_configuration_sha256.items():
            if (
                type(identity) is not tuple
                or len(identity) != 2
                or type(identity[0]) is not str
                or not identity[0]
                or type(identity[1]) is not int
                or identity[1] < 1
            ):
                raise TypeError("approved configuration identity must be (str, positive int)")
            if (
                type(digest) is not str
                or len(digest) != 71
                or not digest.startswith("sha256:")
                or any(character not in "0123456789abcdef" for character in digest[7:])
            ):
                raise ValueError("approved configuration digest must be prefixed lowercase SHA-256")
            approved[identity] = digest

        object.__setattr__(self, "root", self.root.resolve())
        object.__setattr__(self, "signer_public_keys", MappingProxyType(keys))
        object.__setattr__(self, "approved_configuration_sha256", MappingProxyType(approved))
        object.__setattr__(self, "revoked_signer_ids", frozenset(self.revoked_signer_ids))
        object.__setattr__(self, "revoked_revisions", frozenset(self.revoked_revisions))


@dataclass(frozen=True, slots=True)
class BoundConfiguration:
    """One validated model bound to the sole captured file-byte sequence."""

    configuration: SupervisorConfiguration
    exact_bytes: bytes = field(repr=False)
    configuration_sha256: str

    def __post_init__(self) -> None:
        actual = "sha256:" + hashlib.sha256(self.exact_bytes).hexdigest()
        if actual != self.configuration_sha256:
            raise ConfigurationError("bound configuration hash does not match exact bytes")


@dataclass(frozen=True, slots=True)
class RunConfigurationBinding:
    """Immutable run binding that rejects any later configuration substitution."""

    run_id: str
    configuration: BoundConfiguration

    @classmethod
    def start(cls, run_id: str, configuration: BoundConfiguration) -> Self:
        if type(run_id) is not str or not run_id:
            raise ConfigurationError("run_id must be a nonempty plain string")
        return cls(run_id=run_id, configuration=configuration)

    @property
    def configuration_sha256(self) -> str:
        return self.configuration.configuration_sha256

    def accept(self, candidate: BoundConfiguration) -> Self:
        if candidate.configuration_sha256 != self.configuration_sha256:
            raise ConfigurationError("mid-run substitution of configuration is forbidden")
        return self


def _duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ConfigurationError(f"duplicate JSON object name: {name}")
        result[name] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise ConfigurationError(f"non-finite JSON number is forbidden: {value}")


def _validate_json_shape(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ConfigurationError("configuration is not valid UTF-8") from error
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=_reject_nonfinite_constant,
        )
    except ConfigurationError:
        raise
    except (json.JSONDecodeError, RecursionError) as error:
        raise ConfigurationError("configuration is malformed JSON") from error
    if not isinstance(parsed, dict):
        raise ConfigurationError("configuration JSON must be an object")
    return parsed


def configuration_signing_bytes(
    configuration: SupervisorConfiguration | Mapping[str, Any],
) -> bytes:
    """Return deterministic semantic bytes covered by an Ed25519 signature."""

    if isinstance(configuration, SupervisorConfiguration):
        model = configuration
    else:
        try:
            wire = json.dumps(configuration, ensure_ascii=False, allow_nan=False)
            model = SupervisorConfiguration.model_validate_json(wire)
        except (TypeError, ValueError, ValidationError) as error:
            message = "cannot produce signing bytes for invalid configuration"
            raise ConfigurationError(message) from error
    payload = model.model_dump(mode="json", exclude={"signature"})
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _bounded_regular_file_bytes(relative_path: Path, authority: ConfigurationAuthority) -> bytes:
    if not isinstance(relative_path, Path):
        raise ConfigurationError("configuration path must be a Path")
    if (
        relative_path.is_absolute()
        or relative_path.anchor
        or PureWindowsPath(str(relative_path)).drive
        or ".." in relative_path.parts
    ):
        raise ConfigurationError("configuration path must be relative and cannot escape its root")

    candidate = authority.root.joinpath(relative_path)
    cursor = authority.root
    metadata: os.stat_result | None = None
    try:
        for part in relative_path.parts:
            if part in {"", "."}:
                continue
            cursor = cursor / part
            metadata = cursor.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise ConfigurationError("configuration path contains a symlink")
    except FileNotFoundError as error:
        raise ConfigurationError("configuration file does not exist") from error
    except OSError as error:
        raise ConfigurationError("configuration path metadata cannot be read") from error

    if metadata is None:
        try:
            metadata = candidate.lstat()
        except OSError as error:
            raise ConfigurationError("configuration path metadata cannot be read") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise ConfigurationError("configuration path is not a regular file")
    if metadata.st_size > authority.max_configuration_bytes:
        raise ConfigurationError(f"configuration exceeds {authority.max_configuration_bytes} bytes")

    try:
        with candidate.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise ConfigurationError("opened configuration is not a regular file")
            if (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino):
                raise ConfigurationError("configuration changed while opening")
            raw = stream.read(authority.max_configuration_bytes + 1)
    except ConfigurationError:
        raise
    except OSError as error:
        raise ConfigurationError("configuration bytes cannot be read") from error
    if len(raw) > authority.max_configuration_bytes:
        raise ConfigurationError(f"configuration exceeds {authority.max_configuration_bytes} bytes")
    return raw


def _enforce_authority_constraints(
    configuration: SupervisorConfiguration,
    authority: ConfigurationAuthority,
) -> None:
    constraints = authority.constraints
    ceiling_fields = (
        "max_observation_age_seconds",
        "max_receive_delay_seconds",
        "max_future_skew_seconds",
        "max_correlation_delay_seconds",
        "max_speed_mps",
        "max_acceleration_mps2",
    )
    for name in ceiling_fields:
        if getattr(configuration, name) > getattr(constraints, name):
            raise ConfigurationError(f"configuration exceeds authority ceiling for {name}")
    missing = constraints.mandatory_source_ids - set(configuration.required_source_ids)
    if missing:
        raise ConfigurationError("configuration removed an authority-mandated required source")


def _enforce_revision_transition(
    configuration: SupervisorConfiguration,
    previous: BoundConfiguration | None,
) -> None:
    if previous is None:
        return
    prior = previous.configuration
    if configuration.revision < prior.revision:
        raise ConfigurationError("configuration revision rollback is forbidden")
    if configuration.revision == prior.revision:
        if configuration.configuration_id != prior.configuration_id:
            raise ConfigurationError("configuration identity changed without a new revision")
        if configuration_signing_bytes(configuration) != configuration_signing_bytes(prior):
            raise ConfigurationError("configuration changed without a new revision")
        return

    threshold_fields = (
        "max_observation_age_seconds",
        "max_receive_delay_seconds",
        "max_future_skew_seconds",
        "max_correlation_delay_seconds",
        "max_speed_mps",
        "max_acceleration_mps2",
    )
    widened = [
        name for name in threshold_fields if getattr(configuration, name) > getattr(prior, name)
    ]
    if widened:
        raise ConfigurationError(f"threshold widening is forbidden: {', '.join(widened)}")
    if not set(prior.required_source_ids).issubset(configuration.required_source_ids):
        raise ConfigurationError("removing a previously required source is forbidden")
    prior_dependencies = {item.dependency_id: item for item in prior.dependency_bindings}
    current_dependencies = {item.dependency_id: item for item in configuration.dependency_bindings}
    if not set(prior_dependencies).issubset(current_dependencies):
        raise ConfigurationError("removing a previously declared dependency is forbidden")
    if any(
        current_dependencies[identity] != binding
        for identity, binding in prior_dependencies.items()
    ):
        raise ConfigurationError("changing a declared dependency identity is forbidden")


def load_supervisor_configuration(
    relative_path: Path,
    *,
    authority: ConfigurationAuthority,
    evaluation_time: datetime,
    previous: BoundConfiguration | None = None,
) -> BoundConfiguration:
    """Read once, authenticate, authorize, and bind one configuration revision."""

    if type(evaluation_time) is not datetime or evaluation_time.tzinfo is None:
        raise ConfigurationError("evaluation_time must be a timezone-aware plain datetime")
    if evaluation_time.utcoffset() is None:
        raise ConfigurationError("evaluation_time must be timezone-aware")

    raw = _bounded_regular_file_bytes(relative_path, authority)
    parsed = _validate_json_shape(raw)
    try:
        configuration = SupervisorConfiguration.model_validate_json(raw)
    except ValidationError as error:
        message = "configuration does not satisfy the strict runtime contract"
        raise ConfigurationError(message) from error

    identity = (configuration.configuration_id, configuration.revision)
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    expected_digest = authority.approved_configuration_sha256.get(identity)
    if expected_digest is None:
        raise ConfigurationError("configuration revision is not approved for exact-byte use")
    if digest != expected_digest:
        message = "configuration identity has changed bytes from approved exact bytes"
        raise ConfigurationError(message)
    if configuration.scope_id != authority.scope_id:
        raise ConfigurationError("configuration has the wrong scope")
    if configuration.revision < authority.minimum_revision:
        raise ConfigurationError("configuration revision rollback is below the authority minimum")
    if identity in authority.revoked_revisions:
        raise ConfigurationError("configuration uses a revoked revision")
    if configuration.signer_id in authority.revoked_signer_ids:
        raise ConfigurationError("configuration uses a revoked signer")
    public_key_bytes = authority.signer_public_keys.get(configuration.signer_id)
    if public_key_bytes is None:
        raise ConfigurationError("configuration uses an unknown signer")

    try:
        signature = bytes.fromhex(configuration.signature.removeprefix("ed25519:"))
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
            signature, configuration_signing_bytes(configuration)
        )
    except (InvalidSignature, ValueError) as error:
        raise ConfigurationError("configuration has an invalid Ed25519 signature") from error

    if evaluation_time < configuration.valid_from:
        raise ConfigurationError("configuration revision is not yet valid")
    if evaluation_time >= configuration.valid_until:
        raise ConfigurationError("configuration revision is expired")

    _enforce_authority_constraints(configuration, authority)
    _enforce_revision_transition(configuration, previous)
    # The duplicate-checked parse is deliberately retained as a completed boundary check.
    _ = parsed
    return BoundConfiguration(
        configuration=configuration,
        exact_bytes=raw,
        configuration_sha256=digest,
    )
