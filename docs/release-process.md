# Release process

There is no published Oscillink Safety Ops release. This is a fail-closed candidate procedure; it
does not authorize a commit, push, tag, release, visibility change, deployment, or announcement.

## Identity and implemented boundary

The package identity `0.1.0a1` maps to the intended human tag `v0.1.0-alpha.1`. That identity must
agree across runtime metadata, wheel, source distribution, `CITATION.cff`, `CHANGELOG.md`, release
notes, provenance metadata, and release-verification manifest.

The current runtime is implemented only as deterministic closed-file simulation/replay with local
simulated one-way protective-stop and inhibit request records. It has no machine, controller, PLC,
robot, actuator, live-network, remote-reset, or reverse command path. Synthetic benchmark, TLA+,
property/fuzz tests, and CI are software evidence, not field validation or certification.

## Candidate sequence

### 1. Freeze scope and claims

Confirm synthetic/permissively licensed fixtures, metadata-only licensed standards, open-core and
trademark boundaries, current-vs-planned claims, and absence of credentials, customer data, private
prompts, protected labels, and live control paths.

### 2. Audit reachable history

Generate the redacted baseline report from the exact baseline:

```bash
uv run python scripts/audit_history.py \
  --baseline 2943db23ceb075e8955867903069cd5e043fee45 \
  --output docs/audits/history-baseline-2943db2.json
```

Verify Gitleaks 8.30.1's archive SHA-256
`d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e` before running it over
all reachable history. The tracked report intentionally stops at a defined baseline so it never
claims to contain its own commit. After the exact candidate commit exists, create external evidence
for that exact candidate; do not edit a self-referential containing-commit claim into the tracked
report.

### 3. Audit dependencies and licenses

```bash
uv export --locked --no-dev --no-emit-project --no-hashes \
  --output-file audit-requirements.txt
uvx --from pip-audit==2.10.1 pip-audit --strict \
  --requirement audit-requirements.txt
```

A nonzero advisory result blocks promotion. Record only tool version, command, counts, and resolution;
do not paste advisory prose into tracked evidence. Generate the CycloneDX inventory from `uv.lock`.
The alpha's transitive license inventory is currently incomplete and blocks publication until reviewed.

### 4. Run local gates

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

### 5. Build and verify artifacts

Build outside tracked output paths. Generate the CycloneDX SBOM, unsigned provenance metadata,
frozen benchmark metrics, and formal result. Create the release manifest with `--require-complete`,
copy only the six declared artifacts plus two control files into a fresh directory, remove access to
the source build directory, and verify with explicit expected version and commit.

The verifier rejects path separators, duplicate basenames, missing or extra files, symlinks and other
nonregular files, malformed or noncanonical JSON, wrong package/candidate identity, changed size or
bytes, absent required artifact roles, and `SHA256SUMS.txt` drift. Package inspection rejects unsafe
or excluded members including Git internals, `.hermes`, local/private data, runtime output, caches,
and credential-like files.

### 6. Verify the exact candidate

Only after a candidate commit exists, rerun all Windows gates, transfer the exact SHA to the
independent Linux Buildbox, and compare source-distribution bytes and wheel payloads. Then, only with
explicit owner authorization, push while private and require hosted verification/security/nightly or
equivalent release gates on that SHA.

### 7. Promote separately

Tagging and publishing are Batch 8 actions. The release workflow only uploads short-lived verified CI
artifacts; it has read-only repository permissions and no deploy or publication step.

## Rollback and correction

Before publication, document release withdrawal, corrected checksums, visibility rollback, hosted
preview removal, and correction lineage. Do not rewrite public history except for a confirmed
sensitive-data incident with documented consequences.
