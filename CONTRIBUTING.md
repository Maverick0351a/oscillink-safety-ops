# Contributing

This repository is private during product maturation. Contributions must preserve the evidence and
no-control boundaries in `AGENTS.md`, the [product boundary](docs/product-boundary.md), and the
[Code of Conduct](CODE_OF_CONDUCT.md).

Unless explicitly designated otherwise, contributions intentionally submitted for inclusion are
accepted under the repository's Apache License 2.0 terms.

Before proposing runtime behavior:

1. Link the user or authority problem to direct evidence.
2. State source rights, applicability, and privacy constraints.
3. Write a failing contract/behavior test first.
4. Keep OCR/model/provider implementations behind replaceable adapters.
5. Preserve candidate-only extraction and external review.
6. Include deterministic failure, ambiguity, stale-revision, and rollback behavior.
7. Run the complete verification gate.

The required local gate is:

```bash
uv sync --locked --dev
uv run ruff format .
uv run ruff check .
uv run mypy
PYTHONPATH= uv run python scripts/verify.py
git diff --check
```

Never contribute real secrets, employee/customer data, private SOPs, facility layouts, incident
records, permits, runtime databases, hidden labels, or licensed standards content.

A contribution must not add or imply physical control, permit authority, compliance certification,
or safety-rated behavior.

Use the repository issue forms and pull request template. Report vulnerabilities privately under
[SECURITY.md](SECURITY.md), and follow [SUPPORT.md](SUPPORT.md) for usage questions. External
contributors must identify any generated content and remain responsible for its accuracy, rights,
security, and tests.
