"""Render deterministic viewer-facing repository assets."""

# ruff: noqa: E501 - SVG source lines stay intact for deterministic, inspectable output.

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from textwrap import dedent

ASSET_NAMES = (
    "oscillink-safety-ops-architecture.svg",
    "repository-social-preview.png",
    "safety-evidence-packet-synthetic.svg",
)

HEADLINE = (
    "Oscillink Safety Ops is an independent safety and risk-mitigation supervisor for "
    "AI-controlled industrial equipment, connecting machine intent, observed behavior, and "
    "safety-manager oversight."
)
SOCIAL_PREVIEW_LINES = (
    "INDEPENDENT SAFETY SUPERVISOR",
    "AI CONTROLLED INDUSTRIAL EQUIPMENT",
    "RISK MITIGATION / OVERSIGHT",
)

ARCHITECTURE_SVG = (
    dedent(
        """\
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" role="img" aria-labelledby="title desc">
      <title id="title">Oscillink Safety Ops governed evidence architecture</title>
      <desc id="desc">Exact source intake flows through candidate extraction and external review into a Safety Evidence Packet and offline evaluation. No path reaches physical control.</desc>
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M40 0H0V40" fill="none" stroke="#17233a" stroke-width="1"/>
        </pattern>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
          <path d="M0 0L10 5L0 10Z" fill="#38d9f5"/>
        </marker>
        <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#102138"/>
          <stop offset="1" stop-color="#08111f"/>
        </linearGradient>
      </defs>
      <rect width="1280" height="720" fill="#050a12"/>
      <rect width="1280" height="720" fill="url(#grid)" opacity=".72"/>
      <text x="64" y="70" fill="#f5f8ff" font-family="Inter,Segoe UI,sans-serif" font-size="31" font-weight="700">GOVERNED EVIDENCE, END TO END</text>
      <text x="64" y="105" fill="#8ea2bd" font-family="Inter,Segoe UI,sans-serif" font-size="16">Exact identity and authority boundaries remain visible through every transformation.</text>
      <g fill="none" stroke="#38d9f5" stroke-width="3" marker-end="url(#arrow)">
        <path d="M286 275H354"/>
        <path d="M596 275H664"/>
        <path d="M906 275H974"/>
        <path d="M1085 366V438"/>
      </g>
      <g font-family="Inter,Segoe UI,sans-serif">
        <g transform="translate(64 172)">
          <rect width="222" height="194" rx="14" fill="#07101d"/>
          <rect width="222" height="194" rx="14" fill="url(#panel)" stroke="#38d9f5" stroke-width="2"/>
          <text x="22" y="42" fill="#38d9f5" font-size="14" font-weight="700">01 / EXACT SOURCE INTAKE</text>
          <text x="22" y="78" fill="#f5f8ff" font-size="16">Regulations</text>
          <text x="22" y="107" fill="#f5f8ff" font-size="16">Procedures + manuals</text>
          <text x="22" y="136" fill="#f5f8ff" font-size="16">Plans + episodes</text>
          <text x="22" y="170" fill="#8ea2bd" font-family="JetBrains Mono,monospace" font-size="12">BYTES / REVISION / HASH</text>
        </g>
        <g transform="translate(374 172)">
          <rect width="222" height="194" rx="14" fill="#07101d"/>
          <rect width="222" height="194" rx="14" fill="url(#panel)" stroke="#8b9cff" stroke-width="2"/>
          <text x="22" y="42" fill="#8b9cff" font-size="14" font-weight="700">02 / CANDIDATE LAYER</text>
          <text x="22" y="78" fill="#f5f8ff" font-size="16">Cited extraction</text>
          <text x="22" y="107" fill="#f5f8ff" font-size="16">Asset applicability</text>
          <text x="22" y="136" fill="#f5f8ff" font-size="16">Conflict + stale states</text>
          <text x="22" y="170" fill="#8ea2bd" font-family="JetBrains Mono,monospace" font-size="12">UNTRUSTED / FAIL-CLOSED</text>
        </g>
        <g transform="translate(684 172)">
          <rect width="222" height="194" rx="14" fill="#07101d"/>
          <rect width="222" height="194" rx="14" fill="url(#panel)" stroke="#ffbf47" stroke-width="2"/>
          <text x="22" y="42" fill="#ffbf47" font-size="14" font-weight="700">03 / EXTERNAL REVIEW</text>
          <text x="22" y="78" fill="#f5f8ff" font-size="16">Reviewer identity</text>
          <text x="22" y="107" fill="#f5f8ff" font-size="16">Decision + authority</text>
          <text x="22" y="136" fill="#f5f8ff" font-size="16">Correction lineage</text>
          <text x="22" y="170" fill="#8ea2bd" font-family="JetBrains Mono,monospace" font-size="12">EXACT CANDIDATE BINDING</text>
        </g>
        <g transform="translate(994 172)">
          <rect width="222" height="194" rx="14" fill="#07101d"/>
          <rect width="222" height="194" rx="14" fill="url(#panel)" stroke="#49e2a8" stroke-width="2"/>
          <text x="22" y="42" fill="#49e2a8" font-size="14" font-weight="700">04 / REVIEWABLE ARTIFACT</text>
          <text x="22" y="94" fill="#f5f8ff" font-size="16" font-weight="700">SAFETY EVIDENCE PACKET</text>
          <text x="22" y="142" fill="#8ea2bd" font-size="14">Sources + unknowns</text>
          <text x="22" y="170" fill="#8ea2bd" font-family="JetBrains Mono,monospace" font-size="12">AUTHORITY: NONE</text>
        </g>
        <g transform="translate(784 458)">
          <rect width="432" height="104" rx="14" fill="#07101d"/>
          <rect width="432" height="104" rx="14" fill="url(#panel)" stroke="#38d9f5" stroke-width="2"/>
          <text x="24" y="38" fill="#38d9f5" font-size="14" font-weight="700">OFFLINE PLAN + EPISODE EVALUATION</text>
          <text x="24" y="70" fill="#f5f8ff" font-size="16">Cited findings for authorized human review</text>
          <text x="24" y="91" fill="#8ea2bd" font-family="JetBrains Mono,monospace" font-size="11">OUTPUT: EVIDENCE_FINDINGS_ONLY</text>
        </g>
        <g transform="translate(64 596)">
          <rect width="1152" height="72" rx="12" fill="#1a0d13" stroke="#ff617c" stroke-width="2" stroke-dasharray="8 7"/>
          <text x="28" y="31" fill="#ff617c" font-size="16" font-weight="700">NO PHYSICAL CONTROL PATH</text>
          <text x="28" y="54" fill="#d8a6b0" font-size="13">No permits, compliance conclusions, PLC writes, interlock changes, robot commands, or operational authorization.</text>
        </g>
      </g>
    </svg>
    """
    ).strip()
    + "\n"
)

