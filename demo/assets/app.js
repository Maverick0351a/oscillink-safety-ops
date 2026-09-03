"use strict";

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
