# Support

Oscillink Safety Ops is experimental alpha software. There is no support SLA, operational-response
commitment, approved equipment integration, or production deployment.

## Usage help

Before opening an issue:

1. Read the [README](README.md), [technical overview](docs/technical-overview.md), and
   [assurance status](docs/assurance-status.md).
2. Use Python 3.11 and run `uv sync --locked --dev`.
3. Run `PYTHONPATH= uv run python scripts/verify.py` from a clean checkout.
4. Reduce the question to project-authored synthetic inputs and an exact commit SHA.

Use the bug form for reproducible contract failures, the integration form for bounded public-core
proposals, and the external-reproduction form for independent reruns. Community support is best
effort.

## Sensitive and security reports

Never put credentials, private keys, internal URLs, customer procedures, employee information,
facility layouts, production exports, incident records, private prompts, hidden evaluation content,
or licensed standards text in an issue, discussion, pull request, log, screenshot, or attachment.
Use synthetic or permissively licensed reproductions. Vulnerabilities must follow
[SECURITY.md](SECURITY.md), not a public issue.

## Authority limit

Support cannot provide legal interpretation, regulatory applicability, certification, PL/SIL
assessment, work authorization, safe-operation approval, or assistance connecting the alpha to real
equipment. Those decisions remain with appropriately authorized organizations and qualified people.