PACKET_SVG = (
    dedent(
        """\
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" role="img" aria-labelledby="title desc">
      <title id="title">Synthetic Safety Evidence Packet</title>
      <desc id="desc">A synthetic packet for an identified press and maintenance task. It preserves source revisions, unresolved evidence, and fixed no-authority states.</desc>
      <defs>
        <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#17233a" stroke-width="1"/></pattern>
        <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#11223a"/><stop offset="1" stop-color="#08111f"/></linearGradient>
      </defs>
      <rect width="1280" height="720" fill="#050a12"/>
      <rect width="1280" height="720" fill="url(#grid)" opacity=".7"/>
      <g font-family="Inter,Segoe UI,sans-serif">
        <text x="64" y="64" fill="#ffbf47" font-size="13" font-weight="700" letter-spacing="2">SYNTHETIC DEMONSTRATION — NOT FACILITY EVIDENCE</text>
        <text x="64" y="106" fill="#f5f8ff" font-size="32" font-weight="700">SAFETY EVIDENCE PACKET</text>
        <text x="64" y="137" fill="#8ea2bd" font-family="JetBrains Mono,monospace" font-size="13">packet-synthetic-press-7 / revision 1 / schema v1</text>
        <g transform="translate(64 174)">
          <rect width="360" height="210" rx="14" fill="#07101d"/>
          <rect width="360" height="210" rx="14" fill="url(#panel)" stroke="#38d9f5" stroke-width="2"/>
          <text x="24" y="38" fill="#38d9f5" font-size="14" font-weight="700">IDENTIFIED CONTEXT</text>
          <text x="24" y="78" fill="#8ea2bd" font-size="13">ASSET</text><text x="132" y="78" fill="#f5f8ff" font-size="15">SYN-PRESS-7</text>
          <text x="24" y="109" fill="#8ea2bd" font-size="13">SERIAL</text><text x="132" y="109" fill="#f5f8ff" font-size="15">SP7-0042</text>
          <text x="24" y="140" fill="#8ea2bd" font-size="13">TASK</text><text x="132" y="140" fill="#f5f8ff" font-size="15">MAINTENANCE-001</text>
          <text x="24" y="171" fill="#8ea2bd" font-size="13">PHASE</text><text x="132" y="171" fill="#f5f8ff" font-size="15">OFFLINE REVIEW</text>
          <text x="24" y="196" fill="#ffbf47" font-size="12">UNKNOWN: WORKER AUTHORIZATION RECORD</text>
        </g>
        <g transform="translate(460 174)">
          <rect width="756" height="210" rx="14" fill="#07101d"/>
          <rect width="756" height="210" rx="14" fill="url(#panel)" stroke="#8b9cff" stroke-width="2"/>
          <text x="24" y="38" fill="#8b9cff" font-size="14" font-weight="700">EXACT SOURCE SET</text>
          <text x="24" y="78" fill="#f5f8ff" font-size="15">MANUFACTURER MANUAL</text>
          <text x="254" y="78" fill="#8ea2bd" font-family="JetBrains Mono,monospace" font-size="12">REV-2 / SHA256: 4EA54E…E5D</text>
          <text x="24" y="113" fill="#f5f8ff" font-size="15">SITE PROCEDURE</text>
          <text x="254" y="113" fill="#ffbf47" font-family="JetBrains Mono,monospace" font-size="12">REV-1 / SUPERSEDED</text>
          <text x="24" y="148" fill="#f5f8ff" font-size="15">SITE PROCEDURE</text>
          <text x="254" y="148" fill="#8ea2bd" font-family="JetBrains Mono,monospace" font-size="12">REV-2 / SHA256: 22034A…972</text>
          <text x="24" y="186" fill="#8ea2bd" font-size="13">Every finding points back to exact source identity and cited location.</text>
        </g>
        <g transform="translate(64 420)">
          <rect width="730" height="176" rx="14" fill="#07101d"/>
          <rect width="730" height="176" rx="14" fill="url(#panel)" stroke="#ffbf47" stroke-width="2"/>
          <text x="24" y="38" fill="#ffbf47" font-size="14" font-weight="700">UNRESOLVED EVIDENCE REMAINS VISIBLE</text>
          <text x="24" y="76" fill="#f5f8ff" font-size="15">• unreadable responsible-role field</text>
          <text x="24" y="108" fill="#f5f8ff" font-size="15">• source conflict in energy classification</text>
          <text x="24" y="140" fill="#f5f8ff" font-size="15">• stale procedure revision + model mismatch</text>
          <text x="24" y="163" fill="#8ea2bd" font-size="12">No hidden resolution. Exact review is still required.</text>
        </g>
        <g transform="translate(830 420)">
          <rect width="386" height="176" rx="14" fill="#07101d"/>
          <rect width="386" height="176" rx="14" fill="url(#panel)" stroke="#ff617c" stroke-width="2"/>
          <text x="24" y="40" fill="#ff617c" font-size="14" font-weight="700">FIXED AUTHORITY STATES</text>
          <text x="24" y="78" fill="#f5f8ff" font-family="JetBrains Mono,monospace" font-size="14">COMPLIANCE: NO CONCLUSION</text>
          <text x="24" y="112" fill="#f5f8ff" font-family="JetBrains Mono,monospace" font-size="13">APPLICABILITY AUTHORITY: NONE</text>
          <text x="24" y="146" fill="#f5f8ff" font-family="JetBrains Mono,monospace" font-size="14">OPERATIONAL AUTHORITY: NONE</text>
        </g>
        <text x="64" y="652" fill="#8ea2bd" font-size="13">Project-authored fixture. Deterministic engineering evidence only.</text>
      </g>
    </svg>
    """
    ).strip()
    + "\n"
)

