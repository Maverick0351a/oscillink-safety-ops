"""Exact-byte Ed25519 configuration authority tests."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from oscillink_safety_ops.runtime.configuration import (
    BoundConfiguration,
    ConfigurationAuthority,
    ConfigurationConstraints,
    ConfigurationError,
    RunConfigurationBinding,
    configuration_signing_bytes,
    load_supervisor_configuration,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
SCOPE = "SCOPE-ROBOT-CELL-001"


def configuration_document(
    private_key: Ed25519PrivateKey,
    *,
    configuration_id: str = "configuration:robot-cell:001",
    revision: int = 1,
    scope_id: str = SCOPE,
    signer_id: str = "safety-config-signer:001",
    speed: float = 1.0,
    required_sources: tuple[str, ...] = (
        "independent-health-monitor:a",
        "independent-zone-sensor:a",
        "production-ai:planner",
    ),
    valid_from: str = "2026-09-03T11:00:00Z",
    valid_until: str = "2026-09-03T13:00:00Z",
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": 1,
        "configuration_id": configuration_id,
        "revision": revision,
        "scope_id": scope_id,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "required_source_ids": list(required_sources),
        "max_observation_age_seconds": 0.5,
        "max_receive_delay_seconds": 0.2,
        "max_future_skew_seconds": 0.0,
        "max_correlation_delay_seconds": 0.25,
        "max_speed_mps": speed,
        "max_acceleration_mps2": 2.0,
        "signer_id": signer_id,
        "signature_algorithm": "ed25519",
        "signature": "ed25519:" + "00" * 64,
        "authority_state": "externally_signed_configuration",
        "operational_authority": "simulated_evaluation_only",
    }
    signature = private_key.sign(configuration_signing_bytes(data)).hex()
    data["signature"] = "ed25519:" + signature
    return data


def raw_document(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def constraints(*, maximum_speed: float = 2.0) -> ConfigurationConstraints:
    return ConfigurationConstraints(
        max_observation_age_seconds=1.0,
        max_receive_delay_seconds=1.0,
        max_future_skew_seconds=0.1,
        max_correlation_delay_seconds=0.5,
        max_speed_mps=maximum_speed,
        max_acceleration_mps2=3.0,
        mandatory_source_ids=frozenset(
            {
                "independent-health-monitor:a",
                "independent-zone-sensor:a",
                "production-ai:planner",
            }
        ),
    )


def authority(
    root: Path,
    public_key: bytes,
    approved: dict[tuple[str, int], str],
    *,
    revoked_signers: frozenset[str] = frozenset(),
    revoked_revisions: frozenset[tuple[str, int]] = frozenset(),
    minimum_revision: int = 1,
    max_bytes: int = 65_536,
) -> ConfigurationAuthority:
    return ConfigurationAuthority(
        root=root,
        scope_id=SCOPE,
        signer_public_keys={"safety-config-signer:001": public_key},
        approved_configuration_sha256=approved,
        revoked_signer_ids=revoked_signers,
        revoked_revisions=revoked_revisions,
        minimum_revision=minimum_revision,
        constraints=constraints(),
        max_configuration_bytes=max_bytes,
    )


def write_configuration(root: Path, name: str, raw: bytes) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


def test_loads_exact_bytes_once_and_verifies_real_ed25519_signature(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes_raw()
    raw = raw_document(configuration_document(private_key))
    path = write_configuration(tmp_path, "approved/configuration.json", raw)
    policy = authority(
        tmp_path,
        public_key,
        {("configuration:robot-cell:001", 1): sha256(raw)},
    )
    original_open = Path.open
    read_count = 0

    def counting_open(self: Path, *args: object, **kwargs: object) -> Any:
        nonlocal read_count
        if self == path and args and args[0] == "rb":
            read_count += 1
        return original_open(self, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(Path, "open", counting_open)

    loaded = load_supervisor_configuration(
        Path("approved/configuration.json"),
        authority=policy,
        evaluation_time=NOW,
    )

    assert isinstance(loaded, BoundConfiguration)
    assert loaded.exact_bytes == raw
    assert loaded.configuration_sha256 == sha256(raw)
    assert loaded.configuration.configuration_id == "configuration:robot-cell:001"
    assert read_count == 1


def test_rejects_oversized_input_before_opening_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_configuration(tmp_path, "oversized.json", b"{" + b" " * 100)
    policy = authority(tmp_path, bytes(32), {}, max_bytes=32)
    opened = False
    original_open = Path.open

    def tracking_open(self: Path, *args: object, **kwargs: object) -> Any:
        nonlocal opened
        if self == path:
            opened = True
        return original_open(self, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(Path, "open", tracking_open)

    with pytest.raises(ConfigurationError, match="exceeds"):
        load_supervisor_configuration(Path("oversized.json"), authority=policy, evaluation_time=NOW)
    assert opened is False


@pytest.mark.parametrize("relative", (Path("../escape.json"), Path("/absolute.json")))
def test_rejects_traversal_and_absolute_paths(tmp_path: Path, relative: Path) -> None:
    policy = authority(tmp_path, bytes(32), {})

    with pytest.raises(ConfigurationError, match=r"relative|escape"):
        load_supervisor_configuration(relative, authority=policy, evaluation_time=NOW)


def test_rejects_symlinks_and_non_regular_files(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    raw = raw_document(configuration_document(private_key))
    target = write_configuration(tmp_path, "target.json", raw)
    link = tmp_path / "link.json"
    try:
        link.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")
    policy = authority(tmp_path, private_key.public_key().public_bytes_raw(), {})

    with pytest.raises(ConfigurationError, match="symlink"):
        load_supervisor_configuration(Path("link.json"), authority=policy, evaluation_time=NOW)
    with pytest.raises(ConfigurationError, match="regular file"):
        load_supervisor_configuration(Path("."), authority=policy, evaluation_time=NOW)


def test_rejects_symlinked_parent_directory(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    write_configuration(
        outside,
        "configuration.json",
        raw_document(configuration_document(private_key)),
    )
    link = tmp_path / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlink creation unavailable: {error}")
    policy = authority(tmp_path, private_key.public_key().public_bytes_raw(), {})

    with pytest.raises(ConfigurationError, match="symlink"):
        load_supervisor_configuration(
            Path("linked/configuration.json"), authority=policy, evaluation_time=NOW
        )


@pytest.mark.parametrize("raw", (b"\xff", b"{", b"[]", b'{"x":1,"x":2}'))
def test_rejects_malformed_utf8_json_duplicate_keys_and_non_objects(
    tmp_path: Path, raw: bytes
) -> None:
    write_configuration(tmp_path, "bad.json", raw)
    policy = authority(tmp_path, bytes(32), {})

    with pytest.raises(ConfigurationError, match=r"UTF-8|JSON|object|duplicate"):
        load_supervisor_configuration(Path("bad.json"), authority=policy, evaluation_time=NOW)


def test_rejects_excessive_json_nesting_without_crashing(tmp_path: Path) -> None:
    raw = b"[" * 1100 + b"]" * 1100
    write_configuration(tmp_path, "deep.json", raw)
    policy = authority(tmp_path, bytes(32), {})

    with pytest.raises(ConfigurationError, match="malformed JSON"):
        load_supervisor_configuration(Path("deep.json"), authority=policy, evaluation_time=NOW)


def test_rejects_changed_bytes_under_reused_identity(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    original = raw_document(configuration_document(private_key))
    changed = original + b"\n"
    write_configuration(tmp_path, "configuration.json", changed)
    policy = authority(
        tmp_path,
        private_key.public_key().public_bytes_raw(),
        {("configuration:robot-cell:001", 1): sha256(original)},
    )

    with pytest.raises(ConfigurationError, match=r"changed bytes|approved exact bytes"):
        load_supervisor_configuration(
            Path("configuration.json"), authority=policy, evaluation_time=NOW
        )


def test_rejects_unknown_or_revoked_signer_and_invalid_signature(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes_raw()

    unknown_data = configuration_document(private_key, signer_id="unknown-signer:001")
    unknown_raw = raw_document(unknown_data)
    write_configuration(tmp_path, "unknown.json", unknown_raw)
    unknown_policy = authority(
        tmp_path,
        public_key,
        {("configuration:robot-cell:001", 1): sha256(unknown_raw)},
    )
    with pytest.raises(ConfigurationError, match="unknown signer"):
        load_supervisor_configuration(
            Path("unknown.json"), authority=unknown_policy, evaluation_time=NOW
        )

    valid_raw = raw_document(configuration_document(private_key))
    write_configuration(tmp_path, "revoked.json", valid_raw)
    revoked_policy = authority(
        tmp_path,
        public_key,
        {("configuration:robot-cell:001", 1): sha256(valid_raw)},
        revoked_signers=frozenset({"safety-config-signer:001"}),
    )
    with pytest.raises(ConfigurationError, match="revoked signer"):
        load_supervisor_configuration(
            Path("revoked.json"), authority=revoked_policy, evaluation_time=NOW
        )

    invalid_data = configuration_document(private_key)
    invalid_data["signature"] = "ed25519:" + "11" * 64
    invalid_raw = raw_document(invalid_data)
    write_configuration(tmp_path, "invalid.json", invalid_raw)
    invalid_policy = authority(
        tmp_path,
        public_key,
        {("configuration:robot-cell:001", 1): sha256(invalid_raw)},
    )
    with pytest.raises(ConfigurationError, match="invalid Ed25519 signature"):
        load_supervisor_configuration(
            Path("invalid.json"), authority=invalid_policy, evaluation_time=NOW
        )


def test_rejects_wrong_scope_not_yet_valid_expired_revoked_and_unapproved_revision(
    tmp_path: Path,
) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes_raw()
    cases: tuple[tuple[str, dict[str, Any], datetime, dict[str, Any], str], ...] = (
        (
            "wrong-scope",
            configuration_document(private_key, scope_id="SCOPE-OTHER-001"),
            NOW,
            {},
            "scope",
        ),
        (
            "future",
            configuration_document(
                private_key,
                valid_from="2026-09-03T12:01:00Z",
                valid_until="2026-09-03T13:00:00Z",
            ),
            NOW,
            {},
            "not yet valid",
        ),
        (
            "expired",
            configuration_document(
                private_key,
                valid_from="2026-09-03T10:00:00Z",
                valid_until="2026-09-03T12:00:00Z",
            ),
            NOW,
            {},
            "expired",
        ),
        (
            "revoked-revision",
            configuration_document(private_key),
            NOW,
            {"revoked_revisions": frozenset({("configuration:robot-cell:001", 1)})},
            "revoked revision",
        ),
        (
            "below-minimum",
            configuration_document(private_key),
            NOW,
            {"minimum_revision": 2},
            "rollback",
        ),
    )
    for name, data, evaluation_time, options, message in cases:
        raw = raw_document(data)
        write_configuration(tmp_path, f"{name}.json", raw)
        policy = authority(
            tmp_path,
            public_key,
            {(str(data["configuration_id"]), int(data["revision"])): sha256(raw)},
            **options,
        )
        with pytest.raises(ConfigurationError, match=message):
            load_supervisor_configuration(
                Path(f"{name}.json"), authority=policy, evaluation_time=evaluation_time
            )


def test_rejects_naive_evaluation_time(tmp_path: Path) -> None:
    policy = authority(tmp_path, bytes(32), {})

    with pytest.raises(ConfigurationError, match="timezone-aware"):
        load_supervisor_configuration(
            Path("unused.json"),
            authority=policy,
            evaluation_time=NOW.replace(tzinfo=None),
        )


def test_rejects_authority_ceiling_violation_and_threshold_widening(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes_raw()
    baseline_raw = raw_document(configuration_document(private_key, revision=1, speed=1.0))
    widened_raw = raw_document(configuration_document(private_key, revision=2, speed=1.5))
    excessive_raw = raw_document(configuration_document(private_key, revision=3, speed=3.0))
    for revision, raw in ((1, baseline_raw), (2, widened_raw), (3, excessive_raw)):
        write_configuration(tmp_path, f"revision-{revision}.json", raw)
    approved = {
        ("configuration:robot-cell:001", revision): sha256(raw)
        for revision, raw in ((1, baseline_raw), (2, widened_raw), (3, excessive_raw))
    }
    policy = authority(tmp_path, public_key, approved)
    baseline = load_supervisor_configuration(
        Path("revision-1.json"), authority=policy, evaluation_time=NOW
    )

    with pytest.raises(ConfigurationError, match="threshold widening"):
        load_supervisor_configuration(
            Path("revision-2.json"),
            authority=policy,
            evaluation_time=NOW,
            previous=baseline,
        )
    with pytest.raises(ConfigurationError, match="authority ceiling"):
        load_supervisor_configuration(
            Path("revision-3.json"), authority=policy, evaluation_time=NOW
        )


def test_rejects_revision_rollback_and_required_source_removal(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes_raw()
    revision_1 = raw_document(configuration_document(private_key, revision=1))
    revision_2 = raw_document(configuration_document(private_key, revision=2))
    removed = raw_document(
        configuration_document(
            private_key,
            revision=3,
            required_sources=("independent-zone-sensor:a", "production-ai:planner"),
        )
    )
    raws = {1: revision_1, 2: revision_2, 3: removed}
    for revision, raw in raws.items():
        write_configuration(tmp_path, f"r{revision}.json", raw)
    policy = authority(
        tmp_path,
        public_key,
        {("configuration:robot-cell:001", revision): sha256(raw) for revision, raw in raws.items()},
    )
    first = load_supervisor_configuration(Path("r1.json"), authority=policy, evaluation_time=NOW)
    second = load_supervisor_configuration(
        Path("r2.json"), authority=policy, evaluation_time=NOW, previous=first
    )

    with pytest.raises(ConfigurationError, match="rollback"):
        load_supervisor_configuration(
            Path("r1.json"), authority=policy, evaluation_time=NOW, previous=second
        )
    with pytest.raises(ConfigurationError, match="required source"):
        load_supervisor_configuration(
            Path("r3.json"), authority=policy, evaluation_time=NOW, previous=second
        )


def test_run_binding_is_immutable_and_rejects_mid_run_substitution(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes_raw()
    raw_a = raw_document(configuration_document(private_key, revision=1))
    raw_b = raw_document(
        configuration_document(
            private_key,
            configuration_id="configuration:robot-cell:002",
            revision=2,
        )
    )
    write_configuration(tmp_path, "a.json", raw_a)
    write_configuration(tmp_path, "b.json", raw_b)
    policy = authority(
        tmp_path,
        public_key,
        {
            ("configuration:robot-cell:001", 1): sha256(raw_a),
            ("configuration:robot-cell:002", 2): sha256(raw_b),
        },
    )
    loaded_a = load_supervisor_configuration(Path("a.json"), authority=policy, evaluation_time=NOW)
    loaded_b = load_supervisor_configuration(Path("b.json"), authority=policy, evaluation_time=NOW)
    binding = RunConfigurationBinding.start("run:001", loaded_a)

    assert binding.accept(loaded_a) is binding
    with pytest.raises(ConfigurationError, match="mid-run substitution"):
        binding.accept(loaded_b)
    with pytest.raises((AttributeError, TypeError)):
        binding.run_id = "run:changed"  # type: ignore[misc]
