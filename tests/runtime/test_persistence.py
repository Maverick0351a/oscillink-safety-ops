"""Bounded collision-safe exact-byte supervisor-state persistence tests."""

from __future__ import annotations

import hashlib
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from oscillink_safety_ops.runtime import persistence as runtime_persistence
from oscillink_safety_ops.runtime.contracts import CommandAttributionRecord, SupervisorStateRecord
from oscillink_safety_ops.runtime.persistence import (
    PersistenceError,
    StateArtifact,
    load_supervisor_state,
    load_supervisor_state_or_fail_closed,
    persist_supervisor_state,
)
from oscillink_safety_ops.runtime.policy import PolicyEvaluation
from oscillink_safety_ops.runtime.state_machine import (
    apply_policy_evaluation,
    initial_supervisor_state,
    record_action_request,
    record_command_attribution_history,
)
from oscillink_safety_ops.runtime.supervisor import canonical_record_bytes

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
CONFIG = "sha256:" + "a" * 64
INPUT = "sha256:" + "b" * 64


def state(*, run_id: str = "run:001", configuration_sha256: str = CONFIG) -> SupervisorStateRecord:
    initial = initial_supervisor_state(
        run_id=run_id,
        evaluation_time=NOW,
        configuration_sha256=configuration_sha256,
        input_sha256=(INPUT,),
    )
    return apply_policy_evaluation(
        initial,
        PolicyEvaluation("inhibit_request", "missing_source", ("missing_source",)),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=configuration_sha256,
    ).state


def artifact_for(relative_path: Path, raw: bytes) -> StateArtifact:
    return StateArtifact(
        relative_path=relative_path,
        sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
        byte_count=len(raw),
    )


def test_restart_restores_only_the_exact_latched_state(tmp_path: Path) -> None:
    expected = state()
    artifact = persist_supervisor_state(expected, root=tmp_path)

    result = runtime_persistence.load_restart_state_or_fail_closed(
        artifact,
        root=tmp_path,
        expected_run_id=expected.run_id,
        expected_configuration_sha256=expected.configuration_sha256,
        fail_closed_state=expected,
    )

    assert result.integrity_state == "verified"
    assert result.reason_code == "verified_restart_latch"
    assert result.state == expected
    assert result.state.latched is True


def test_restart_restores_exact_command_attribution_history(tmp_path: Path) -> None:
    command = CommandAttributionRecord(
        command_id="command-id:0",
        sequence_number=0,
        observed_at=NOW,
        motion_requested=True,
        input_sha256=INPUT,
    )
    expected = record_command_attribution_history(
        state(),
        command_history=(command,),
        consumed_command_attributions=("command-id:0:sequence:0",),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
    ).state
    artifact = persist_supervisor_state(expected, root=tmp_path)

    result = runtime_persistence.load_restart_state_or_fail_closed(
        artifact,
        root=tmp_path,
        expected_run_id=expected.run_id,
        expected_configuration_sha256=expected.configuration_sha256,
        fail_closed_state=state(),
    )

    assert result.integrity_state == "verified"
    assert result.state.command_history == (command,)
    assert result.state.consumed_command_attributions == ("command-id:0:sequence:0",)


def test_restart_rejects_a_pre_restart_nonlatched_state(tmp_path: Path) -> None:
    normal = apply_policy_evaluation(
        initial_supervisor_state(
            run_id="run:001",
            evaluation_time=NOW,
            configuration_sha256=CONFIG,
            input_sha256=(INPUT,),
        ),
        PolicyEvaluation("none", "monitoring_normal", ("monitoring_normal",)),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    ).state
    artifact = persist_supervisor_state(normal, root=tmp_path)
    fail_closed = state()

    result = runtime_persistence.load_restart_state_or_fail_closed(
        artifact,
        root=tmp_path,
        expected_run_id=normal.run_id,
        expected_configuration_sha256=normal.configuration_sha256,
        fail_closed_state=fail_closed,
    )

    assert result.integrity_state == "failed_closed"
    assert result.reason_code == "restart_state_not_latched"
    assert result.state == fail_closed


