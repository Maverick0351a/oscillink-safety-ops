"""Fuzz bounded observation and replay parsing without external effects."""

from __future__ import annotations

import sys
from pathlib import Path

from oscillink_safety_ops.runtime.contracts import (
    CommandObservation,
    PhysicalObservation,
    SharedDependencyObservation,
    SourceHealthObservation,
    bind_observation_bytes,
)
from oscillink_safety_ops.runtime.replay import ReplayError, parse_observation_jsonl


def exercise_bytes(data: bytes) -> None:
    """libFuzzer entry body: only documented parser rejections may escape internally."""

    try:
        parse_observation_jsonl(data)
    except (ReplayError, TypeError, ValueError):
        pass
    observation = data[:-1] if data.endswith(b"\n") else data
    for model in (
        CommandObservation,
        PhysicalObservation,
        SharedDependencyObservation,
        SourceHealthObservation,
    ):
        try:
            bind_observation_bytes(observation, model)
        except (TypeError, ValueError):
            pass


def TestOneInput(data: bytes) -> None:
    exercise_bytes(data)


def exercise_seed(path: Path) -> None:
    """Decode and execute one committed minimized hexadecimal seed."""

    raw_hex = path.read_text(encoding="ascii").strip()
    data = bytes.fromhex(raw_hex)
    try:
        parse_observation_jsonl(data)
    except ReplayError:
        pass
    else:
        raise AssertionError(f"malformed seed was accepted: {path.name}")
    exercise_bytes(data)


def main(argv: list[str] | None = None) -> None:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments:
        for name in arguments:
            exercise_seed(Path(name))
        print(f"fuzz seeds: ok ({len(arguments)})")
        return
    try:
        import atheris  # type: ignore[import-untyped]
    except ImportError as error:
        raise SystemExit(
            "pass seed paths, or install optional atheris for mutation fuzzing"
        ) from error
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
