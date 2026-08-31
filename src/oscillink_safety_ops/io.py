"""Strict JSON loading and content-addressed fixture verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .domain import ProposedPlan, SafetyMemoryPacket

MAX_JSON_BYTES = 1024 * 1024


class FixtureIntegrityError(ValueError):
    """Raised when fixture bytes do not match the pinned manifest."""


def _json_object(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"input exceeds {MAX_JSON_BYTES} bytes")
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def load_packet(path: Path) -> SafetyMemoryPacket:
    return SafetyMemoryPacket.model_validate(_json_object(path))


def load_plan(path: Path) -> ProposedPlan:
    return ProposedPlan.model_validate(_json_object(path))


def verify_manifest(path: Path) -> frozenset[str]:
    manifest = _json_object(path)
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise FixtureIntegrityError("manifest files must be a list")
    root = path.parent.resolve()
    verified: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise FixtureIntegrityError("manifest file entry must be an object")
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise FixtureIntegrityError("manifest path and sha256 must be strings")
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            raise FixtureIntegrityError(f"invalid fixture path: {relative}")
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != expected:
            raise FixtureIntegrityError(f"hash mismatch for {relative}")
        verified.add("sha256:" + actual)
    return frozenset(verified)
