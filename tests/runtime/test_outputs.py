"""Local closed-file output publication tests."""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from oscillink_safety_ops.runtime.outputs import OutputError, publish_local_output


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