FONT: dict[str, tuple[str, ...]] = {
    " ": ("00000",) * 7,
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}

Color = tuple[int, int, int]


class Canvas:
    """Small deterministic RGB canvas used for the repository social preview."""

    def __init__(self, width: int, height: int, background: Color) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(background * (width * height))

    def pixel(self, x: int, y: int, color: Color) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 3
            self.pixels[offset : offset + 3] = bytes(color)

    def rectangle(self, x: int, y: int, width: int, height: int, color: Color) -> None:
        for row in range(y, y + height):
            if not 0 <= row < self.height:
                continue
            start = (row * self.width + max(x, 0)) * 3
            end = (row * self.width + min(x + width, self.width)) * 3
            self.pixels[start:end] = bytes(color) * ((end - start) // 3)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: Color) -> None:
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        step_x = 1 if x1 < x2 else -1
        step_y = 1 if y1 < y2 else -1
        error = dx + dy
        while True:
            self.pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            doubled = 2 * error
            if doubled >= dy:
                error += dy
                x1 += step_x
            if doubled <= dx:
                error += dx
                y1 += step_y

    def text(self, x: int, y: int, value: str, scale: int, color: Color) -> None:
        cursor = x
        for character in value.upper():
            glyph = FONT[character]
            for glyph_y, row in enumerate(glyph):
                for glyph_x, enabled in enumerate(row):
                    if enabled == "1":
                        self.rectangle(
                            cursor + glyph_x * scale,
                            y + glyph_y * scale,
                            scale,
                            scale,
                            color,
                        )
            cursor += 6 * scale


def png_bytes(canvas: Canvas) -> bytes:
    """Encode a canvas as a deterministic RGB PNG."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    stride = canvas.width * 3
    scanlines = b"".join(
        b"\x00" + bytes(canvas.pixels[offset : offset + stride])
        for offset in range(0, len(canvas.pixels), stride)
    )
    header = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(scanlines, level=9))
        + chunk(b"IEND", b"")
    )


def social_preview() -> bytes:
    """Render the 1280x640 GitHub social preview."""
    canvas = Canvas(1280, 640, (5, 10, 18))
    grid = (18, 33, 53)
    for x in range(0, 1280, 40):
        canvas.line(x, 0, x, 639, grid)
    for y in range(0, 640, 40):
        canvas.line(0, y, 1279, y, grid)
    canvas.rectangle(56, 58, 8, 524, (56, 217, 245))
    canvas.text(100, 94, "OSCILLINK", 9, (245, 248, 255))
    canvas.text(100, 202, SOCIAL_PREVIEW_LINES[0], 5, (56, 217, 245))
    canvas.text(100, 258, SOCIAL_PREVIEW_LINES[1], 4, (56, 217, 245))
    canvas.rectangle(100, 350, 936, 2, (54, 78, 106))
    canvas.text(100, 396, SOCIAL_PREVIEW_LINES[2], 3, (255, 191, 71))
    canvas.text(100, 520, "SAFETY OPS", 4, (142, 162, 189))
    return png_bytes(canvas)


def render_assets(output_dir: Path) -> tuple[Path, ...]:
    """Render the complete marketing-asset set into ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    architecture = output_dir / ASSET_NAMES[0]
    social = output_dir / ASSET_NAMES[1]
    packet = output_dir / ASSET_NAMES[2]
    architecture.write_text(ARCHITECTURE_SVG, encoding="utf-8", newline="\n")
    social.write_bytes(social_preview())
    packet.write_text(PACKET_SVG, encoding="utf-8", newline="\n")
    return architecture, social, packet


def main() -> None:
    rendered = render_assets(Path("docs/assets"))
    for path in rendered:
        print(path.as_posix())


if __name__ == "__main__":
    main()
