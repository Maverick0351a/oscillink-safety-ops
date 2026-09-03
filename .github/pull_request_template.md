## Scope

Describe the narrow safety-supervision, evidence, or release-contract change.

## Boundary and data

- [ ] The change adds no real equipment, controller, PLC, robot, actuator, remote-reset, or reverse command path.
- [ ] Runtime outputs remain local simulated one-way request records.
- [ ] Production AI cannot change configuration, suppress evidence, acknowledge its own request, or reset a latch.
- [ ] Missing, stale, contradictory, invalid, or unverifiable inputs remain explicit and fail closed.
- [ ] The pull request contains no credential, customer or employee data, facility detail, production export, private prompt, hidden label, or licensed standards text.
- [ ] New fixtures are synthetic or permissively licensed and hash-pinned.

## RED → GREEN evidence

```text
RED command and expected failure:
GREEN command and result:
```

## Verification

- [ ] `uv sync --locked --dev`
- [ ] `uv run ruff format --check .`
- [ ] `uv run ruff check .`
- [ ] `uv run mypy`
- [ ] `PYTHONPATH= uv run python scripts/verify.py`
- [ ] `PYTHONPATH= uv run python -m pytest -q`
- [ ] `PYTHONPATH= uv run pytest -q`
- [ ] `git diff --check`

## Claims and release impact

- [ ] Documentation distinguishes implemented closed-file simulation/replay, synthetic benchmarks, TLA+ abstraction, and CI from field evidence.
- [ ] No certification, PL/SIL achievement, safe-operation, field-validation, or production-readiness claim was added.
- [ ] Schema, generated evidence, changelog, SBOM, and release-manifest impacts are addressed.

## Residual limitations

List hosted-CI, platform, legal, practitioner, rights, privacy, integration, or operational review not performed.
