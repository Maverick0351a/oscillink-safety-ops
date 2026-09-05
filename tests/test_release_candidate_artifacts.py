from __future__ import annotations

import importlib
import io
import json
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import pytest

COMMIT = "b" * 40
VERSION = "0.1.0a2"


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _complete_artifacts(root: Path) -> list[Path]:
    artifacts = [
        root / "oscillink_safety_ops-0.1.0a2-py3-none-any.whl",
        root / "oscillink_safety_ops-0.1.0a2.tar.gz",
        root / "cyclonedx-sbom.json",
        root / "provenance.json",
        root / "benchmark-metrics.json",
        root / "formal-result.json",
    ]
    artifacts[0].write_bytes(b"wheel")
    artifacts[1].write_bytes(b"sdist")
    artifacts[2].write_bytes(
        _canonical(
            {
                "bomFormat": "CycloneDX",
                "metadata": {"component": {"name": "oscillink-safety-ops", "version": VERSION}},
                "specVersion": "1.6",
                "version": 1,
            }
        )
    )
    artifacts[3].write_bytes(
        _canonical(
            {
                "candidate_commit": COMMIT,
                "evidence_class": "workflow_generated_unsigned_build_metadata",
                "package_name": "oscillink-safety-ops",
                "package_version": VERSION,
                "schema_version": 1,
            }
        )
    )
    artifacts[4].write_bytes(_canonical({"metrics_format": "test", "schema_version": 1}))
    artifacts[5].write_bytes(_canonical({"result_format": "test", "schema_version": 1}))
    return artifacts


def _isolated_release(tmp_path: Path) -> tuple[Any, Path]:
    module = importlib.import_module("scripts.create_release_manifest")
    source = tmp_path / "source"
    source.mkdir()
    artifacts = _complete_artifacts(source)
    isolated = tmp_path / "isolated"
    module.create_release_files(
        artifacts=artifacts,
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
        require_complete=True,
    )
    for artifact in artifacts:
        (isolated / artifact.name).write_bytes(artifact.read_bytes())
    return module, isolated


def test_complete_release_roundtrip_validates_identity_and_artifact_roles(tmp_path: Path) -> None:
    module, isolated = _isolated_release(tmp_path)

    result = module.verify_release_directory(
        isolated,
        expected_version=VERSION,
        expected_commit=COMMIT,
        require_complete=True,
    )

    assert result.package_version == VERSION
    assert len(result.artifacts) == 6


def test_complete_release_rejects_missing_evidence_role(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_manifest")
    root = tmp_path / "artifacts"
    root.mkdir()
    artifacts = _complete_artifacts(root)[:-1]

    with pytest.raises(ValueError, match="required release artifact set"):
        module.create_release_files(
            artifacts=artifacts,
            output_dir=tmp_path / "release",
            package_version=VERSION,
            candidate_commit=COMMIT,
            require_complete=True,
        )


def test_release_verifier_rejects_noncanonical_manifest_json(tmp_path: Path) -> None:
    module, isolated = _isolated_release(tmp_path)
    path = isolated / "release-verification.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(value, indent=4) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="canonical JSON"):
        module.verify_release_directory(isolated, require_complete=True)


def test_release_verifier_rejects_duplicate_manifest_basenames(tmp_path: Path) -> None:
    module, isolated = _isolated_release(tmp_path)
    path = isolated / "release-verification.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["artifacts"].append(value["artifacts"][0])
    path.write_bytes(_canonical(value))

    with pytest.raises(ValueError, match="duplicate artifact basename"):
        module.verify_release_directory(isolated, require_complete=True)


def test_release_verifier_rejects_wrong_expected_identity(tmp_path: Path) -> None:
    module, isolated = _isolated_release(tmp_path)

    with pytest.raises(ValueError, match="package version does not match"):
        module.verify_release_directory(isolated, expected_version="0.1.0a1")
    with pytest.raises(ValueError, match="candidate commit does not match"):
        module.verify_release_directory(isolated, expected_commit="c" * 40)


def test_release_verifier_rejects_noncanonical_json_evidence(tmp_path: Path) -> None:
    module, isolated = _isolated_release(tmp_path)
    sbom = isolated / "cyclonedx-sbom.json"
    value = json.loads(sbom.read_text(encoding="utf-8"))
    sbom.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    # Rebind the changed bytes so this reaches semantic/canonical validation.
    module.create_release_files(
        artifacts=[
            path
            for path in isolated.iterdir()
            if path.name not in {"release-verification.json", "SHA256SUMS.txt"}
        ],
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
        require_complete=True,
    )

    with pytest.raises(ValueError, match="canonical JSON"):
        module.verify_release_directory(isolated, require_complete=True)


def test_release_verifier_rejects_provenance_for_wrong_candidate(tmp_path: Path) -> None:
    module, isolated = _isolated_release(tmp_path)
    provenance = isolated / "provenance.json"
    value = json.loads(provenance.read_text(encoding="utf-8"))
    value["candidate_commit"] = "d" * 40
    provenance.write_bytes(_canonical(value))
    module.create_release_files(
        artifacts=[
            path
            for path in isolated.iterdir()
            if path.name not in {"release-verification.json", "SHA256SUMS.txt"}
        ],
        output_dir=isolated,
        package_version=VERSION,
        candidate_commit=COMMIT,
        require_complete=True,
    )

    with pytest.raises(ValueError, match="provenance candidate commit"):
        module.verify_release_directory(isolated, require_complete=True)


def test_release_evidence_generator_creates_canonical_redacted_metadata(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.create_release_evidence")

    module.create_release_evidence(
        root=Path(__file__).resolve().parents[1],
        output_dir=tmp_path,
        package_version=VERSION,
        candidate_commit=COMMIT,
    )

    for name in (
        "cyclonedx-sbom.json",
        "provenance.json",
        "benchmark-metrics.json",
        "formal-result.json",
    ):
        raw = (tmp_path / name).read_bytes()
        assert raw == _canonical(json.loads(raw))
        assert b"C:/Users/" not in raw and b"C:\\Users\\" not in raw


def test_package_archive_verifier_rejects_prohibited_and_unsafe_members(tmp_path: Path) -> None:
    module = importlib.import_module("scripts.verify_package_archives")
    wheel = tmp_path / "oscillink_safety_ops-0.1.0a2-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("../escape", b"x")
    sdist = tmp_path / "oscillink_safety_ops-0.1.0a2.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        item = tarfile.TarInfo("oscillink_safety_ops-0.1.0a2/.hermes/private.md")
        item.size = 1
        archive.addfile(item, io.BytesIO(b"x"))

    with pytest.raises(ValueError, match=r"unsafe|prohibited"):
        module.verify_package_archives(tmp_path, VERSION)


@pytest.mark.parametrize("name", ("C:/escape", "safe//escape", "//server/share"))
def test_package_archive_path_policy_is_cross_platform(name: str) -> None:
    module = importlib.import_module("scripts.verify_package_archives")

    with pytest.raises(ValueError, match="unsafe archive member path"):
        module._check_name(name, allow_runtime_package=True)
