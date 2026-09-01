## Scope

Describe the narrow evidence contract or documentation problem this pull request addresses.

## Evidence and authority boundary

- [ ] The change preserves source class, identity, revision, exact hash, applicability metadata, and correction or supersession lineage where relevant.
- [ ] Extraction and interpretation remain candidates until externally authorized review.
- [ ] Unknown, stale, missing, conflicting, ambiguous, unreadable, and unsupported evidence remains explicit.
- [ ] The change adds no equipment command, permit, certification, compliance-conclusion, or operational-authorization surface.
- [ ] The pull request contains no credentials, customer or employee records, facility details, incident evidence, private prompts, hidden labels, or licensed standards text.

## Test evidence

Describe the RED failure that established the requested behavior, then the GREEN result.

```text
failing test:
passing test:
```

- [ ] `uv run ruff format .`
- [ ] `uv run ruff check .`
- [ ] `uv run mypy`
- [ ] `PYTHONPATH= uv run python scripts/verify.py`
- [ ] `git diff --check`

## Schemas and fixtures

- [ ] Domain-contract changes include regenerated JSON Schemas.
- [ ] New fixtures are deterministic, project-authored or permissively licensed, and hash-pinned.
- [ ] Expected answers and protected evaluation labels remain outside agent-readable fixture inputs.
- [ ] Documentation and changelog entries match the implemented boundary.

## Review limitations

List any platform, hosted-CI, legal, practitioner, rights, privacy, or operational review that has not occurred.
