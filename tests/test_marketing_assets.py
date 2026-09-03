from __future__ import annotations

import importlib
import struct
from pathlib import Path

APPROVED_HEADLINE = (
    "Oscillink Safety Ops is an independent safety and risk-mitigation supervisor for "
    "AI-controlled industrial equipment, connecting machine intent, observed behavior, and "
    "safety-manager oversight."
)


def test_render_assets_creates_expected_files(tmp_path: Path) -> None:
    render_assets = importlib.import_module("scripts.render_marketing_assets").render_assets

    rendered = render_assets(tmp_path)

    assert {path.name for path in rendered} == {
        "oscillink-safety-ops-architecture.svg",
        "repository-social-preview.png",
        "safety-evidence-packet-synthetic.svg",
    }
    assert all(path.is_file() for path in rendered)


def test_svg_assets_preserve_product_and_authority_labels(tmp_path: Path) -> None:
    render_assets = importlib.import_module("scripts.render_marketing_assets").render_assets

    render_assets(tmp_path)

    architecture = (tmp_path / "oscillink-safety-ops-architecture.svg").read_text(encoding="utf-8")
    packet = (tmp_path / "safety-evidence-packet-synthetic.svg").read_text(encoding="utf-8")
    assert 'viewBox="0 0 1280 720"' in architecture
    assert "EXACT SOURCE INTAKE" in architecture
    assert "EXTERNAL REVIEW" in architecture
    assert "SAFETY EVIDENCE PACKET" in architecture
    assert "NO PHYSICAL CONTROL PATH" in architecture
    assert 'viewBox="0 0 1280 720"' in packet
    assert "SYNTHETIC DEMONSTRATION" in packet
    assert "COMPLIANCE: NO CONCLUSION" in packet
    assert "OPERATIONAL AUTHORITY: NONE" in packet


def test_social_preview_is_1280_by_640_png(tmp_path: Path) -> None:
    render_assets = importlib.import_module("scripts.render_marketing_assets").render_assets

    render_assets(tmp_path)

    raw = (tmp_path / "repository-social-preview.png").read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", raw[16:24])
    assert (width, height) == (1280, 640)


def test_rendered_assets_are_deterministic(tmp_path: Path) -> None:
    render_assets = importlib.import_module("scripts.render_marketing_assets").render_assets
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_paths = render_assets(first)
    second_paths = render_assets(second)

    assert [path.read_bytes() for path in first_paths] == [
        path.read_bytes() for path in second_paths
    ]


def test_social_preview_copy_uses_approved_product_positioning() -> None:
    module = importlib.import_module("scripts.render_marketing_assets")

    assert hasattr(module, "HEADLINE")
    assert hasattr(module, "SOCIAL_PREVIEW_LINES")
    assert module.HEADLINE == APPROVED_HEADLINE
    assert "INDEPENDENT SAFETY SUPERVISOR" in module.SOCIAL_PREVIEW_LINES
    assert "AI CONTROLLED INDUSTRIAL EQUIPMENT" in module.SOCIAL_PREVIEW_LINES
