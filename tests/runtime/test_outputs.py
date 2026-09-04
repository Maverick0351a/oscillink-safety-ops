"""Local closed-file output publication tests."""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import IO, Any

import pytest

from oscillink_safety_ops.runtime import outputs as runtime_outputs
from oscillink_safety_ops.runtime.contracts import ActionRequest
from oscillink_safety_ops.runtime.outputs import OutputError, publish_local_output
from oscillink_safety_ops.runtime.supervisor import canonical_record_bytes

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


def request() -> ActionRequest:
    return ActionRequest.model_validate(
        {
            "request_id": "request:001",
            "run_id": "run:001",
            "created_at": NOW,
            "action": "protective_stop_request",
            "decision_sha256": "sha256:" + "a" * 64,
            "configuration_sha256": "sha256:" + "b" * 64,
            "input_sha256": ("sha256:" + "c" * 64,),
        }
    )


def test_action_request_is_published_at_its_content_address(tmp_path: Path) -> None:
    expected = request()
    raw = canonical_record_bytes(expected)
    digest = hashlib.sha256(raw).hexdigest()

    artifact = runtime_outputs.persist_action_request(expected, root=tmp_path)

    assert artifact.relative_path == Path(f"requests/{digest}.json")
    assert artifact.sha256 == f"sha256:{digest}"
    assert artifact.byte_count == len(raw)
    assert artifact.delivery_mode == "local_closed_file_simulation"
    assert artifact.operational_authority == "none"
    assert (tmp_path / artifact.relative_path).read_bytes() == raw


def test_action_request_round_trip_verifies_exact_bytes(tmp_path: Path) -> None:
    expected = request()
    artifact = runtime_outputs.persist_action_request(expected, root=tmp_path)

    loaded = runtime_outputs.load_action_request(artifact, root=tmp_path)

    assert loaded == expected


def test_action_request_load_rejects_changed_bytes_before_parse(tmp_path: Path) -> None:
    artifact = runtime_outputs.persist_action_request(request(), root=tmp_path)
    path = tmp_path / artifact.relative_path
    raw = path.read_bytes()
    path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])

    with pytest.raises(OutputError) as captured:
        runtime_outputs.load_action_request(artifact, root=tmp_path)

    assert captured.value.code == "hash_mismatch"


def test_action_request_load_rejects_a_valid_request_at_the_wrong_content_address(
    tmp_path: Path,
) -> None:
    expected = request()
    raw = canonical_record_bytes(expected)
    relative = Path("requests/not-the-digest.json")
    destination = tmp_path / relative
    destination.parent.mkdir()
    destination.write_bytes(raw)
    artifact = runtime_outputs.OutputArtifact(
        relative,
        "sha256:" + hashlib.sha256(raw).hexdigest(),
        len(raw),
    )

    with pytest.raises(OutputError) as captured:
        runtime_outputs.load_action_request(artifact, root=tmp_path)

    assert captured.value.code == "content_address_mismatch"


def test_action_request_load_rejects_non_regular_artifact(tmp_path: Path) -> None:
    raw = canonical_record_bytes(request())
    digest = hashlib.sha256(raw).hexdigest()
    relative = Path(f"requests/{digest}.json")
    (tmp_path / relative).mkdir(parents=True)
    artifact = runtime_outputs.OutputArtifact(relative, f"sha256:{digest}", len(raw))

    with pytest.raises(OutputError) as captured:
        runtime_outputs.load_action_request(artifact, root=tmp_path)

    assert captured.value.code == "non_regular"


def test_action_request_load_rejects_noncanonical_valid_json(tmp_path: Path) -> None:
    raw = request().model_dump_json(indent=2).encode("utf-8") + b"\n"
    digest = hashlib.sha256(raw).hexdigest()
    relative = Path(f"requests/{digest}.json")
    destination = tmp_path / relative
    destination.parent.mkdir()
    destination.write_bytes(raw)
    artifact = runtime_outputs.OutputArtifact(relative, f"sha256:{digest}", len(raw))

    with pytest.raises(OutputError) as captured:
        runtime_outputs.load_action_request(artifact, root=tmp_path)

    assert captured.value.code == "noncanonical_request"


def test_action_request_identity_cannot_be_reused_for_changed_bytes(tmp_path: Path) -> None:
    first = request()
    runtime_outputs.persist_action_request(first, root=tmp_path)
    changed = first.model_copy(update={"created_at": NOW + timedelta(microseconds=1)})

    with pytest.raises(OutputError) as captured:
        runtime_outputs.persist_action_request(changed, root=tmp_path)

    assert captured.value.code == "request_identity_collision"


