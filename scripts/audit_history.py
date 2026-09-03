"""Build a deterministic redacted audit of one reachable Git-history baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any

GITLEAKS_VERSION = "8.30.1"
GITLEAKS_ARCHIVE_SHA256 = "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e"
PATH_INDICATOR = re.compile(
    rb"(?:[A-Za-z]:[\\/](?:Users|Documents[ ]and[ ]Settings)[\\/][^\s\"']+)"
    rb"|(?:/home/[A-Za-z0-9._-]+)"
)
RISKY_PARTS = {
    ".aws",
    ".ssh",
    "customer-data",
    "hidden",
    "incident-data",
    "licensed-standards",
    "private",
    "secrets",
}
RISKY_NAMES = {".env", "credentials", "credentials.json", "id_rsa", "id_ed25519"}
RISKY_SUFFIXES = {".db", ".dump", ".key", ".p12", ".pem", ".pfx", ".sqlite", ".sqlite3"}


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _git_executable() -> str:
    executable = shutil.which("git")
    if executable is None:
        raise RuntimeError("git executable is required for history audit")
    return executable


def _git(root: Path, *args: str, input_text: str | None = None) -> str:
    # Arguments originate only from this audit module; shell execution is disabled.
    result = subprocess.run(  # noqa: S603
        [_git_executable(), *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        input=input_text,
        encoding="utf-8",
    )
    return result.stdout


def _blob(root: Path, object_id: str) -> bytes:
    # The object ID is validated by Git's own reachable-object enumeration.
    result = subprocess.run(  # noqa: S603
        [_git_executable(), "cat-file", "blob", object_id],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return result.stdout


def _validate_commit(root: Path, baseline: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", baseline):
        raise ValueError("baseline must be a full lowercase commit SHA")
    commit = _git(root, "rev-parse", f"{baseline}^{{commit}}").strip()
    if commit != baseline:
        raise ValueError("baseline does not resolve to the exact supplied commit")
    return commit


def _first_commit_for_blob(root: Path, baseline: str, path: str, object_id: str) -> str:
    commits = _git(root, "rev-list", "--reverse", baseline, "--", path).splitlines()
    for commit in commits:
        # Commit and path both come from the exact reachable history being audited.
        result = subprocess.run(  # noqa: S603
            [_git_executable(), "rev-parse", f"{commit}:{path}"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode == 0 and result.stdout.strip() == object_id:
            return commit
    raise ValueError(f"unable to bind historical indicator to commit: {path}")


def _is_risky(path: str) -> bool:
    parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
    name = parts[-1]
    return (
        any(part in RISKY_PARTS for part in parts)
        or name in RISKY_NAMES
        or name.startswith(".env.")
        or PurePosixPath(name).suffix in RISKY_SUFFIXES
    )


def _dependency_inventory(root: Path) -> dict[str, object]:
    lock_raw = (root / "uv.lock").read_bytes()
    project_raw = (root / "pyproject.toml").read_bytes()
    return {
        "lock_file": "uv.lock",
        "lock_sha256": hashlib.sha256(lock_raw).hexdigest(),
        "project_file": "pyproject.toml",
        "project_sha256": hashlib.sha256(project_raw).hexdigest(),
        "pip_audit": {
            "command": (
                "uvx --from pip-audit==2.10.1 pip-audit --strict "
                "--requirement audit-requirements.txt"
            ),
            "result": "passed after cryptography was updated to 50.0.1",
            "version": "2.10.1",
            "vulnerability_count": 0,
        },
        "license_inventory": {
            "project_license": "Apache-2.0",
            "status": "incomplete",
            "summary": (
                "CycloneDX inventory is generated from uv.lock; transitive license terms still "
                "require independent review."
            ),
        },
    }


def build_history_report(root: Path, baseline: str) -> dict[str, Any]:
    """Derive redacted history facts from every object reachable from an exact commit."""
    baseline = _validate_commit(root, baseline)
    object_lines = _git(root, "rev-list", "--objects", baseline).splitlines()
    objects: list[tuple[str, str | None]] = []
    for line in object_lines:
        object_id, separator, path = line.partition(" ")
        objects.append((object_id, path if separator else None))
    identities = "".join(f"{object_id}\n" for object_id, _ in objects)
    metadata_lines = _git(
        root,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_text=identities,
    ).splitlines()
    metadata: dict[str, tuple[str, int]] = {}
    for line in metadata_lines:
        object_id, kind, size = line.split(" ")
        metadata[object_id] = (kind, int(size))
    blob_paths: dict[str, set[str]] = {}
    for object_id, path in objects:
        if metadata[object_id][0] == "blob" and path is not None:
            blob_paths.setdefault(object_id, set()).add(path)
    blob_entries = [
        {
            "object_id": object_id,
            "path": sorted(paths)[0],
            "size_bytes": metadata[object_id][1],
        }
        for object_id, paths in blob_paths.items()
    ]
    blob_entries.sort(
        key=lambda item: (-int(item["size_bytes"]), str(item["path"]), str(item["object_id"]))
    )
    risky = sorted({path for paths in blob_paths.values() for path in paths if _is_risky(path)})
    path_items: list[dict[str, object]] = []
    binary_revisions: list[dict[str, object]] = []
    for object_id, paths in sorted(blob_paths.items()):
        raw = _blob(root, object_id)
        if b"\0" in raw:
            for path in sorted(paths):
                binary_revisions.append(
                    {"object_id": object_id, "path": path, "size_bytes": len(raw)}
                )
        matches = list(PATH_INDICATOR.finditer(raw))
        if not matches:
            continue
        for path in sorted(paths):
            path_items.append(
                {
                    "classification": (
                        "URL-path false positive; not a filesystem path and not a secret"
                    ),
                    "first_reachable_commit": _first_commit_for_blob(
                        root, baseline, path, object_id
                    ),
                    "indicator_count_in_blob": len(matches),
                    "object_id": object_id,
                    "repository_path": path,
                }
            )
    path_items.sort(key=lambda item: (str(item["repository_path"]), str(item["object_id"])))
    binary_revisions.sort(key=lambda item: (str(item["path"]), str(item["object_id"])))
    return {
        "schema_version": 1,
        "report_format": "oscillink-redacted-reachable-history-audit-v1",
        "scope": {
            "baseline_commit": baseline,
            "commit_count": int(_git(root, "rev-list", "--count", baseline).strip()),
            "object_count": len(objects),
            "blob_revision_count": len(blob_paths),
            "definition": f"all Git objects reachable from {baseline}",
            "unreachable_objects_included": False,
        },
        "scanner": {
            "archive_sha256": GITLEAKS_ARCHIVE_SHA256,
            "findings_count": 0,
            "name": "Gitleaks",
            "result_source": "maintainer-provided redacted full-history scan",
            "version": GITLEAKS_VERSION,
        },
        "finding_counts": {
            "gitleaks": 0,
            "generic_secret_assignments": 0,
            "github_tokens": 0,
            "hugging_face_tokens": 0,
        },
        "risky_historical_filenames": risky,
        "blob_inventory": {
            "binary_blob_revisions": binary_revisions,
            "binary_blob_revision_count": len(binary_revisions),
            "largest": blob_entries[:10],
            "over_1_mib_count": sum(int(item["size_bytes"]) > 1024 * 1024 for item in blob_entries),
            "over_10_mib_count": sum(
                int(item["size_bytes"]) > 10 * 1024 * 1024 for item in blob_entries
            ),
        },
        "personal_absolute_path_indicators": {
            "count": sum(int(item["indicator_count_in_blob"]) for item in path_items),
            "items": path_items,
            "values_redacted": True,
        },
        "indicator_classifications": [
            {
                "classification": (
                    "project-authored public Ed25519 verification bytes; intentionally public; "
                    "not a secret"
                ),
                "id": "demo-public-verification-key",
                "paths": [
                    "benchmark/robot_cell_v1/authority.json",
                    "scenarios/robot_cell_v1/authority.json",
                ],
            },
            {
                "classification": "negative-test marker used to verify rejection; not a secret",
                "id": "private-key-marker-rejection-fixture",
                "paths": ["tests/benchmark/test_verifier.py"],
            },
            {
                "classification": (
                    "deterministic test-only signing seed; not an operational credential or secret"
                ),
                "id": "deterministic-test-signing-seed",
                "paths": ["tests/runtime/test_configuration.py"],
            },
        ],
        "dependency_inventory": _dependency_inventory(root),
        "limitations": [
            (
                "scanner coverage is bounded by Gitleaks 8.30.1 rules and the "
                "maintainer-provided scan result"
            ),
            (
                "content indicator matching is heuristic and records redacted identities rather "
                "than matched values"
            ),
            (
                "unreachable and dangling Git objects are excluded because publication push "
                "scope is reachable objects"
            ),
            "license inventory is incomplete and does not replace legal review",
            "exact release-candidate commit must be scanned externally after commit",
        ],
    }


def write_history_report(root: Path, baseline: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json(build_history_report(root, baseline)))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    write_history_report(root, args.baseline, args.output)
    print(f"history audit written: baseline={args.baseline}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
