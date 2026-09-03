"""Deterministic TLA+/TLC execution and result-binding tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verify_tla import (
    EXPECTED_JAR_SHA256,
    EXPECTED_TLC_VERSION,
    FormalVerificationError,
    parse_tlc_output,
    verify_formal_result_binding,
    verify_jar,
)


def test_tlc_output_parser_requires_exact_success_and_state_counts() -> None:
    output = """TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)
Model checking completed. No error has been found.
1,234 states generated, 567 distinct states found, 0 states left on queue.
The depth of the complete state graph search is 9.
"""

    parsed = parse_tlc_output(output)

    assert parsed.generated_states == 1234
    assert parsed.distinct_states == 567
    assert parsed.invariant_success is True
    assert parsed.search_depth == 9


@pytest.mark.parametrize(
    ("output", "code"),
    (
        ("Model checking completed. No error has been found.\n", "missing_state_counts"),
        (
            "Error: Invariant SafetyInvariant is violated.\n"
            "4 states generated, 3 distinct states found, 0 states left on queue.\n",
            "invariant_violation",
        ),
        (
            "Model checking completed. No error has been found.\n"
            "4 states generated, 3 distinct states found, 1 states left on queue.\n",
            "incomplete_state_space",
        ),
    ),
)
def test_tlc_output_parser_rejects_ambiguous_incomplete_or_failed_runs(
    output: str, code: str
) -> None:
    with pytest.raises(FormalVerificationError) as captured:
        parse_tlc_output(output)
    assert captured.value.code == code


def test_jar_hash_is_checked_before_tool_execution(tmp_path: Path) -> None:
    jar = tmp_path / "tla2tools.jar"
    jar.write_bytes(b"not the pinned TLC jar")

    with pytest.raises(FormalVerificationError) as captured:
        verify_jar(jar, expected_sha256=EXPECTED_JAR_SHA256)
    assert captured.value.code == "jar_hash_mismatch"


def test_canonical_verifier_includes_offline_formal_result_binding() -> None:
    root = Path(__file__).resolve().parents[1]
    verifier = (root / "scripts" / "verify.py").read_text(encoding="utf-8")

    assert "def check_tla_result()" in verifier
    assert "check_tla_result()" in verifier.split("def main()", 1)[1]


def test_production_formal_result_is_canonical_and_bound_to_model_config_and_tool() -> None:
    root = Path(__file__).resolve().parents[1]

    assert verify_formal_result_binding(root) == ()
    result = json.loads((root / "assurance" / "tla" / "formal-result.json").read_bytes())
    assert result["tool"]["jar_sha256"] == "sha256:" + EXPECTED_JAR_SHA256
    assert result["tool"]["tlc_version"] == EXPECTED_TLC_VERSION
    assert result["execution"]["workers"] == 1
    assert result["execution"]["invariant_success"] is True
    assert result["execution"]["generated_states"] > 0
    assert result["execution"]["distinct_states"] > 0


def test_formal_result_binding_detects_model_drift(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    copied = tmp_path / "repository"
    (copied / "assurance").mkdir(parents=True)
    source = root / "assurance" / "tla"
    import shutil

    shutil.copytree(source, copied / "assurance" / "tla")
    model = copied / "assurance" / "tla" / "Supervisor.tla"
    model.write_bytes(model.read_bytes() + b"\n")

    errors = verify_formal_result_binding(copied)

    assert errors == (
        "formal model byte count mismatch: assurance/tla/Supervisor.tla",
        "formal model SHA-256 mismatch: assurance/tla/Supervisor.tla",
    )
