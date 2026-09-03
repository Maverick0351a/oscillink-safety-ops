# Transitive dependency license review — 2026-09-03

## Decision

The exact `uv.lock` reviewed has SHA-256
`e79f276ce355d6ece64c5170077ccc67eddee2b5773939132a82fe54f7c73a2b`. The review covers
23 locked third-party packages after excluding the local editable project.

No license incompatibility identified for distribution of the Apache-2.0 project based on the package
metadata and license files reviewed. This is a maintainer engineering review, not legal advice.

## Method and scope

- Exported runtime and development groups with `uv export --locked --all-groups --no-hashes
  --no-emit-project --format requirements-txt`.
- Queried each exact name/version through the official PyPI JSON endpoint on 2026-09-03.
- Preferred SPDX `license_expression`; otherwise used PyPI license classifiers or the legacy license
  field.
- PyPI supplied no license metadata for `mypy-extensions 1.1.0`; its sole PyPI wheel was downloaded,
  checked against PyPI SHA-256
  `1be4cccdb0f2482337c4743e60421de3a356cd97508abadd57d47403e94f5505`, and its bundled
  `mypy_extensions-1.1.0.dist-info/licenses/LICENSE` was identified as MIT.
- Scope covers the exact lockfile, including development dependencies. A lockfile change invalidates
  this review until it is repeated.

## Inventory

| Package | Version | License evidence |
|---|---:|---|
| annotated-types | 0.8.0 | MIT |
| cffi | 2.1.1 | MIT-0 |
| colorama | 0.4.6 | BSD classifier |
| cryptography | 50.0.1 | Apache-2.0 OR BSD-3-Clause |
| defusedxml | 0.7.1 | PSFL / Python Software Foundation License classifier |
| hypothesis | 6.167.1 | MPL-2.0 |
| iniconfig | 2.3.0 | MIT |
| librt | 0.15.0 | MIT |
| mypy | 1.20.2 | MIT |
| mypy-extensions | 1.1.0 | MIT, verified from checksum-bound PyPI wheel license file |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pathspec | 1.1.1 | MPL-2.0 classifier |
| pluggy | 1.6.0 | MIT |
| pycparser | 3.0 | BSD-3-Clause |
| pydantic | 2.13.5 | MIT |
| pydantic-core | 2.46.5 | MIT |
| pygments | 2.21.0 | BSD-2-Clause |
| pytest | 9.1.1 | MIT |
| ruff | 0.16.5 | MIT |
| sortedcontainers | 2.4.0 | Apache-2.0 |
| types-defusedxml | 0.7.0.20260504 | Apache-2.0 |
| typing-extensions | 4.16.0 | PSF-2.0 |
| typing-inspection | 0.4.4 | MIT |

## Limitations

Metadata can be incomplete or corrected after review. This review does not cover optional packages not
resolved by the lockfile, external tools downloaded by workflows, operating-system components, or
future dependency versions. Release artifacts retain their own SBOM and provenance evidence.
