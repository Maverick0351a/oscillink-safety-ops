"""Governed Oscillink brand assets and responsive variants."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "brand"
SOURCE_SHA256 = "350d999865a14123bbf4501f24fbde1d3f5ad0367b1e8b7b39094c049aa7b66f"


class SvgParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


def test_source_logo_is_exact_hash_bound_and_manifested() -> None:
    source = BRAND / "source" / "oscillink-logo-original.png"
    manifest = json.loads((BRAND / "manifest.json").read_text(encoding="utf-8"))

    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256
    assert manifest["source"]["sha256"] == "sha256:" + SOURCE_SHA256
    assert manifest["source"]["width"] == 1024
    assert manifest["source"]["height"] == 1024
    assert manifest["source"]["byte_count"] == len(source.read_bytes())
    assert manifest["authority"]["trademark_owner"] == "Oscillink"
    assert manifest["authority"]["certification_mark"] is False
    assert {item["path"]: item["sha256"] for item in manifest["generated_assets"]} == {
        path.relative_to(BRAND).as_posix(): (
            "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for path in sorted((BRAND / "dist").iterdir())
        if path.is_file()
    }


def test_brand_renderer_is_byte_repeatable_and_matches_committed_variants(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    command = [sys.executable, str(ROOT / "scripts" / "render_brand_assets.py")]
    for destination in (first, second):
        result = subprocess.run(  # noqa: S603 -- fixed local interpreter and repository script
            [*command, "--destination", str(destination)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    expected_names = {
        "oscillink-lockup-dark.svg",
        "oscillink-lockup-light.svg",
        "oscillink-lockup-mono.svg",
        "oscillink-mark.svg",
        "tokens.css",
    }
    assert {path.name for path in first.iterdir()} == expected_names
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in (BRAND / "dist").iterdir() if path.is_file()
    }


def test_svg_variants_are_accessible_local_and_not_safety_certification_marks() -> None:
    for path in sorted((BRAND / "dist").glob("*.svg")):
        text = path.read_text(encoding="utf-8")
        parser = SvgParser()
        parser.feed(text)
        tags = [tag for tag, _attrs in parser.tags]
        assert tags[0] == "svg"
        assert "title" in tags
        assert "desc" in tags
        for _tag, attrs in parser.tags:
            for attribute in ("href", "src"):
                value = attrs.get(attribute)
                if value is not None:
                    assert not value.startswith(("http:", "https:", "//", "data:"))
        assert "certified" not in text.lower()
        assert "approved" not in text.lower()


def test_brand_tokens_keep_identity_and_safety_semantics_separate() -> None:
    css = (BRAND / "dist" / "tokens.css").read_text(encoding="utf-8")

    assert "--oscillink-navy: #151a3d" in css
    assert "--oscillink-teal: #35b6be" in css
    assert "--oscillink-white: #f7f7f4" in css
    assert "--safety-warning: #ffbd5b" in css
    assert "--safety-critical: #ff6b73" in css
    assert "Brand teal does not communicate safety state" in css
