"""Generate the dependency-free static safety-monitor demonstration."""
# ruff: noqa: E501 -- embedded HTML, CSS, and JavaScript preserve generated source lines

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DEMO_FORMAT = "oscillink-safety-monitor-demo-v1"
EVIDENCE_LABEL = "SYNTHETIC EVIDENCE — SOFTWARE BEHAVIOR ONLY"
PHYSICAL_STOP_NOTICE = "No physical stop established"

STYLES = """:root {
  color-scheme: dark;
  --ink: #dbe9ee;
  --muted: #8da0aa;
  --dim: #60717a;
  --base: #071014;
  --panel: #0a171c;
  --panel-strong: #0d2026;
  --line: #1c3a43;
  --line-strong: #2c6570;
  --cyan: #54e6e7;
  --amber: #ffbd5b;
  --red: #ff6b73;
  --green: #77e1a0;
  --sans: "Segoe UI Variable", "Aptos", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  --mono: "Cascadia Mono", "SFMono-Regular", Consolas, "Liberation Mono", monospace;
}

* {
  box-sizing: border-box;
}

html {
  min-width: 320px;
  background: var(--base);
}

body {
  min-height: 100vh;
  margin: 0;
  color: var(--ink);
  background:
    linear-gradient(rgba(84, 230, 231, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(84, 230, 231, 0.025) 1px, transparent 1px),
    radial-gradient(circle at 75% -10%, #12343d 0, transparent 34rem),
    var(--base);
  background-size: 28px 28px, 28px 28px, auto, auto;
  font-family: var(--sans);
  line-height: 1.5;
}

body::before {
  position: fixed;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--cyan), transparent);
  content: "";
  opacity: 0.75;
  pointer-events: none;
}

.skip-link {
  position: absolute;
  z-index: 10;
  top: 0.5rem;
  left: 0.5rem;
  padding: 0.75rem 1rem;
  color: var(--base);
  background: var(--cyan);
  transform: translateY(-160%);
}

.skip-link:focus {
  transform: translateY(0);
}

.site-header,
.workspace,
.site-footer {
  width: min(100% - 2rem, 1440px);
  margin-inline: auto;
}

.site-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 2rem;
  padding-block: 1.5rem 1rem;
  border-bottom: 1px solid var(--line-strong);
}

.product-mark,
.eyebrow,
.section-kicker,
.term,
.hash-key {
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.product-mark {
  margin: 0;
  color: var(--cyan);
  font-family: var(--mono);
  font-size: 0.82rem;
  font-weight: 700;
}

.site-header h1 {
  max-width: 28ch;
  margin: 0.2rem 0 0;
  font-size: clamp(1.35rem, 3vw, 2.15rem);
  font-weight: 620;
  letter-spacing: -0.025em;
}

.mode-label {
  margin: 0;
  color: var(--muted);
  font-family: var(--mono);
  font-size: 0.78rem;
  text-align: right;
}

.evidence-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: min(100% - 2rem, 1440px);
  min-height: 44px;
  margin: 1rem auto 0;
  padding: 0.65rem 1rem;
  border: 1px solid #725b27;
  color: #ffe2a8;
  background: #211b0d;
  font-family: var(--mono);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.07em;
}

.evidence-banner::before {
  flex: 0 0 auto;
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  background: var(--amber);
  box-shadow: 0 0 0.8rem rgba(255, 189, 91, 0.55);
  content: "";
}

.workspace {
  display: grid;
  grid-template-columns: minmax(0, 2.15fr) minmax(300px, 0.85fr);
  gap: 1rem;
  padding-block: 1rem 2rem;
}

.monitor,
.inspect {
  min-width: 0;
  border: 1px solid var(--line);
  background: rgba(8, 23, 28, 0.94);
}

.monitor {
  border-top-color: var(--cyan);
}

.inspect {
  align-self: start;
  border-top-color: var(--amber);
}

.section-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.15rem;
  border-bottom: 1px solid var(--line);
  background: var(--panel-strong);
}

.section-kicker {
  display: block;
  margin-bottom: 0.2rem;
  color: var(--dim);
  font-family: var(--mono);
  font-size: 0.68rem;
  font-weight: 700;
}

.section-header h2,
.signal-section h3,
.decision-section h3,
.output-section h3,
.recovery-section h3,
.inspect h3 {
  margin: 0;
  font-weight: 620;
}

.section-header h2 {
  font-size: 1rem;
}

.scenario-state {
  color: var(--green);
  font-family: var(--mono);
  font-size: 0.76rem;
  font-variant-numeric: tabular-nums;
}

.scenario-picker {
  padding: 1rem 1.15rem;
  border-bottom: 1px solid var(--line);
}

.scenario-picker label {
  display: block;
  margin-bottom: 0.4rem;
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 650;
}

select,
summary {
  min-height: 44px;
}

select {
  width: 100%;
  padding: 0.65rem 2.5rem 0.65rem 0.8rem;
  border: 1px solid var(--line-strong);
  border-radius: 0;
  color: var(--ink);
  background: #071217;
  font: 0.9rem var(--mono);
}

.help {
  margin: 0.45rem 0 0;
  color: var(--dim);
  font-size: 0.75rem;
}

.identity-line {
  display: grid;
  grid-template-columns: minmax(12rem, 0.7fr) minmax(0, 1.3fr);
  gap: 1rem;
  padding: 0.85rem 1.15rem;
  border-bottom: 1px solid var(--line);
}

.identity-line p {
  margin: 0;
}

.case-id,
.mono,
.value,
.hash-value,
.metric-value,
td:first-child,
td:nth-child(2) {
  font-family: var(--mono);
  font-variant-numeric: tabular-nums;
}

.case-id {
  color: var(--cyan);
  font-size: 0.82rem;
  overflow-wrap: anywhere;
}

.case-title {
  font-size: 0.95rem;
}

.signal-section,
.decision-section,
.output-section,
.recovery-section {
  padding: 1rem 1.15rem;
  border-bottom: 1px solid var(--line);
}

.signal-section h3,
.decision-section h3,
.output-section h3,
.recovery-section h3,
.inspect h3 {
  margin-bottom: 0.8rem;
  color: var(--muted);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.signal-list,
.decision-list,
.output-list,
.recovery-list,
.hash-list,
.metric-list {
  display: grid;
  grid-template-columns: minmax(9rem, 0.72fr) minmax(0, 1.28fr);
  gap: 0;
  margin: 0;
}

.signal-list > *,
.decision-list > *,
.output-list > *,
.recovery-list > *,
.hash-list > *,
.metric-list > * {
  min-width: 0;
  margin: 0;
  padding: 0.55rem 0;
  border-top: 1px solid rgba(44, 101, 112, 0.38);
}

.term,
.hash-key {
  color: var(--dim);
  font-family: var(--mono);
  font-size: 0.67rem;
  font-weight: 700;
}

.value {
  color: var(--ink);
  font-size: 0.8rem;
  overflow-wrap: anywhere;
}

.signal-blocks {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.signal-blocks > div {
  min-width: 0;
}

.signal-blocks h4 {
  margin: 0 0 0.5rem;
  color: var(--cyan);
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.decision-list .action-value {
  color: var(--amber);
  font-weight: 750;
}

.first-out {
  color: var(--red);
}

.physical-stop {
  color: #ffacb1;
  font-weight: 800;
}

.output-list {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.output-list > div {
  min-width: 0;
  padding: 0 0.75rem;
  border-left: 1px solid var(--line);
}

.output-list > div:first-child {
  padding-left: 0;
  border-left: 0;
}

.output-list dt,
.output-list dd {
  margin: 0;
}

.output-list dd {
  margin-top: 0.35rem;
}

.inspect-block {
  padding: 1rem 1.15rem;
  border-bottom: 1px solid var(--line);
}

.hash-list {
  display: block;
}

.hash-list dt {
  padding-bottom: 0.15rem;
  border-top: 1px solid rgba(44, 101, 112, 0.38);
}

.hash-list dd {
  padding-top: 0;
  border-top: 0;
}

.hash-value {
  display: block;
  color: #a9c6cd;
  font-size: 0.67rem;
  overflow-wrap: anywhere;
}

.metric-list {
  grid-template-columns: minmax(8rem, 1fr) auto;
}

.metric-value {
  color: var(--green);
  font-size: 0.78rem;
  text-align: right;
}

details {
  border-top: 1px solid var(--line);
}

summary {
  display: flex;
  align-items: center;
  padding: 0.7rem 1.15rem;
  color: var(--cyan);
  background: #08171c;
  cursor: pointer;
  font-family: var(--mono);
  font-size: 0.76rem;
  font-weight: 700;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.72rem;
}

th,
td {
  padding: 0.65rem 0.7rem;
  border-top: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}

th {
  color: var(--dim);
  font-family: var(--mono);
  font-size: 0.64rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

td:last-child {
  min-width: 22rem;
  color: var(--muted);
  overflow-wrap: anywhere;
}

.site-footer {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding-block: 1rem 2rem;
  border-top: 1px solid var(--line);
  color: var(--dim);
  font-size: 0.74rem;
}

:focus-visible {
  outline: 3px solid var(--amber);
  outline-offset: 3px;
}

[hidden] {
  display: none !important;
}

@media (max-width: 980px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .inspect {
    align-self: stretch;
  }
}

@media (max-width: 680px) {
  .site-header,
  .identity-line,
  .site-footer {
    display: block;
  }

  .mode-label {
    margin-top: 0.75rem;
    text-align: left;
  }

  .signal-blocks,
  .output-list {
    grid-template-columns: 1fr;
  }

  .signal-blocks > div + div {
    padding-top: 0.8rem;
  }

  .output-list > div {
    padding: 0.75rem 0 0;
    border-top: 1px solid var(--line);
    border-left: 0;
  }

  .signal-list,
  .decision-list,
  .recovery-list,
  .metric-list {
    grid-template-columns: 1fr;
  }

  .signal-list dd,
  .decision-list dd,
  .recovery-list dd,
  .metric-list dd {
    padding-top: 0;
    border-top: 0;
    text-align: left;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
"""

