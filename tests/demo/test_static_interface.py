"""Semantic, accessible, read-only static interface contract."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "demo"


class InterfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def _interface() -> tuple[str, str, str, InterfaceParser]:
    html = (DEMO / "index.html").read_text(encoding="utf-8")
    css = (DEMO / "assets" / "styles.css").read_text(encoding="utf-8")
    script = (DEMO / "assets" / "app.js").read_text(encoding="utf-8")
    parser = InterfaceParser()
    parser.feed(html)
    return html, css, script, parser


def test_monitor_primary_inspect_secondary_landmarks_and_required_copy() -> None:
    html, _, _, parser = _interface()
    tags = [tag for tag, _ in parser.tags]
    ids = {attrs.get("id") for _, attrs in parser.tags}
    visible_text = " ".join(parser.text)

    assert tags.count("header") >= 1
    assert (
        sum(attrs.get("class") == "site-header" for tag, attrs in parser.tags if tag == "header")
        == 1
    )
    assert tags.count("main") == 1
    assert "section" in tags
    assert "aside" in tags
    assert tags.count("footer") == 1
    assert {"monitor", "inspect", "scenario-select", "physical-stop"} <= ids
    assert html.index('id="monitor"') < html.index('id="inspect"')
    assert "SYNTHETIC EVIDENCE — SOFTWARE BEHAVIOR ONLY" in visible_text
    assert "No physical stop established" in visible_text
    for copy in (
        "Production intent",
        "Independent occupancy",
        "Independent motion",
        "Independent source health",
        "Deterministic state",
        "Deterministic action",
        "First-out reason",
        "Contributing reasons",
        "Request",
        "Acknowledgment",
        "Latch / recovery",
        "Configuration SHA-256",
        "Input SHA-256",
        "Report SHA-256",
        "Runtime SHA-256",
    ):
        assert copy in visible_text


def test_selector_is_labeled_and_only_supports_scenario_inspection() -> None:
    _, _, script, parser = _interface()
    selectors = [attrs for tag, attrs in parser.tags if tag == "select"]
    labels = [attrs for tag, attrs in parser.tags if tag == "label"]

    assert selectors == [
        {
            "id": "scenario-select",
            "aria-describedby": "selector-help",
        }
    ]
    assert any(label.get("for") == "scenario-select" for label in labels)
    assert 'addEventListener("change"' in script
    assert 'addEventListener("click"' not in script
    forbidden_tags = {"button", "form", "input", "textarea"}
    assert not any(tag in forbidden_tags for tag, _ in parser.tags)
    forbidden_copy = (
        "Reset latch",
        "Rearm system",
        "Acknowledge alarm",
        "Command machine",
        "Stop machine",
    )
    visible_text = " ".join(parser.text)
    assert not any(copy in visible_text for copy in forbidden_copy)


def test_static_demo_has_no_external_or_dynamic_execution_surface() -> None:
    html, _, script, parser = _interface()
    for _tag, attrs in parser.tags:
        for attribute in ("src", "href", "action"):
            value = attrs.get(attribute)
            if value is not None:
                assert not value.startswith(("http:", "https:", "//", "data:"))
        assert not any(name.startswith("on") for name in attrs)
    lowered = script.lower()
    for token in (
        "fetch(",
        "xmlhttprequest",
        "websocket",
        "eventsource",
        "sendbeacon",
        "rtcpeerconnection",
        "eval(",
        "exec(",
        "new function",
        "innerhtml",
        "insertadjacenthtml",
        "document.write",
    ):
        assert token not in lowered
    assert '<script src="assets/app.js" defer></script>' in html
    assert '<link rel="stylesheet" href="assets/styles.css">' in html


def test_css_enforces_focus_touch_numerals_responsiveness_and_reduced_motion() -> None:
    _, css, _, _ = _interface()
    lowered = css.lower()

    assert ":focus-visible" in css
    assert "min-height: 44px" in css
    assert "font-variant-numeric: tabular-nums" in css
    assert "@media (max-width:" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "transition: all" not in lowered
    assert "Inter," not in css
    assert ".hero" not in css
    assert ".card-grid" not in css