def test_action_request_load_rejects_symlinked_parent(tmp_path: Path) -> None:
    raw = canonical_record_bytes(request())
    digest = hashlib.sha256(raw).hexdigest()
    outside = tmp_path.parent / f"{tmp_path.name}-outside-requests"
    outside.mkdir(exist_ok=True)
    (outside / f"{digest}.json").write_bytes(raw)
    linked = tmp_path / "linked"
    try:
        linked.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")
    artifact = runtime_outputs.OutputArtifact(
        Path(f"linked/{digest}.json"),
        f"sha256:{digest}",
        len(raw),
    )

    with pytest.raises(OutputError) as captured:
        runtime_outputs.load_action_request(artifact, root=tmp_path)

    assert captured.value.code == "path_symlink"


def test_action_request_load_rejects_substitution_while_opening(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = runtime_outputs.persist_action_request(request(), root=tmp_path)
    path = tmp_path / artifact.relative_path
    replacement = path.with_suffix(".replacement")
    replacement.write_bytes(
        canonical_record_bytes(request().model_copy(update={"request_id": "request:002"}))
    )
    original_open = Path.open
    replaced = False

    def substitute_then_open(
        candidate: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        nonlocal replaced
        if candidate == path and not replaced:
            replaced = True
            replacement.replace(path)
        return original_open(candidate, mode, buffering, encoding, errors, newline)

    monkeypatch.setattr(Path, "open", substitute_then_open)

    with pytest.raises(OutputError) as captured:
        runtime_outputs.load_action_request(artifact, root=tmp_path)

    assert captured.value.code == "substitution"


def test_action_request_load_rejects_oversized_bytes_before_parse(tmp_path: Path) -> None:
    relative = Path("requests/" + "f" * 64 + ".json")
    destination = tmp_path / relative
    destination.parent.mkdir()
    raw = b"{" + b" " * 100
    destination.write_bytes(raw)
    artifact = runtime_outputs.OutputArtifact(relative, "sha256:" + "f" * 64, len(raw))

    with pytest.raises(OutputError) as captured:
        runtime_outputs.load_action_request(artifact, root=tmp_path, max_bytes=32)

    assert captured.value.code == "oversized"


def test_action_request_load_rejects_actual_oversized_file_despite_small_claim(
    tmp_path: Path,
) -> None:
    relative = Path("requests/" + "f" * 64 + ".json")
    destination = tmp_path / relative
    destination.parent.mkdir()
    destination.write_bytes(b"{" + b" " * 100)
    artifact = runtime_outputs.OutputArtifact(relative, "sha256:" + "f" * 64, 1)

    with pytest.raises(OutputError) as captured:
        runtime_outputs.load_action_request(artifact, root=tmp_path, max_bytes=32)

    assert captured.value.code == "oversized"


def test_action_request_load_requires_its_immutable_identity_binding(tmp_path: Path) -> None:
    expected = request()
    artifact = runtime_outputs.persist_action_request(expected, root=tmp_path)
    identity_digest = hashlib.sha256(expected.request_id.encode("utf-8")).hexdigest()
    (tmp_path / "requests" / "by-id" / f"{identity_digest}.json").unlink()

    with pytest.raises(OutputError) as captured:
        runtime_outputs.load_action_request(artifact, root=tmp_path)

    assert captured.value.code == "missing_identity_binding"


def test_output_publication_is_atomic_verified_and_idempotent_for_exact_bytes(
    tmp_path: Path,
) -> None:
    raw = b'{"delivery_mode":"local_closed_file_simulation","operational_authority":"none"}\n'

    first = publish_local_output(raw, root=tmp_path, relative_path=Path("reports/result.json"))
    second = publish_local_output(raw, root=tmp_path, relative_path=Path("reports/result.json"))

    assert first == second
    assert first.sha256 == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert first.byte_count == len(raw)
    assert (tmp_path / first.relative_path).read_bytes() == raw
    assert not tuple((tmp_path / "reports").glob("*.tmp"))


def test_output_rejects_escape_symlink_special_and_existing_different_bytes(tmp_path: Path) -> None:
    raw = b"{}\n"
    publish_local_output(raw, root=tmp_path, relative_path=Path("result.json"))
    with pytest.raises(OutputError, match="collision"):
        publish_local_output(
            b'{"different":true}\n', root=tmp_path, relative_path=Path("result.json")
        )
    with pytest.raises(OutputError, match=r"relative|escape"):
        publish_local_output(raw, root=tmp_path, relative_path=Path("../escape.json"))
    with pytest.raises(OutputError, match="regular"):
        publish_local_output(raw, root=tmp_path, relative_path=Path("."))

    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")
    with pytest.raises(OutputError, match="symlink"):
        publish_local_output(raw, root=tmp_path, relative_path=Path("linked/result.json"))


def test_concurrent_writers_publish_one_verified_exact_artifact(tmp_path: Path) -> None:
    raw = b'{"report_format":"oscillink-runtime-replay-report-v1"}\n'

    with ThreadPoolExecutor(max_workers=8) as pool:
        artifacts = list(
            pool.map(
                lambda _: publish_local_output(
                    raw, root=tmp_path, relative_path=Path("concurrent/report.json")
                ),
                range(24),
            )
        )

    assert len(set(artifacts)) == 1
    assert (tmp_path / "concurrent/report.json").read_bytes() == raw
