"""Canonical local verification gate."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".json", ".toml", ".yaml", ".yml", ".txt"}


def executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        raise SystemExit(f"required executable not found: {name}")
    return resolved


def run(*command: str) -> None:
    print("+", " ".join(command), flush=True)
    resolved = (executable(command[0]), *command[1:])
    subprocess.run(resolved, cwd=ROOT, check=True)  # noqa: S603


def repository_files() -> list[Path]:
    result = subprocess.run(  # noqa: S603 -- resolved trusted git executable
        [executable("git"), "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def check_text_hygiene() -> None:
    home_marker = "C:" + "\\Users\\"
    secret_pattern = re.compile(
        r"(?i)(api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*['\"][^'\"]+"
    )
    errors: list[str] = []
    for path in repository_files():
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        raw = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        if b"\r\n" in raw or b"\r" in raw:
            errors.append(f"non-LF line endings: {relative}")
        text = raw.decode("utf-8")
        if home_marker in text:
            errors.append(f"absolute Windows user path: {relative}")
        if path.name != "verify.py" and secret_pattern.search(text):
            errors.append(f"possible embedded secret: {relative}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("text hygiene: ok")


def check_schemas() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from export_schemas import SCHEMAS, render

    for name, schema in SCHEMAS.items():
        expected = render(schema)
        actual = (ROOT / "schemas" / name).read_text(encoding="utf-8")
        if actual != expected:
            raise SystemExit(f"schema is stale: schemas/{name}")
    print("schemas: ok")


def check_fixture() -> None:
    from oscillink_safety_ops.io import load_packet, load_plan, verify_manifest

    fixture = ROOT / "tests" / "fixtures" / "synthetic_press"
    verified = verify_manifest(fixture / "manifest.json")
    packet = load_packet(fixture / "packet.json")
    load_plan(fixture / "plan.json")
    missing = {source.sha256 for source in packet.sources} - verified
    if missing:
        raise SystemExit("fixture packet contains an unpinned source hash")
    print("fixture: ok")


def main() -> None:
    check_text_hygiene()
    check_schemas()
    check_fixture()
    run("uv", "run", "ruff", "check", ".")
    run("uv", "run", "ruff", "format", "--check", ".")
    run("uv", "run", "mypy")
    run("uv", "build")
    run("uv", "run", "python", "-m", "pytest", "-q")
    print("verification: ok")


if __name__ == "__main__":
    main()
