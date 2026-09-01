"""Download the cataloged OSHA/eCFR snapshot into a local content-addressed cache."""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from oscillink_safety_ops.regulations import (
    RegulationArtifact,
    validate_osha_catalog,
    write_content_addressed_regulation,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("knowledge/osha/catalog.json"),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("knowledge/osha/cache"),
    )
    parser.add_argument("--jobs", type=int, default=1)
    return parser


def _download(source: dict[str, Any], root: Path) -> dict[str, object]:
    endpoint = source["content_endpoint"]
    if not isinstance(endpoint, str):
        raise ValueError("content_endpoint must be a string")
    request = Request(  # noqa: S310 -- allowlist-validated official eCFR URL
        endpoint, headers={"User-Agent": "oscillink-safety-ops/0.1"}
    )
    for attempt in range(6):
        try:
            with urlopen(  # noqa: S310 -- catalog is allowlist-validated
                request, timeout=120
            ) as response:
                content = response.read()
            break
        except HTTPError as error:
            if error.code != 429 or attempt == 5:
                raise ValueError(
                    f"eCFR download failed for part {source['part']}: {error.code}"
                ) from error
            time.sleep(min(2**attempt, 30))
    if not content.lstrip().startswith(b"<?xml") or b"<DIV" not in content[:1024]:
        raise ValueError(f"unexpected eCFR response for part {source['part']}")
    artifact: RegulationArtifact = write_content_addressed_regulation(root, content)
    return {
        "part": source["part"],
        "source_url": endpoint,
        "sha256": artifact.sha256,
        "byte_count": artifact.byte_count,
        "artifact_ref": artifact.relative_path,
        "review_state": "unreviewed_source",
    }


def main() -> None:
    args = _parser().parse_args()
    catalog: dict[str, Any] = json.loads(args.catalog.read_text(encoding="utf-8"))
    validate_osha_catalog(catalog)
    active = [
        source
        for source in catalog["sources"]
        if not source["reserved"] and source["content_status"] == "available"
    ]
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        snapshots = list(executor.map(lambda source: _download(source, args.root), active))
    manifest = {
        "schema_version": 1,
        "catalog_id": catalog["catalog_id"],
        "catalog_index_sha256": catalog["index_sha256"],
        "ecfr_as_of": catalog["ecfr_as_of"],
        "authority_notice": catalog["authority_notice"],
        "source_count": len(snapshots),
        "sources": snapshots,
    }
    args.root.mkdir(parents=True, exist_ok=True)
    (args.root / "snapshot-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"synced {len(snapshots)} active OSHA regulation parts to {args.root}")


if __name__ == "__main__":
    main()
