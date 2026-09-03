"""Bounded collision-safe exact-byte supervisor-state persistence tests."""

from __future__ import annotations

import hashlib
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from oscillink_safety_ops.runtime.contracts import SupervisorStateRecord
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
)
from oscillink_safety_ops.runtime.supervisor import canonical_record_bytes

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
CONFIG = "sha256:" + "a" * 64
INPUT = "sha256:" + "b" * 64


def state() -> SupervisorStateRecord:
    initial = initial_supervisor_state(
        run_id="run:001",
        evaluation_time=NOW,
        configuration_sha256=CONFIG,
        input_sha256=(INPUT,),
    )
    return apply_policy_evaluation(
        initial,
        PolicyEvaluation("inhibit_request", "missing_source", ("missing_source",)),
        evaluation_time=NOW,
        input_sha256=(INPUT,),
        configuration_sha256=CONFIG,
    ).state


def artifact_for(relative_path: Path, raw: bytes) -> StateArtifact:
    return StateArtifact(
        relative_path=relative_path,
        sha256="sha256:" + hashlib.sha256(raw).hexdigest(),
        byte_count=len(raw),
    )


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
