# Support

Oscillink Safety Ops is experimental private product software. There is no production service,
support SLA, operational-response commitment, or approved equipment integration.

## Questions and usage help

Before opening an issue:

1. Read the [README](README.md), [technical overview](docs/technical-overview.md), and
   [synthetic demonstration](docs/synthetic-demo.md).
2. Run `PYTHONPATH= uv run python scripts/verify.py` from a clean checkout.
3. Confirm Python 3.11 and the locked `uv` environment are in use.
4. Reduce the question to project-authored synthetic data.

Use a repository issue for reproducible questions about the public contracts, schemas, fixtures, or
offline CLI. Community support is best effort.

## Sensitive information

Do not put any of the following in an issue, discussion, pull request, log, screenshot, or attached
file:

- credentials, tokens, private keys, or internal URLs;
- customer procedures, permits, incident records, or employee information;
- facility layouts, equipment secrets, or production-system exports;
- licensed standards text or unlawfully reproduced manuals;
- private prompts, hidden evaluation tasks, expected answers, or protected labels; or
- information that identifies a vulnerability before coordinated disclosure.

Use synthetic or permissively licensed reproductions instead.

## Security reports

Do not report vulnerabilities in a public issue. Follow [SECURITY.md](SECURITY.md). A public launch
is blocked until a tested private vulnerability-reporting route exists.

## Product and authority limits

Support cannot provide legal interpretation, regulatory-applicability decisions, compliance
certification, work authorization, safe-operation approval, or equipment-control assistance. Those
decisions remain with appropriately authorized people and organizations.
