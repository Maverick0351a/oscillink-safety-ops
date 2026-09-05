from __future__ import annotations

import hashlib
import importlib
import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from oscillink_safety_ops.release import ReleaseArtifact

COMMIT = "a" * 40
VERSION = "0.1.0a2"


def test_release_artifact_rejects_non_basename_path() -> None:
    with pytest.raises(ValidationError, match="name"):
        ReleaseArtifact(
            name="../outside.whl",
            sha256="0" * 64,
            size_bytes=1,
        )


def test_create_release_files_are_deterministic_and_portable(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    wheel = artifacts / "oscillink_safety_ops-0.1.0a2-py3-none-any.whl"
    source = artifacts / "oscillink_safety_ops-0.1.0a2.tar.gz"
    wheel.write_bytes(b"wheel-bytes")
    source.write_bytes(b"source-bytes")
    output = tmp_path / "release"

    module.create_release_files(
        artifacts=[wheel, source],
        output_dir=output,
        package_version=VERSION,
        candidate_commit=COMMIT,
    )

    manifest = json.loads((output / "release-verification.json").read_text(encoding="utf-8"))
    assert manifest == {
        "artifacts": [
            {
                "name": source.name,
                "sha256": hashlib.sha256(b"source-bytes").hexdigest(),
                "size_bytes": len(b"source-bytes"),
            },
            {
                "name": wheel.name,
                "sha256": hashlib.sha256(b"wheel-bytes").hexdigest(),
                "size_bytes": len(b"wheel-bytes"),
            },
        ],
        "candidate_commit": COMMIT,
        "package_name": "oscillink-safety-ops",
        "package_version": VERSION,
        "schema_version": 1,
    }
    assert (output / "SHA256SUMS.txt").read_text(encoding="utf-8") == (
        f"{hashlib.sha256(b'source-bytes').hexdigest()}  {source.name}\n"
        f"{hashlib.sha256(b'wheel-bytes').hexdigest()}  {wheel.name}\n"
    )


def test_verify_release_directory_uses_only_isolated_files(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    artifacts = tmp_path / "originals"
    artifacts.mkdir()
    wheel = artifacts / "oscillink_safety_ops-0.1.0a2-py3-none-any.whl"
    source = artifacts / "oscillink_safety_ops-0.1.0a2.tar.gz"
    wheel.write_bytes(b"wheel-bytes")
    source.write_bytes(b"source-bytes")
    isolated = tmp_path / "isolated"
    module.create_release_files(
        artifacts=[wheel, source],
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
    )
    shutil.copy2(wheel, isolated / wheel.name)
    shutil.copy2(source, isolated / source.name)
    shutil.rmtree(artifacts)

    manifest = module.verify_release_directory(isolated)

    assert manifest.package_version == VERSION
    assert manifest.candidate_commit == COMMIT


def test_verify_release_directory_rejects_changed_artifact_bytes(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    artifacts = tmp_path / "originals"
    artifacts.mkdir()
    artifact = artifacts / "oscillink_safety_ops-0.1.0a2.tar.gz"
    artifact.write_bytes(b"source-bytes")
    isolated = tmp_path / "isolated"
    module.create_release_files(
        artifacts=[artifact],
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
    )
    shutil.copy2(artifact, isolated / artifact.name)
    shutil.rmtree(artifacts)
    (isolated / artifact.name).write_bytes(b"tampered!!!!")

    with pytest.raises(ValueError, match="artifact checksum does not match"):
        module.verify_release_directory(isolated)


def test_verify_release_directory_rejects_declared_size_drift(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    artifacts = tmp_path / "originals"
    artifacts.mkdir()
    artifact = artifacts / "oscillink_safety_ops-0.1.0a2.tar.gz"
    artifact.write_bytes(b"source-bytes")
    isolated = tmp_path / "isolated"
    module.create_release_files(
        artifacts=[artifact],
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
    )
    shutil.copy2(artifact, isolated / artifact.name)
    manifest_path = isolated / "release-verification.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][0]["size_bytes"] += 1
    manifest_path.write_bytes(
        (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    )

    with pytest.raises(ValueError, match="artifact size does not match"):
        module.verify_release_directory(isolated)


def test_verify_release_directory_rejects_checksum_manifest_drift(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    artifacts = tmp_path / "originals"
    artifacts.mkdir()
    artifact = artifacts / "oscillink_safety_ops-0.1.0a2.tar.gz"
    artifact.write_bytes(b"source-bytes")
    isolated = tmp_path / "isolated"
    module.create_release_files(
        artifacts=[artifact],
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
    )
    shutil.copy2(artifact, isolated / artifact.name)
    (isolated / "SHA256SUMS.txt").write_text(
        f"{'0' * 64}  {artifact.name}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="checksum file does not match"):
        module.verify_release_directory(isolated)


def test_verify_release_directory_rejects_unmanifested_files(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    artifacts = tmp_path / "originals"
    artifacts.mkdir()
    artifact = artifacts / "oscillink_safety_ops-0.1.0a2.tar.gz"
    artifact.write_bytes(b"source-bytes")
    isolated = tmp_path / "isolated"
    module.create_release_files(
        artifacts=[artifact],
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
    )
    shutil.copy2(artifact, isolated / artifact.name)
    (isolated / "unexpected.txt").write_text("not in manifest\n", encoding="utf-8")

    with pytest.raises(ValueError, match="file set does not match"):
        module.verify_release_directory(isolated)


def test_verify_release_directory_requires_regular_artifacts(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    artifacts = tmp_path / "originals"
    artifacts.mkdir()
    artifact = artifacts / "oscillink_safety_ops-0.1.0a2.tar.gz"
    artifact.write_bytes(b"source-bytes")
    isolated = tmp_path / "isolated"
    module.create_release_files(
        artifacts=[artifact],
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
    )
    (isolated / artifact.name).mkdir()

    with pytest.raises(ValueError, match="artifact must be a regular file"):
        module.verify_release_directory(isolated)


def test_release_manifest_cli_creates_candidate_files(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    artifact = tmp_path / "oscillink_safety_ops-0.1.0a2.tar.gz"
    artifact.write_bytes(b"source-bytes")
    output = tmp_path / "candidate"

    result = module.main(
        [
            "create",
            "--artifact",
            str(artifact),
            "--output-dir",
            str(output),
            "--package-version",
            VERSION,
            "--candidate-commit",
            COMMIT,
        ]
    )

    assert result == 0
    assert (output / "release-verification.json").is_file()
    assert (output / "SHA256SUMS.txt").is_file()


def test_release_manifest_cli_verifies_isolated_directory(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    artifact = tmp_path / "oscillink_safety_ops-0.1.0a2.tar.gz"
    artifact.write_bytes(b"source-bytes")
    isolated = tmp_path / "candidate"
    module.create_release_files(
        artifacts=[artifact],
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
    )
    shutil.copy2(artifact, isolated / artifact.name)

    result = module.main(["verify", "--release-dir", str(isolated)])

    assert result == 0
    assert capsys.readouterr().out == (
        f"verified release: package=oscillink-safety-ops version={VERSION} "
        f"commit={COMMIT} artifacts=1\n"
    )


def test_release_verification_schema_is_exported() -> None:
    schemas = importlib.import_module("scripts.export_schemas").SCHEMAS

    assert "release-verification.schema.json" in schemas