APP = """"use strict";

const dataNode = document.getElementById("demo-data");
const scenarioSelect = document.getElementById("scenario-select");

if (!(dataNode instanceof HTMLScriptElement) || !(scenarioSelect instanceof HTMLSelectElement)) {
  throw new Error("Static demonstration contract is incomplete");
}

const demo = JSON.parse(dataNode.textContent || "{}");

function byId(id) {
  const node = document.getElementById(id);
  if (node === null) {
    throw new Error(`Missing interface node: ${id}`);
  }
  return node;
}

function text(id, value) {
  byId(id).textContent = value === null || value === undefined || value === "" ? "—" : String(value);
}

function yesNo(value) {
  return value ? "yes" : "no";
}

function joined(value) {
  return Array.isArray(value) && value.length > 0 ? value.join(", ") : "none";
}

function timelineState(event) {
  return event.decision_state || event.latched_state || event.recovery_stage || event.disposition || "recorded";
}

function renderTimeline(events) {
  const body = byId("timeline-body");
  body.replaceChildren();
  events.forEach((event) => {
    const row = document.createElement("tr");
    const values = [event.step, event.kind, timelineState(event), JSON.stringify(event)];
    values.forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = String(value);
      row.append(cell);
    });
    body.append(row);
  });
}

function renderScenario(caseRecord) {
  const final = caseRecord.final;
  text("case-id", caseRecord.case_id);
  text("case-title", caseRecord.title);
  text("fault-families", joined(caseRecord.fault_families));
  text("intent-kind", final.production_intent.command_kind);
  text("intent-motion", yesNo(final.production_intent.motion_requested));
  text("occupancy", joined(final.occupancy));
  text("motion-commanded", yesNo(final.motion.commanded));
  text("motion-measured", yesNo(final.motion.measured));
  text("motion-speed", final.motion.speed_mps);
  text("motion-acceleration", final.motion.acceleration_mps2);
  text("health-state", final.source_health.source_state);
  text("clock-state", final.source_health.clock_state);
  text("policy-state", final.policy_state);
  text("outcome-action", caseRecord.outcome_action);
  text("first-out", final.first_out_reason);
  text("reason-codes", joined(final.reason_codes));
  text("request-state", final.request_state);
  text("ack-state", final.acknowledgment_state);
  text("latched", yesNo(final.latched));
  text("recovery-stage", final.recovery_stage);
  text("fresh-start", yesNo(final.fresh_start_required));
  text("reset-sequence", final.reset_sequence);
  text("scenario-hash", caseRecord.scenario_identity);
  text("case-hash", caseRecord.case_sha256);
  text("config-hash", caseRecord.configuration_sha256);
  text("authority-hash", caseRecord.configuration_authority_sha256);
  text("input-hashes", joined(final.input_sha256));
  text("report-hash", caseRecord.report_sha256);
  text("runtime-hash", caseRecord.runtime_format_sha256);
  renderTimeline(caseRecord.timeline);
}

function initialize() {
  demo.cases.forEach((caseRecord, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `${String(index + 1).padStart(2, "0")} · ${caseRecord.case_id} · ${caseRecord.title}`;
    scenarioSelect.append(option);
  });
  text("metric-exact", `${demo.metrics.exact_matches}/${demo.metrics.total_cases}`);
  text("metric-runs", demo.metrics.deterministic_repeatability.runs_per_case);
  text("metric-families", `${demo.metrics.fault_family_coverage.covered_families}/${demo.metrics.fault_family_coverage.total_required}`);
  text("metric-executions", demo.metrics.deterministic_repeatability.total_executions);
  text("benchmark-hash", demo.source.benchmark_manifest_sha256);
  text("expected-hash", demo.source.expected_results_sha256);
  text("metrics-hash", demo.source.metrics_sha256);
  text("data-hash", demo.payload_sha256);
  text("baseline-commit", demo.source.runtime_baseline_commit);
  renderScenario(demo.cases[0]);
}

scenarioSelect.addEventListener("change", () => {
  const selected = demo.cases[Number.parseInt(scenarioSelect.value, 10)];
  if (selected !== undefined) {
    renderScenario(selected);
  }
});

initialize();
"""

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Read-only synthetic evidence monitor for the Oscillink robot-cell benchmark.">
  <title>Oscillink Safety Ops · Synthetic Monitor</title>
  <link rel="stylesheet" href="assets/styles.css">
  <script src="assets/app.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#monitor">Skip to monitor</a>
  <header class="site-header">
    <div>
      <p class="product-mark">OSCILLINK / SAFETY OPS</p>
      <h1>Robot-cell supervisor evidence monitor</h1>
    </div>
    <p class="mode-label">MONITOR PRIMARY · INSPECT SECONDARY · READ ONLY</p>
  </header>

  <div class="evidence-banner" role="note">SYNTHETIC EVIDENCE — SOFTWARE BEHAVIOR ONLY</div>

  <main class="workspace">
    <section id="monitor" class="monitor" aria-labelledby="monitor-heading">
      <header class="section-header">
        <div>
          <span class="section-kicker">PRIMARY VIEW</span>
          <h2 id="monitor-heading">Deterministic monitor</h2>
        </div>
        <span class="scenario-state">LOCAL · CLOSED FILE</span>
      </header>

      <div class="scenario-picker">
        <label for="scenario-select">Synthetic benchmark scenario</label>
        <select id="scenario-select" aria-describedby="selector-help"></select>
        <p id="selector-help" class="help">Selection changes the displayed evidence only. It sends no command or acknowledgment.</p>
      </div>

      <div class="identity-line" aria-label="Exact scenario identity">
        <p id="case-id" class="case-id">Loading scenario identity…</p>
        <p id="case-title" class="case-title">Loading deterministic result…</p>
      </div>

      <section class="signal-section" aria-labelledby="signals-heading">
        <h3 id="signals-heading">Intent and independent observations</h3>
        <div class="signal-blocks">
          <div>
            <h4>Production intent</h4>
            <dl class="signal-list">
              <dt class="term">Kind</dt><dd id="intent-kind" class="value">—</dd>
              <dt class="term">Motion requested</dt><dd id="intent-motion" class="value">—</dd>
            </dl>
          </div>
          <div>
            <h4>Independent occupancy</h4>
            <dl class="signal-list">
              <dt class="term">Zone state</dt><dd id="occupancy" class="value">—</dd>
              <dt class="term">Independent motion</dt><dd id="motion-measured" class="value">—</dd>
              <dt class="term">Commanded</dt><dd id="motion-commanded" class="value">—</dd>
              <dt class="term">Speed m/s</dt><dd id="motion-speed" class="value">—</dd>
              <dt class="term">Acceleration m/s²</dt><dd id="motion-acceleration" class="value">—</dd>
            </dl>
          </div>
          <div>
            <h4>Independent source health</h4>
            <dl class="signal-list">
              <dt class="term">Source</dt><dd id="health-state" class="value">—</dd>
              <dt class="term">Clock</dt><dd id="clock-state" class="value">—</dd>
            </dl>
          </div>
        </div>
      </section>

      <section class="decision-section" aria-labelledby="decision-heading">
        <h3 id="decision-heading">Deterministic decision</h3>
        <dl class="decision-list">
          <dt class="term">Deterministic state</dt><dd id="policy-state" class="value">—</dd>
          <dt class="term">Deterministic action</dt><dd id="outcome-action" class="value action-value">—</dd>
          <dt class="term">First-out reason</dt><dd id="first-out" class="value first-out">—</dd>
          <dt class="term">Contributing reasons · sorted</dt><dd id="reason-codes" class="value">—</dd>
          <dt class="term">Fault families</dt><dd id="fault-families" class="value">—</dd>
        </dl>
      </section>

      <section class="output-section" aria-labelledby="output-heading">
        <h3 id="output-heading">Request ≠ acknowledgment ≠ physical stop</h3>
        <dl class="output-list">
          <div><dt class="term">Request</dt><dd id="request-state" class="value">—</dd></div>
          <div><dt class="term">Acknowledgment</dt><dd id="ack-state" class="value">—</dd></div>
          <div><dt class="term">Physical stop</dt><dd id="physical-stop" class="value physical-stop">No physical stop established</dd></div>
        </dl>
      </section>

      <section class="recovery-section" aria-labelledby="recovery-heading">
        <h3 id="recovery-heading">Latch / recovery</h3>
        <dl class="recovery-list">
          <dt class="term">Latched</dt><dd id="latched" class="value">—</dd>
          <dt class="term">Recovery stage</dt><dd id="recovery-stage" class="value">—</dd>
          <dt class="term">Fresh start required</dt><dd id="fresh-start" class="value">—</dd>
          <dt class="term">Reset sequence record</dt><dd id="reset-sequence" class="value">—</dd>
        </dl>
      </section>

      <details>
        <summary>Inspect event evidence</summary>
        <div class="table-wrap">
          <table>
            <caption class="section-kicker">Exact deterministic timeline records</caption>
            <thead><tr><th>Step</th><th>Kind</th><th>State</th><th>Evidence</th></tr></thead>
            <tbody id="timeline-body"></tbody>
          </table>
        </div>
      </details>
    </section>

    <aside id="inspect" class="inspect" aria-labelledby="inspect-heading">
      <header class="section-header">
        <div>
          <span class="section-kicker">SECONDARY VIEW</span>
          <h2 id="inspect-heading">Evidence inspection</h2>
        </div>
      </header>

      <section class="inspect-block" aria-labelledby="scenario-binding-heading">
        <h3 id="scenario-binding-heading">Scenario binding</h3>
        <dl class="hash-list">
          <dt class="hash-key">Scenario identity</dt><dd><code id="scenario-hash" class="hash-value">—</code></dd>
          <dt class="hash-key">Case SHA-256</dt><dd><code id="case-hash" class="hash-value">—</code></dd>
          <dt class="hash-key">Configuration SHA-256</dt><dd><code id="config-hash" class="hash-value">—</code></dd>
          <dt class="hash-key">Authority SHA-256</dt><dd><code id="authority-hash" class="hash-value">—</code></dd>
          <dt class="hash-key">Input SHA-256</dt><dd><code id="input-hashes" class="hash-value">—</code></dd>
          <dt class="hash-key">Report SHA-256</dt><dd><code id="report-hash" class="hash-value">—</code></dd>
          <dt class="hash-key">Runtime SHA-256</dt><dd><code id="runtime-hash" class="hash-value">—</code></dd>
        </dl>
      </section>

      <section class="inspect-block" aria-labelledby="corpus-binding-heading">
        <h3 id="corpus-binding-heading">Benchmark / data hashes</h3>
        <dl class="hash-list">
          <dt class="hash-key">Benchmark manifest SHA-256</dt><dd><code id="benchmark-hash" class="hash-value">—</code></dd>
          <dt class="hash-key">Expected results SHA-256</dt><dd><code id="expected-hash" class="hash-value">—</code></dd>
          <dt class="hash-key">Metrics SHA-256</dt><dd><code id="metrics-hash" class="hash-value">—</code></dd>
          <dt class="hash-key">Data payload SHA-256</dt><dd><code id="data-hash" class="hash-value">—</code></dd>
          <dt class="hash-key">Runtime baseline commit</dt><dd><code id="baseline-commit" class="hash-value">—</code></dd>
        </dl>
      </section>

      <section class="inspect-block" aria-labelledby="metrics-heading">
        <h3 id="metrics-heading">Mechanically derived metrics</h3>
        <dl class="metric-list">
          <dt class="term">Exact cases</dt><dd id="metric-exact" class="metric-value">—</dd>
          <dt class="term">Runs per case</dt><dd id="metric-runs" class="metric-value">—</dd>
          <dt class="term">Fault families</dt><dd id="metric-families" class="metric-value">—</dd>
          <dt class="term">Executions</dt><dd id="metric-executions" class="metric-value">—</dd>
        </dl>
      </section>
    </aside>
  </main>

  <footer class="site-footer">
    <span>Read-only benchmark inspection. No runtime machine interface.</span>
    <span>PLr · SIL · stopping time · DC · application validation · common cause: TBD</span>
  </footer>

  <script id="demo-data" type="application/json">__DEMO_DATA__</script>
