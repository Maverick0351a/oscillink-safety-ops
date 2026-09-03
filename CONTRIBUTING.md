# Contributing

Oscillink Safety Ops uses an open-core model. The project-authored public core in this repository is
licensed under Apache-2.0. Commercial connectors, configurations, deployment, fleet, and
certification-support layers are separate offerings and are not represented as open source by this
repository. The Oscillink marks remain governed by [TRADEMARKS.md](TRADEMARKS.md).

## Before contributing

Read [AGENTS.md](AGENTS.md), the [product boundary](docs/product-boundary.md), the
[assurance status](docs/assurance-status.md), and the [Code of Conduct](CODE_OF_CONDUCT.md).
Contributions must preserve these boundaries:

- closed-file simulation/replay and local simulated one-way request records only;
- no machine, controller, PLC, robot, actuator, live-network, remote-reset, or reverse command path;
- production AI has no configuration, acknowledgment, suppression, or recovery authority;
- no certification, PL/SIL achievement, safe-operation, work-authorization, or field-validation claim;
- synthetic or permissively licensed fixtures with exact hashes; and
- no credentials, customer or employee data, facility details, private prompts, hidden labels, or
  licensed standards text.

## Development method

Use a narrow vertical RED → GREEN cycle:

1. add one behavior test and run it to capture the expected failure;
2. implement only that behavior;
3. rerun the focused test, then the complete gate;
4. update schemas, generated artifacts, claims, and changelog where affected; and
5. record remaining platform or review limitations.

```bash
uv sync --locked --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy
PYTHONPATH= uv run python scripts/verify.py
PYTHONPATH= uv run python -m pytest -q
PYTHONPATH= uv run pytest -q
git diff --check
```

Use the issue forms and pull-request template. Usage questions follow [SUPPORT.md](SUPPORT.md).
Vulnerabilities must follow [SECURITY.md](SECURITY.md), not a public issue. Contributors remain
responsible for generated content, source rights, tests, and accurate claims.
