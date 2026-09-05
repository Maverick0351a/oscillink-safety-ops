# Oscillink brand assets

This directory contains the owner-supplied Oscillink logo and deterministic responsive derivatives for the Oscillink Safety Ops interface and documentation.

## Asset authority

- `source/oscillink-logo-original.png` is the exact owner-supplied raster artwork. Its immutable byte identity and dimensions are recorded in `manifest.json`.
- `dist/oscillink-lockup-dark.svg` is the primary dark-field horizontal lockup.
- `dist/oscillink-lockup-light.svg` is the light-field lockup.
- `dist/oscillink-lockup-mono.svg` is the one-color reproduction variant.
- `dist/oscillink-mark.svg` is a simplified compact mark for small UI surfaces.
- `dist/tokens.css` defines identity colors separately from safety-state colors.

The responsive SVGs are simplified project-authored derivatives, not replacements for the source artwork. Regenerate them with:

```bash
uv run python scripts/render_brand_assets.py
```

## Usage rules

- Preserve clear space equal to at least one terminal-node diameter around a mark.
- Use the full raster badge only where the internal circuit detail remains legible.
- Use the simplified mark below 96 CSS pixels.
- Do not stretch, recolor individual traces, add glow to warning states, or place status badges over the mark.
- Brand teal communicates Oscillink identity, linkage, and active inspection. It does **not** mean safe, approved, acknowledged, certified, or stopped.
- Warning, critical, and positive states require distinct colors, visible text, and non-color cues.
- The Oscillink marks are governed by [`TRADEMARKS.md`](../TRADEMARKS.md). They are not certification seals and confer no operational authority.

## Core palette

| Token | Value | Use |
|---|---:|---|
| Oscillink navy | `#151a3d` | Primary identity field |
| Oscillink teal | `#35b6be` | Links, signal accents, active inspection |
| Oscillink white | `#f7f7f4` | High-contrast wordmark and structure |
| Safety warning | `#ffbd5b` | Uncertainty and warnings, with text |
| Safety critical | `#ff6b73` | Latches and critical findings, with text |
| Safety positive | `#77e1a0` | Verified software-state indicators only |
