# OSHA regulation source catalog

This starting knowledge base catalogs every part currently listed by OSHA on its official
[Regulations (Standards — 29 CFR)](https://www.osha.gov/laws-regs/regulations/standardnumber)
index, including reserved parts and entries outside 29 CFR Chapter XVII that OSHA includes on that
index.

`catalog.json` is a deterministic point-in-time source catalog generated from the official OSHA
index. It contains 67 entries and binds the source index bytes by SHA-256. Each non-reserved entry
has a dated eCFR Versioner API endpoint for retrieving XML as it existed on `ecfr_as_of`.

The catalog is **source discovery**, not approved safety memory:

- no catalog entry is automatically applicable to an asset, site, jurisdiction, task, or person;
- no regulation text is converted into an approved constraint without authorized external review;
- conflicts, amendments, corrections, state-plan differences, incorporation by reference, and legal
  interpretation remain unresolved;
- the eCFR is continuously updated and is not the official legal edition of the CFR; and
- the annual official CFR publication is linked through GovInfo for qualified review.

## Refresh the catalog

```bash
PYTHONPATH= uv run python scripts/export_osha_catalog.py --ecfr-as-of YYYY-MM-DD
```

Use the `up_to_date_as_of` value for Title 29 from the official eCFR titles API. Review the resulting
diff and source count rather than silently accepting additions or removals.

## Populate the local content-addressed cache

```bash
PYTHONPATH= uv run python scripts/sync_osha_knowledge.py --jobs 1
```

This downloads every available, non-reserved catalog entry only from its allowlist-validated eCFR endpoint,
stores immutable XML bytes by SHA-256 under `knowledge/osha/cache/`, and writes a snapshot manifest.
The cache is intentionally gitignored because it is reproducible source material, not reviewed
canonical memory. The committed catalog remains the portable starting knowledge-base index.
