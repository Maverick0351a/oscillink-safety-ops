"""Refresh the committed OSHA regulation source catalog from the official OSHA index."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import Request, urlopen

from oscillink_safety_ops.regulations import OSHA_INDEX_URL, render_osha_catalog


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ecfr-as-of", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("knowledge/osha/catalog.json"),
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    request = Request(  # noqa: S310 -- fixed official HTTPS URL
        OSHA_INDEX_URL, headers={"User-Agent": "oscillink-safety-ops/0.1"}
    )
    with urlopen(request, timeout=60) as response:  # noqa: S310 -- fixed official HTTPS URL
        index_bytes = response.read()
    rendered = render_osha_catalog(index_bytes, ecfr_as_of=args.ecfr_as_of)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