@pytest.mark.parametrize(
    ("expected_run_id", "expected_configuration_sha256", "fail_closed"),
    (
        ("run:other", CONFIG, state(run_id="run:other")),
        ("run:001", "sha256:" + "c" * 64, state(configuration_sha256="sha256:" + "c" * 64)),
    ),
    ids=("run-mismatch", "configuration-mismatch"),
)
def test_restart_rejects_latched_state_from_another_run_or_configuration(
    tmp_path: Path,
    expected_run_id: str,
    expected_configuration_sha256: str,
    fail_closed: SupervisorStateRecord,
) -> None:
    artifact = persist_supervisor_state(state(), root=tmp_path)

    result = runtime_persistence.load_restart_state_or_fail_closed(
        artifact,
        root=tmp_path,
        expected_run_id=expected_run_id,
        expected_configuration_sha256=expected_configuration_sha256,
        fail_closed_state=fail_closed,
    )

    assert result.integrity_state == "failed_closed"
    assert result.reason_code == "restart_identity_mismatch"
    assert result.state == fail_closed
    assert result.state.latched is True


def test_restart_rejects_a_fail_closed_fallback_for_the_wrong_identity(tmp_path: Path) -> None:
    expected = state()
    artifact = persist_supervisor_state(expected, root=tmp_path)

    with pytest.raises(ValueError, match="fail_closed_state identity"):
        runtime_persistence.load_restart_state_or_fail_closed(
            artifact,
            root=tmp_path,
            expected_run_id="run:other",
            expected_configuration_sha256=expected.configuration_sha256,
            fail_closed_state=expected,
        )


def test_restart_rejects_a_stale_valid_state_against_the_trusted_expected_state_id(
    tmp_path: Path,
) -> None:
    stale = state()
    current = record_action_request(
        stale,
        request_sha256="sha256:" + "d" * 64,
        evaluation_time=NOW,
        input_sha256=(INPUT,),
    ).state
    stale_artifact = persist_supervisor_state(stale, root=tmp_path)
    fail_closed = state()

    result = runtime_persistence.load_restart_state_or_fail_closed(
        stale_artifact,
        root=tmp_path,
        expected_run_id=current.run_id,
        expected_configuration_sha256=current.configuration_sha256,
        expected_state_id=current.state_id,
        fail_closed_state=fail_closed,
    )

    assert result.integrity_state == "failed_closed"
    assert result.reason_code == "restart_state_id_mismatch"
    assert result.state == fail_closed


def test_persist_and_load_exact_canonical_bytes_preserves_latch_across_restart(
    tmp_path: Path,
) -> None:
    artifact = persist_supervisor_state(state(), root=tmp_path, directory=Path("runtime-state"))
    raw = (tmp_path / artifact.relative_path).read_bytes()
    loaded = load_supervisor_state(artifact, root=tmp_path)

    assert raw == canonical_record_bytes(state())
    assert artifact.sha256 == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert artifact.byte_count == len(raw)
    assert loaded == state()
    assert loaded.latched is True
    assert loaded.supervisor_state == "intervention_requested"


def test_missing_truncated_malformed_substituted_and_corrupt_state_fail_closed(
    tmp_path: Path,
) -> None:
    fail_closed = state()
    missing = StateArtifact(Path("states/missing.json"), "sha256:" + "c" * 64, 10)
    assert (
        load_supervisor_state_or_fail_closed(
            missing, root=tmp_path, fail_closed_state=fail_closed
        ).state
        == fail_closed
    )

    valid = persist_supervisor_state(state(), root=tmp_path)
    path = tmp_path / valid.relative_path
    original = path.read_bytes()
    mutations = (
        original[:-1],
        b"{",
        original.replace(b'"latched":true', b'"latched":false'),
        bytes([original[0] ^ 1]) + original[1:],
    )
    for index, mutated in enumerate(mutations):
        candidate_path = Path(f"hostile/state-{index}.json")
        destination = tmp_path / candidate_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(mutated)
        result = load_supervisor_state_or_fail_closed(
            StateArtifact(candidate_path, valid.sha256, valid.byte_count),
            root=tmp_path,
            fail_closed_state=fail_closed,
        )
        assert result.integrity_state == "failed_closed"
        assert result.state.latched is True
        assert result.state.supervisor_state not in {"monitoring_normal", "monitoring_degraded"}