</body>
</html>
"""


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _manifest_files(manifest: dict[str, Any]) -> dict[str, str]:
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("benchmark manifest files are unavailable")
    result: dict[str, str] = {}
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("path"), str)
            or not isinstance(entry.get("sha256"), str)
        ):
            raise ValueError("benchmark manifest file entry is invalid")
        result[entry["path"]] = entry["sha256"]
    return result


def build_demo_data(benchmark_root: Path, *, source_repository: Path) -> dict[str, Any]:
    """Build display data from exact benchmark expected results and metrics."""

    manifest_raw = (benchmark_root / "benchmark-manifest.json").read_bytes()
    expected_raw = (benchmark_root / "expected-results.jsonl").read_bytes()
    metrics_raw = (benchmark_root / "metrics.json").read_bytes()
    manifest = json.loads(manifest_raw)
    metrics = json.loads(metrics_raw)
    entries = _manifest_files(manifest)
    if sha256(expected_raw) != entries.get("expected-results.jsonl"):
        raise ValueError("expected-results hash does not match benchmark manifest")
    if sha256(metrics_raw) != entries.get("metrics.json"):
        raise ValueError("metrics hash does not match benchmark manifest")
    cases: list[dict[str, Any]] = []
    for raw in expected_raw.splitlines(keepends=True):
        case = json.loads(raw)
        case["report_sha256"] = sha256(raw)
        cases.append(case)
    if len(cases) != 36 or metrics.get("total_cases") != len(cases):
        raise ValueError("demo requires all 36 benchmark expected results")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "demo_format": DEMO_FORMAT,
        "evidence_label": EVIDENCE_LABEL,
        "physical_stop_notice": PHYSICAL_STOP_NOTICE,
        "source": {
            "benchmark_manifest_sha256": sha256(manifest_raw),
            "expected_results_sha256": entries["expected-results.jsonl"],
            "metrics_sha256": entries["metrics.json"],
            "runtime_baseline_commit": manifest["runtime_baseline_commit"],
            "demo_generator_sha256": sha256(
                (source_repository / "scripts" / "generate_demo.py").read_bytes()
            ),
        },
        "metrics": metrics,
        "cases": cases,
    }
    payload["payload_sha256"] = sha256(canonical_json(payload))
    return payload


def generate_demo(
    destination: Path, *, benchmark_root: Path, source_repository: Path
) -> dict[str, Any]:
    """Write byte-deterministic local static assets."""

    data = build_demo_data(benchmark_root, source_repository=source_repository)
    data_raw = canonical_json(data)
    embedded = data_raw.decode("utf-8").strip().replace("<", "\\u003c")
    html = HTML.replace("__DEMO_DATA__", embedded)
    assets = destination / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (destination / "index.html").write_bytes(html.encode("utf-8"))
    (assets / "styles.css").write_bytes(STYLES.encode("utf-8"))
    (assets / "app.js").write_bytes(APP.encode("utf-8"))
    (assets / "data.json").write_bytes(data_raw)
    return data


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, default=root / "benchmark" / "robot_cell_v1")
    parser.add_argument("--destination", type=Path, default=root / "demo")
    args = parser.parse_args()
    generate_demo(args.destination, benchmark_root=args.benchmark_root, source_repository=root)


if __name__ == "__main__":
    main()
