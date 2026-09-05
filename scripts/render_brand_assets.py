"""Render deterministic responsive Oscillink brand assets."""

# ruff: noqa: E501 -- SVG source lines remain intact for deterministic assets.

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent

NAVY = "#151a3d"
TEAL = "#35b6be"
WHITE = "#f7f7f4"
INK = "#101630"

MARK_PATHS = """
  <path d="M80 10 134 42v30M134 88v30L80 150 26 118V88M26 72V42L80 10" fill="none" stroke="{frame}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
  <g fill="none" stroke="{frame}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
    <path d="M80 24v26L64 64"/><path d="M80 136v-26L64 96"/>
    <path d="M44 48h18l10 10"/><path d="M44 112h18l10-10"/>
    <path d="M116 48H98L88 58"/><path d="M116 112H98l-10-10"/>
  </g>
  <g fill="none" stroke="{accent}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
    <path d="M48 80h22l10-10 10 10h22"/>
    <path d="M48 88h22l10 10 10-10h22"/>
  </g>
  <g fill="{accent}"><circle cx="44" cy="48" r="4"/><circle cx="44" cy="112" r="4"/><circle cx="116" cy="48" r="4"/><circle cx="116" cy="112" r="4"/></g>
""".strip()

TOKENS = """:root {
  --oscillink-navy: #151a3d;
  --oscillink-teal: #35b6be;
  --oscillink-white: #f7f7f4;
  --oscillink-ink: #101630;
  --safety-warning: #ffbd5b;
  --safety-critical: #ff6b73;
  --safety-positive: #77e1a0;
}

/* Brand teal does not communicate safety state. Pair safety colors with text and shape. */
"""


def _svg(*, name: str, background: str | None, frame: str, accent: str, text: str) -> str:
    backdrop = f'<rect width="560" height="160" rx="20" fill="{background}"/>' if background else ""
    return (
        dedent(
            f"""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 160" role="img" aria-labelledby="title desc">
              <title id="title">Oscillink {name} logo</title>
              <desc id="desc">Oscillink circuit-link emblem with the Oscillink Safety Ops wordmark.</desc>
              {backdrop}
              <g transform="translate(10)">
                {MARK_PATHS.format(frame=frame, accent=accent)}
              </g>
              <g fill="{text}" font-family="Segoe UI Variable,Segoe UI,Arial,sans-serif">
                <text x="172" y="83" font-size="47" font-weight="700" letter-spacing="2">OSCILLINK</text>
                <text x="175" y="111" fill="{accent}" font-size="15" font-weight="700" letter-spacing="5">SAFETY OPS</text>
              </g>
            </svg>
            """
        ).strip()
        + "\n"
    )


def _mark() -> str:
    return (
        dedent(
            f"""\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" role="img" aria-labelledby="title desc">
              <title id="title">Oscillink responsive mark</title>
              <desc id="desc">Simplified hexagonal circuit-link emblem for compact Oscillink brand use.</desc>
              {MARK_PATHS.format(frame=NAVY, accent=TEAL)}
            </svg>
            """
        ).strip()
        + "\n"
    )


def render_brand_assets(destination: Path) -> tuple[Path, ...]:
    """Write deterministic responsive assets and return sorted output paths."""

    destination.mkdir(parents=True, exist_ok=True)
    assets = {
        "oscillink-lockup-dark.svg": _svg(
            name="dark", background=NAVY, frame=WHITE, accent=TEAL, text=WHITE
        ),
        "oscillink-lockup-light.svg": _svg(
            name="light", background=WHITE, frame=NAVY, accent=TEAL, text=INK
        ),
        "oscillink-lockup-mono.svg": _svg(
            name="monochrome", background=None, frame="#000000", accent="#000000", text="#000000"
        ),
        "oscillink-mark.svg": _mark(),
        "tokens.css": TOKENS,
    }
    paths: list[Path] = []
    for name in sorted(assets):
        path = destination / name
        path.write_text(assets[name], encoding="utf-8", newline="\n")
        paths.append(path)
    return tuple(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path("brand/dist"))
    args = parser.parse_args()
    render_brand_assets(args.destination)


if __name__ == "__main__":
    main()