def test_duplicate_keys_are_rejected_even_when_exact_hash_matches(tmp_path: Path) -> None:
    raw = canonical_record_bytes(state())
    duplicate = raw.replace(
        b'{"active_request_sha256":', b'{"schema_version":1,"active_request_sha256":'
    )
    relative = Path("hostile/duplicate.json")
    path = tmp_path / relative
    path.parent.mkdir()
    path.write_bytes(duplicate)

    with pytest.raises(PersistenceError, match="duplicate"):
        load_supervisor_state(artifact_for(relative, duplicate), root=tmp_path)


def test_paths_are_root_confined_and_symlinks_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(PersistenceError, match=r"relative|escape"):
        persist_supervisor_state(state(), root=tmp_path, directory=Path("../escape"))
    with pytest.raises(PersistenceError, match=r"relative|escape"):
        load_supervisor_state(
            StateArtifact(Path("../escape.json"), "sha256:" + "c" * 64, 1), root=tmp_path
        )

    outside = tmp_path.parent / f"{tmp_path.name}-outside-state"
    outside.mkdir(exist_ok=True)
    target = outside / "state.json"
    target.write_bytes(canonical_record_bytes(state()))
    link = tmp_path / "linked-state.json"
    try:
        link.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")
    raw = target.read_bytes()
    with pytest.raises(PersistenceError, match="symlink"):
        load_supervisor_state(artifact_for(Path("linked-state.json"), raw), root=tmp_path)


def test_oversized_state_is_rejected_before_parse(tmp_path: Path) -> None:
    relative = Path("hostile/oversized.json")
    path = tmp_path / relative
    path.parent.mkdir()
    raw = b"{" + b" " * 100
    path.write_bytes(raw)

    with pytest.raises(PersistenceError, match="exceeds"):
        load_supervisor_state(artifact_for(relative, raw), root=tmp_path, max_bytes=32)


def test_poisoned_digest_destination_is_never_overwritten(tmp_path: Path) -> None:
    raw = canonical_record_bytes(state())
    digest = hashlib.sha256(raw).hexdigest()
    destination = tmp_path / "states" / f"{digest}.json"
    destination.parent.mkdir()
    destination.write_bytes(b"poison")

    with pytest.raises(PersistenceError, match=r"collision|poison|hash"):
        persist_supervisor_state(state(), root=tmp_path)
    assert destination.read_bytes() == b"poison"


def test_identical_existing_and_concurrent_publications_are_idempotent(tmp_path: Path) -> None:
    first = persist_supervisor_state(state(), root=tmp_path)
    second = persist_supervisor_state(state(), root=tmp_path)

    assert first == second
    assert load_supervisor_state(second, root=tmp_path) == state()


def test_simultaneous_writers_publish_the_same_exact_state(tmp_path: Path) -> None:
    workers = 8
    barrier = threading.Barrier(workers)

    def publish(_: int) -> StateArtifact:
        barrier.wait()
        return persist_supervisor_state(state(), root=tmp_path)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        artifacts = tuple(executor.map(publish, range(workers)))

    assert len(set(artifacts)) == 1
    assert load_supervisor_state(artifacts[0], root=tmp_path) == state()


def test_publication_failure_leaves_no_partial_destination_or_owned_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_link(source: Path | str, destination: Path | str) -> None:
        raise OSError("simulated publication interruption")

    monkeypatch.setattr(os, "link", fail_link)
    with pytest.raises(PersistenceError, match="publication"):
        persist_supervisor_state(state(), root=tmp_path)

    files = tuple((tmp_path / "states").glob("*"))
    assert files == ()


def test_preexisting_unowned_temporary_is_preserved_without_blocking_publication(
    tmp_path: Path,
) -> None:
    raw = canonical_record_bytes(state())
    digest = hashlib.sha256(raw).hexdigest()
    directory = tmp_path / "states"
    directory.mkdir()
    unowned_temporary = directory / f".{digest}.tmp"
    unowned_temporary.write_bytes(b"untrusted-concurrent-or-stale-bytes")

    artifact = persist_supervisor_state(state(), root=tmp_path)

    assert unowned_temporary.read_bytes() == b"untrusted-concurrent-or-stale-bytes"
    assert load_supervisor_state(artifact, root=tmp_path) == state()
