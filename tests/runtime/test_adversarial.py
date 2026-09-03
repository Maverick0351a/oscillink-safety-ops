"""Adversarial replay and forbidden production-boundary tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fuzz.runtime_observation_fuzz import exercise_seed
from scripts.verify_runtime_boundary import scan_core_boundary


@pytest.mark.parametrize(
    "source,marker",
    (
        ("import socket\nsocket.socket()\n", "network client"),
        ("import requests\nrequests.get('https://controller.invalid')\n", "network client"),
        ("node.create_publisher(object, '/robot/stop', 1)\n", "ROS publisher"),
        ("node.create_client(object, '/robot/reset')\n", "service/action client"),
        ("plc_writer.write(b'1')\n", "PLC writer"),
        ("controller_address = '10.0.0.9'\n", "controller address"),
        ("machine_credentials = {'user': 'x'}\n", "machine credential"),
        ("remote_reset()\n", "remote reset"),
        ("reverse_control_callback = lambda command: command\n", "reverse-control callback"),
        ("exec('x = 1')\n", "dynamic execution"),
    ),
)
def test_boundary_scanner_rejects_each_live_control_surface(
    tmp_path: Path, source: str, marker: str
) -> None:
    package = tmp_path / "core"
    package.mkdir()
    (package / "bad.py").write_text(source, encoding="utf-8")

    errors = scan_core_boundary(package)

    assert errors
    assert marker in "\n".join(errors)


def test_boundary_scanner_ignores_explicit_negative_documentation(tmp_path: Path) -> None:
    package = tmp_path / "core"
    package.mkdir()
    (package / "safe.py").write_text(
        '"""No ROS publishers, PLC writers, controller addresses, machine credentials, '
        "remote reset, reverse-control callbacks, sockets/network clients, "
        'or dynamic execution."""\n'
        "DELIVERY_MODE = 'local_closed_file_simulation'\n",
        encoding="utf-8",
    )

    assert scan_core_boundary(package) == ()


def test_repository_core_has_no_live_machine_or_network_boundary() -> None:
    root = Path(__file__).resolve().parents[2]
    assert scan_core_boundary(root / "src" / "oscillink_safety_ops") == ()


def test_boundary_scanner_rejects_symlinked_python_source(tmp_path: Path) -> None:
    package = tmp_path / "core"
    package.mkdir()
    target = tmp_path / "outside.py"
    target.write_text("x = 1\n", encoding="utf-8")
    link = package / "linked.py"
    try:
        os.symlink(target, link)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    assert "symlink" in "\n".join(scan_core_boundary(package))


def test_minimized_fuzz_corpus_is_committed_and_exercised() -> None:
    root = Path(__file__).resolve().parents[2]
    seeds = sorted((root / "fuzz" / "corpus" / "runtime").glob("*.hex"))
    assert {seed.name for seed in seeds} == {
        "blank-line.hex",
        "duplicate-key.hex",
        "invalid-utf8.hex",
        "reserved-identity.hex",
        "truncated-json.hex",
    }
    for seed in seeds:
        exercise_seed(seed)
