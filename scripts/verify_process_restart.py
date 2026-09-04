"""Verify latch recovery across real process boundaries using only local state artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from oscillink_safety_ops.runtime.contracts import (
    ActionAcknowledgment,
    CommandAttributionRecord,
    RecoveryEvent,
)
from oscillink_safety_ops.runtime.persistence import (
    StateArtifact,
    load_restart_state_or_fail_closed,
    persist_supervisor_state,
)
from oscillink_safety_ops.runtime.policy import PolicyEvaluation
from oscillink_safety_ops.runtime.state_machine import (
    RecoveryConditions,
    apply_policy_evaluation,
    apply_recovery_event,
    assess_reset_readiness,
    initial_supervisor_state,
    observe_action_acknowledgment,
    observe_action_request_timeout,
    record_action_request,
    record_command_attribution_history,
)

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
RUN_ID = "run:process-restart-verification"
CONFIGURATION_SHA256 = "sha256:" + "a" * 64
STARTUP_INPUT_SHA256 = "sha256:" + "b" * 64
REQUEST_SHA256 = "sha256:" + "c" * 64
CHECKPOINT = Path("checkpoint.json")
PHASES = (
    "create",
    "acknowledgment",
    "readiness",
    "reset",
    "rearm",
    "confirm",
    "fresh-start",
)
ADVERSARIAL_CASES = (
    "missing",
    "corrupt",
    "nonlatched-bypass",
    "identity-bypass",
    "partial-publication",
    "stale-checkpoint",
    "conflicting-checkpoint",
)
OUTPUT_UNCERTAINTY_PHASES = (
    "request-pending-create",
    "request-pending-check",
    "output-unresolved-create",
    "output-unresolved-check",
    "request-timeout-create",
    "request-timeout-check",
)
INVALID_RECOVERY_CASES = (
    "reset-not-permitted",
    "rearm-pending",
    "recovery-pending",
    "recovery-confirmed",
)
INVALID_RECOVERY_PHASES = tuple(
    f"invalid-{case}-{operation}"
    for case in INVALID_RECOVERY_CASES
    for operation in ("create", "check")
)
ATTRIBUTION_HISTORY_PHASES = ("attribution-history-create", "attribution-history-check")


def _canonical_json(value: object) -> str:
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n"


def _fail_closed_state(*, run_id: str = RUN_ID, configuration_sha256: str = CONFIGURATION_SHA256):
    initial = initial_supervisor_state(
        run_id=run_id,
        evaluation_time=NOW,
        configuration_sha256=configuration_sha256,
        input_sha256=(STARTUP_INPUT_SHA256,),
    )
    return apply_policy_evaluation(
        initial,
        PolicyEvaluation(
            "inhibit_request",
            "restart_state_unavailable",
            ("restart_state_unavailable",),
        ),
        evaluation_time=NOW,
        input_sha256=(STARTUP_INPUT_SHA256,),
        configuration_sha256=configuration_sha256,
    ).state


def _write_checkpoint(root: Path, artifact: StateArtifact) -> None:
    (root / CHECKPOINT).write_text(
        _canonical_json(
            {
                "relative_path": artifact.relative_path.as_posix(),
                "sha256": artifact.sha256,
                "byte_count": artifact.byte_count,
            }
        ),
        encoding="utf-8",
        newline="",
    )


def _load_checkpoint(root: Path):
    data = json.loads((root / CHECKPOINT).read_bytes())
    artifact = StateArtifact(Path(data["relative_path"]), data["sha256"], data["byte_count"])
    result = load_restart_state_or_fail_closed(
        artifact,
        root=root,
        expected_run_id=RUN_ID,
        expected_configuration_sha256=CONFIGURATION_SHA256,
        fail_closed_state=_fail_closed_state(),
    )
    if result.integrity_state != "verified":
        raise RuntimeError(f"restart failed closed: {result.reason_code}")
    return result.state


def _conditions() -> RecoveryConditions:
    return RecoveryConditions(
        occupancy_clear=True,
        motion_stopped=True,
        sources_healthy=True,
        configuration_unchanged=True,
        output_resolved=True,
    )


def _event(kind: str, offset: int) -> RecoveryEvent:
    return RecoveryEvent.model_validate(
        {
            "event_id": f"recovery:{kind}",
            "run_id": RUN_ID,
            "observed_at": NOW + timedelta(seconds=offset),
            "event_kind": kind,
            "actor_domain": "independent_safety_authority",
            "authorization_state": "externally_authorized",
            "configuration_sha256": CONFIGURATION_SHA256,
            "input_sha256": "sha256:" + format(offset, "064x"),
        }
    )


def _create_latched_state():
    initial = initial_supervisor_state(
        run_id=RUN_ID,
        evaluation_time=NOW,
        configuration_sha256=CONFIGURATION_SHA256,
        input_sha256=(STARTUP_INPUT_SHA256,),
    )
    requested = apply_policy_evaluation(
        initial,
        PolicyEvaluation(
            "protective_stop_request",
            "human_present_with_measured_motion",
            ("human_present_with_measured_motion",),
        ),
        evaluation_time=NOW,
        input_sha256=(STARTUP_INPUT_SHA256,),
        configuration_sha256=CONFIGURATION_SHA256,
    ).state
    return record_action_request(
        requested,
        request_sha256=REQUEST_SHA256,
        evaluation_time=NOW,
        input_sha256=(STARTUP_INPUT_SHA256,),
    ).state


def _acknowledgment() -> ActionAcknowledgment:
    return ActionAcknowledgment.model_validate(
        {
            "acknowledgment_id": "ack:process-restart-verification",
            "run_id": RUN_ID,
            "observed_at": NOW,
            "request_sha256": REQUEST_SHA256,
            "configuration_sha256": CONFIGURATION_SHA256,
            "input_sha256": ("sha256:" + "d" * 64,),
            "status": "received_by_simulated_fixture",
        }
    )


def _run_worker(root: Path, phase: str):
    if phase == "create":
        state = _create_latched_state()
    else:
        state = _load_checkpoint(root)
        conditions = _conditions()
        if phase == "acknowledgment":
            state = observe_action_acknowledgment(
                state,
                _acknowledgment(),
                evaluation_time=NOW,
            ).state
        elif phase == "readiness":
            state = assess_reset_readiness(
                state,
                conditions=conditions,
                evaluation_time=NOW + timedelta(seconds=1),
            ).state
        else:
            kinds = {
                "reset": ("reset", 2),
                "rearm": ("rearm", 3),
                "confirm": ("recovery_confirmed", 4),
                "fresh-start": ("fresh_start", 5),
            }
            kind, offset = kinds[phase]
            state = apply_recovery_event(
                state,
                _event(kind, offset),
                conditions=conditions,
                evaluation_time=NOW + timedelta(seconds=offset),
            ).state
    artifact = persist_supervisor_state(state, root=root)
    _write_checkpoint(root, artifact)
    return {
        "phase": phase,
        "state": state.supervisor_state,
        "latched": state.latched,
        "fresh_start_required": state.fresh_start_required,
        "active_request_sha256": state.active_request_sha256,
        "state_sha256": artifact.sha256,
    }


def _state_at_invalid_recovery_case(case: str):
    conditions = _conditions()
    state = _create_latched_state()
    if case == "reset-not-permitted":
        return assess_reset_readiness(
            state,
            conditions=conditions,
            evaluation_time=NOW + timedelta(seconds=1),
        ).state
    state = observe_action_acknowledgment(state, _acknowledgment(), evaluation_time=NOW).state
    state = assess_reset_readiness(
        state,
        conditions=conditions,
        evaluation_time=NOW + timedelta(seconds=1),
    ).state
    state = apply_recovery_event(
        state,
        _event("reset", 2),
        conditions=conditions,
        evaluation_time=NOW + timedelta(seconds=2),
    ).state
    if case == "rearm-pending":
        return state
    state = apply_recovery_event(
        state,
        _event("rearm", 3),
        conditions=conditions,
        evaluation_time=NOW + timedelta(seconds=3),
    ).state
    if case == "recovery-pending":
        return state
    return apply_recovery_event(
        state,
        _event("recovery_confirmed", 4),
        conditions=conditions,
        evaluation_time=NOW + timedelta(seconds=4),
    ).state


def _run_invalid_recovery_worker(root: Path, phase: str) -> dict[str, object]:
    operation = phase.rsplit("-", 1)[1]
    case = phase.removeprefix("invalid-").removesuffix(f"-{operation}")
    if operation == "create":
        state = _state_at_invalid_recovery_case(case)
        artifact = persist_supervisor_state(state, root=root)
        _write_checkpoint(root, artifact)
        return {"phase": phase, "state_sha256": artifact.sha256}

    state = _load_checkpoint(root)
    active_request = state.active_request_sha256
    probe_kind = "reset" if case == "recovery-confirmed" else "fresh_start"
    probed = apply_recovery_event(
        state,
        _event(probe_kind, 5),
        conditions=_conditions(),
        evaluation_time=NOW + timedelta(seconds=5),
    ).state
    return {
        "case": case,
        "pre_restart_state": state.supervisor_state,
        "fresh_start_required": state.fresh_start_required,
        "post_probe_state": probed.supervisor_state,
        "latched": probed.latched,
        "active_request_preserved": probed.active_request_sha256 == active_request,
    }


def _run_output_uncertainty_worker(root: Path, phase: str) -> dict[str, object]:
    if phase.endswith("-create"):
        state = _create_latched_state()
        if phase == "output-unresolved-create":
            false_acknowledgment = _acknowledgment().model_copy(
                update={"request_sha256": "sha256:" + "e" * 64}
            )
            state = observe_action_acknowledgment(
                state,
                false_acknowledgment,
                evaluation_time=NOW,
            ).state
        elif phase == "request-timeout-create":
            state = observe_action_request_timeout(
                state,
                evaluation_time=NOW + timedelta(seconds=1),
                timeout_seconds=1.0,
            ).state
        artifact = persist_supervisor_state(state, root=root)
        _write_checkpoint(root, artifact)
        return {"phase": phase, "state_sha256": artifact.sha256}

    data = json.loads((root / CHECKPOINT).read_bytes())
    artifact = StateArtifact(Path(data["relative_path"]), data["sha256"], data["byte_count"])
    restart = load_restart_state_or_fail_closed(
        artifact,
        root=root,
        expected_run_id=RUN_ID,
        expected_configuration_sha256=CONFIGURATION_SHA256,
        fail_closed_state=_fail_closed_state(),
    )
    state = restart.state
    reset_probe = assess_reset_readiness(
        state,
        conditions=_conditions(),
        evaluation_time=NOW + timedelta(seconds=1),
    ).state
    return {
        "case": phase.removesuffix("-check"),
        "restart_integrity_state": restart.integrity_state,
        "state": state.supervisor_state,
        "latched": state.latched,
        "active_request_sha256": state.active_request_sha256,
        "output_state": state.output_state,
        "reason_codes": state.reason_codes,
        "reset_probe_state": reset_probe.supervisor_state,
        "reset_probe_latched": reset_probe.latched,
        "acknowledgment_inferred": state.output_state == "acknowledged_unverified",
        "physical_stop": "not_established",
    }


def _run_adversarial_worker(root: Path, case: str) -> dict[str, object]:
    fail_closed = _fail_closed_state()
    expected_run_id = RUN_ID
    expected_state_id: str | None = None
    if case == "missing":
        artifact = StateArtifact(
            Path("states/missing.json"),
            "sha256:" + "e" * 64,
            1,
        )
    elif case == "corrupt":
        artifact = persist_supervisor_state(fail_closed, root=root)
        destination = root / artifact.relative_path
        raw = destination.read_bytes()
        destination.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
    elif case == "nonlatched-bypass":
        initial = initial_supervisor_state(
            run_id=RUN_ID,
            evaluation_time=NOW,
            configuration_sha256=CONFIGURATION_SHA256,
            input_sha256=(STARTUP_INPUT_SHA256,),
        )
        normal = apply_policy_evaluation(
            initial,
            PolicyEvaluation("none", "monitoring_normal", ("monitoring_normal",)),
            evaluation_time=NOW,
            input_sha256=(STARTUP_INPUT_SHA256,),
            configuration_sha256=CONFIGURATION_SHA256,
        ).state
        artifact = persist_supervisor_state(normal, root=root)
    elif case == "identity-bypass":
        artifact = persist_supervisor_state(fail_closed, root=root)
        expected_run_id = "run:substituted"
        fail_closed = _fail_closed_state(run_id=expected_run_id)
    elif case == "partial-publication":
        partial = root / "states" / ".interrupted.tmp"
        partial.parent.mkdir()
        partial.write_bytes(b'{"partial":true')
        artifact = StateArtifact(
            Path("states/final.json"),
            "sha256:" + "f" * 64,
            16,
        )
        expected_state_id = fail_closed.state_id
    elif case == "stale-checkpoint":
        stale = _fail_closed_state()
        current = record_action_request(
            stale,
            request_sha256=REQUEST_SHA256,
            evaluation_time=NOW,
            input_sha256=(STARTUP_INPUT_SHA256,),
        ).state
        artifact = persist_supervisor_state(stale, root=root)
        expected_state_id = current.state_id
    else:
        conflicting = _fail_closed_state()
        expected = _create_latched_state()
        artifact = persist_supervisor_state(conflicting, root=root)
        expected_state_id = expected.state_id

    result = load_restart_state_or_fail_closed(
        artifact,
        root=root,
        expected_run_id=expected_run_id,
        expected_configuration_sha256=CONFIGURATION_SHA256,
        fail_closed_state=fail_closed,
        expected_state_id=expected_state_id,
    )
    return {
        "case": case,
        "integrity_state": result.integrity_state,
        "reason_code": result.reason_code,
        "latched": result.state.latched,
    }


def _run_attribution_history_worker(root: Path, phase: str) -> dict[str, object]:
    if phase.endswith("-create"):
        command = CommandAttributionRecord(
            command_id="command-id:restart-history",
            sequence_number=0,
            observed_at=NOW,
            motion_requested=True,
            input_sha256=STARTUP_INPUT_SHA256,
        )
        state = record_command_attribution_history(
            _create_latched_state(),
            command_history=(command,),
            consumed_command_attributions=("command-id:restart-history:sequence:0",),
            evaluation_time=NOW,
            input_sha256=(STARTUP_INPUT_SHA256,),
        ).state
        artifact = persist_supervisor_state(state, root=root)
        _write_checkpoint(root, artifact)
        return {"phase": phase, "state_sha256": artifact.sha256}

    state = _load_checkpoint(root)
    return {
        "phase": phase,
        "restart_integrity_state": "verified",
        "latched": state.latched,
        "history_count": len(state.command_history),
        "history_command_id": state.command_history[0].command_id,
        "consumed": state.consumed_command_attributions,
        "physical_stop": "not_established",
    }


def _run_parent() -> dict[str, object]:
    phases: list[dict[str, object]] = []
    adversarial_cases: list[dict[str, object]] = []
    output_uncertainty_cases: list[dict[str, object]] = []
    invalid_recovery_cases: list[dict[str, object]] = []
    attribution_history: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="oscillink-process-restart-") as temporary:
        root = Path(temporary)
        for phase in PHASES:
            completed = subprocess.run(  # noqa: S603 -- fixed interpreter and local script
                [sys.executable, __file__, "--worker", phase, "--root", str(root)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or f"worker failed: {phase}")
            phases.append(json.loads(completed.stdout))
        for phase in OUTPUT_UNCERTAINTY_PHASES:
            case_root = root / phase.rsplit("-", 1)[0]
            if phase.endswith("-create"):
                case_root.mkdir()
            completed = subprocess.run(  # noqa: S603 -- fixed interpreter and local script
                [sys.executable, __file__, "--worker", phase, "--root", str(case_root)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or f"worker failed: {phase}")
            result = json.loads(completed.stdout)
            if phase.endswith("-check"):
                output_uncertainty_cases.append(result)
        for phase in INVALID_RECOVERY_PHASES:
            case = phase.removeprefix("invalid-").rsplit("-", 1)[0]
            case_root = root / f"invalid-{case}"
            if phase.endswith("-create"):
                case_root.mkdir()
            completed = subprocess.run(  # noqa: S603 -- fixed interpreter and local script
                [sys.executable, __file__, "--worker", phase, "--root", str(case_root)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or f"worker failed: {phase}")
            result = json.loads(completed.stdout)
            if phase.endswith("-check"):
                invalid_recovery_cases.append(result)
        for case in ADVERSARIAL_CASES:
            case_root = root / case
            case_root.mkdir()
            completed = subprocess.run(  # noqa: S603 -- fixed interpreter and local script
                [sys.executable, __file__, "--worker", case, "--root", str(case_root)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or f"worker failed: {case}")
            adversarial_cases.append(json.loads(completed.stdout))
        attribution_root = root / "attribution-history"
        for phase in ATTRIBUTION_HISTORY_PHASES:
            if phase.endswith("-create"):
                attribution_root.mkdir()
            completed = subprocess.run(  # noqa: S603 -- fixed interpreter and local script
                [sys.executable, __file__, "--worker", phase, "--root", str(attribution_root)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or f"worker failed: {phase}")
            if phase.endswith("-check"):
                attribution_history = json.loads(completed.stdout)
    return {
        "schema_version": 1,
        "verification": "process_restart_latch_recovery_v1",
        "process_count": len(phases),
        "phases": phases,
        "output_uncertainty_process_count": len(OUTPUT_UNCERTAINTY_PHASES),
        "output_uncertainty_cases": output_uncertainty_cases,
        "invalid_recovery_process_count": len(INVALID_RECOVERY_PHASES),
        "invalid_recovery_cases": invalid_recovery_cases,
        "adversarial_process_count": len(adversarial_cases),
        "adversarial_cases": adversarial_cases,
        "attribution_history_process_count": len(ATTRIBUTION_HISTORY_PHASES),
        "attribution_history": attribution_history,
        "physical_stop": "not_established",
        "operational_authority": "none",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--worker",
        choices=(
            PHASES
            + OUTPUT_UNCERTAINTY_PHASES
            + INVALID_RECOVERY_PHASES
            + ATTRIBUTION_HISTORY_PHASES
            + ADVERSARIAL_CASES
        ),
    )
    parser.add_argument("--root", type=Path)
    arguments = parser.parse_args()
    if arguments.worker is not None:
        if arguments.root is None:
            raise SystemExit("--root is required with --worker")
        if arguments.worker in ADVERSARIAL_CASES:
            report = _run_adversarial_worker(arguments.root, arguments.worker)
        elif arguments.worker in OUTPUT_UNCERTAINTY_PHASES:
            report = _run_output_uncertainty_worker(arguments.root, arguments.worker)
        elif arguments.worker in INVALID_RECOVERY_PHASES:
            report = _run_invalid_recovery_worker(arguments.root, arguments.worker)
        elif arguments.worker in ATTRIBUTION_HISTORY_PHASES:
            report = _run_attribution_history_worker(arguments.root, arguments.worker)
        else:
            report = _run_worker(arguments.root, arguments.worker)
    else:
        if arguments.root is not None:
            raise SystemExit("--root is only valid with --worker")
        report = _run_parent()
    sys.stdout.write(_canonical_json(report))


if __name__ == "__main__":
    main()
