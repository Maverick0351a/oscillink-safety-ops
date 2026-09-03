"""Generate deterministic release SBOM and bounded provenance metadata."""

from __future__ import annotations

import argparse
import json
import stat
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _locked_components(root: Path) -> list[dict[str, object]]:
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    components: list[dict[str, object]] = []
    for package in lock["package"]:
        name = package["name"]
        version = package.get("version")
        source = package.get("source", {})
        if name == "oscillink-safety-ops" or type(version) is not str:
            continue
        component: dict[str, object] = {
            "bom-ref": f"pkg:pypi/{name}@{version}",
            "name": name,
            "purl": f"pkg:pypi/{name}@{version}",
            "type": "library",
            "version": version,
        }
        hashes: list[dict[str, str]] = []
        sdist = package.get("sdist")
        if type(sdist) is dict and type(sdist.get("hash")) is str:
            algorithm, digest = sdist["hash"].split(":", 1)
            if algorithm == "sha256":
                hashes.append({"alg": "SHA-256", "content": digest})
        if hashes:
            component["hashes"] = hashes
        if "registry" not in source:
            component["properties"] = [{"name": "oscillink:source", "value": "non-registry"}]
        components.append(component)
    return sorted(components, key=lambda item: (str(item["name"]), str(item["version"])))


def _copy_canonical_json(source: Path, destination: Path) -> None:
    metadata = source.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"release evidence source must be regular: {source.name}")
    value = json.loads(source.read_bytes())
    raw = canonical_json(value)
    if raw != source.read_bytes():
        raise ValueError(f"release evidence source is not canonical JSON: {source.name}")
    destination.write_bytes(raw)


def create_release_evidence(
    *, root: Path, output_dir: Path, package_version: str, candidate_commit: str
) -> None:
    if len(candidate_commit) != 40 or any(
        character not in "0123456789abcdef" for character in candidate_commit
    ):
        raise ValueError("candidate commit must be 40 lowercase hexadecimal characters")
    output_dir.mkdir(parents=True, exist_ok=True)
    sbom: dict[str, Any] = {
        "bomFormat": "CycloneDX",
        "components": _locked_components(root),
        "metadata": {
            "component": {
                "bom-ref": f"pkg:pypi/oscillink-safety-ops@{package_version}",
                "name": "oscillink-safety-ops",
                "purl": f"pkg:pypi/oscillink-safety-ops@{package_version}",
                "type": "application",
                "version": package_version,
            },
            "properties": [
                {"name": "oscillink:candidate-commit", "value": candidate_commit},
                {"name": "oscillink:dependency-source", "value": "uv.lock"},
            ],
        },
        "specVersion": "1.6",
        "version": 1,
    }
    provenance = {
        "candidate_commit": candidate_commit,
        "evidence_class": "workflow_generated_unsigned_build_metadata",
        "limitations": [
            "not_a_cryptographic_attestation",
            "not_a_deployment_or_publication_record",
            "github_hosted_provenance_not_generated",
        ],
        "package_name": "oscillink-safety-ops",
        "package_version": package_version,
        "repository": "https://github.com/Maverick0351a/oscillink-safety-ops",
        "schema_version": 1,
    }
    (output_dir / "cyclonedx-sbom.json").write_bytes(canonical_json(sbom))
    (output_dir / "provenance.json").write_bytes(canonical_json(provenance))
    _copy_canonical_json(
        root / "benchmark" / "robot_cell_v1" / "metrics.json",
        output_dir / "benchmark-metrics.json",
    )
    _copy_canonical_json(
        root / "assurance" / "tla" / "formal-result.json",
        output_dir / "formal-result.json",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--package-version", required=True)
    parser.add_argument("--candidate-commit", required=True)
    args = parser.parse_args(argv)
    create_release_evidence(
        root=ROOT,
        output_dir=args.output_dir,
        package_version=args.package_version,
        candidate_commit=args.candidate_commit,
    )
    print("release evidence: CycloneDX SBOM, provenance, benchmark, formal result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
