# Open-source and public-demo strategy for Oscillink Safety Ops

**Research cutoff:** 2026-09-02  
**Evidence labels:** `verified` = canonical repository or official record inspected; `author claim` = publisher/dataset claim not independently reproduced; `proposal` = recommended experiment or architecture.  
**Current baseline inspected:** 173 locally collected deterministic tests; read-only Python 3.11 evidence contracts; Windows and prior Linux build evidence; no hosted CI, external tester, industrial partner, field deployment, safety rating, or certification evidence.

## Executive decision

The strongest credible public story is **not** “an AI safety system proved in simulation.” It is:

> A deterministic, read-only evidence supervisor with exact-byte provenance, public adversarial fixtures, replayable ROS/PLC simulation evidence, model-checked authority invariants, reproducible releases, and an explicit validation ladder.

The next credibility bottleneck is hosted reproducibility, not a larger simulator. Establish hosted Linux/Windows CI, release provenance, and a frozen benchmark before adding ROS 2/Gazebo. Then add one industrially legible simulation fixture, one PLC/software-in-the-loop fixture, public-log adapter tests, and an optional isolated hardware bench. Keep simulator, PLC, and fault-injector code outside the product's authority boundary: they create test evidence; Safety Ops only reads finalized exports.

No solo test, public dataset, simulator run, formal model, CI badge, or HIL bench can establish field fitness, legal applicability, functional-safety integrity, safe operation, practitioner acceptance, or certification. The repository should say this wherever results appear.

## 1. Claim and authority boundary

### Public claim that is supportable now

“Experimental, deterministic, read-only evidence infrastructure for offline review of physical-intelligence artifacts.”

### Claims to prohibit

- “safety-rated,” “certified,” “validated for industrial use,” “field-proven,” or “production ready”;
- “detects all hazards,” “prevents incidents,” “proves compliance,” or “approves operation”;
- “digital twin” for a Gazebo/Isaac scene without measured plant calibration;
- “independently validated” when all runs are authored and executed by the maintainer;
- “HIL-validated” without identifying the exact hardware, firmware, wiring, calibration, test scope, and non-industrial bench limitations; and
- aggregate “safety scores” that hide missing, ambiguous, stale, or conflicting evidence.

### Evidence-tier vocabulary

| Tier | Label | Minimum evidence | What it may support |
|---|---|---|---|
| E0 | Contract test | Unit/property/fuzz test on synthetic bytes | Specific software behavior under stated inputs |
| E1 | Reproducible synthetic benchmark | Frozen fixtures, hidden expected outputs, exact environment and hashes, hosted rerun | Reproducibility and measured behavior on the benchmark distribution |
| E2 | SIL/replay | Version-pinned ROS/Gazebo/PLC simulator or public recording, deterministic export and replay | Adapter behavior and scenario coverage in that software/log environment |
| E3 | Isolated HIL bench | Exact BOM, firmware, wiring, calibration, oscilloscope/log evidence, repeated runs | Bench I/O, timing, protocol, and failure-handling behavior for that setup |
| E4 | External lab/practitioner evaluation | Independent operator, frozen protocol, preserved raw results | External reproducibility or workflow evidence in that bounded setting |
| E5 | Field/certification evidence | Qualified lifecycle, relevant plant/system, authorities and assessors | Only the claims expressly supported by that process |

The project is at E0 with pieces of release/cross-platform evidence. Hosted CI advances reproducibility, not external validity.

## 2. Credible simulation and automation stack

### Recommended stack

| Component | Canonical URL and license/status | Concrete use | What it can establish | What it cannot establish |
|---|---|---|---|---|
| **ROS 2 Jazzy + Gazebo Harmonic** | Official pairing documentation; `gz-sim` is Apache-2.0.[1][2] Jazzy is an LTS ROS release supported through May 2029.[3] | Primary open SIL environment. Pin container digest, SDF world, ROS packages, physics step, random seed, QoS, locale, and CPU architecture. Run headless. | ROS integration, observer/export behavior, scenario replay, timing/loss behavior in the pinned simulator. | Real sensor performance, contact fidelity, human behavior, plant dynamics, deterministic equivalence across physics engines/CPUs, or field safety. |
| **rosbag2 + MCAP** | `rosbag2` is Apache-2.0; MCAP is MIT.[4][43] | Immutable episode envelope and replay artifact. Ingest only closed recordings; never replay into a live robot graph from Safety Ops. | Exact recorded topic/schema/timestamp provenance, offline parser behavior, repeatable regression inputs. | Completeness or truth of what was recorded; absence of dropped/unlogged events; causal or safety conclusions. |
| **ROS `launch_testing`** | Official ROS integration-test framework.[5] | Assert simulator/test-harness process exit, observer isolation, expected topics/files, and clean shutdown. | Process-level and integration behavior in CI. | Physical correctness or hazard coverage. |
| **NIST ARIAC 2025** | NIST's Gazebo/ROS 2 industrial-automation competition simulates EV-cell inspection, kitting, module construction, noisy voltage readings, defective cells, collision penalties, tool change, and welding workflow.[6] | Best industrially legible public scenario base. Generate a short, project-authored MCAP and evidence envelope from one trial. | Adaptation to a dynamic manufacturing-style simulation and realistic multi-robot/log schemas. | A safety benchmark, a faithful factory model, or field validation. **Rights caveat:** the GitHub repository exposed no detected top-level license at the cutoff; link to/pin it, but do not redistribute ARIAC source/assets until NIST rights are clarified.[7] |
| **Isaac Sim 6.x, optional showcase** | Repository source is Apache-2.0, but Omniverse Kit, models, textures, and other runtime components have separate NVIDIA terms; redistribution/service delivery can require NVIDIA AI Enterprise.[8] Current requirements call for a substantial RTX-capable workstation.[9] | Optional GPU-rendered variant of the same export contract, run locally or on a documented GPU runner. Publish only project-owned fixture/output bytes whose rights are clear. | Portability of the observer/export contract to a second simulator; photorealistic synthetic-data pipeline behavior. | Greater physical validity merely from rendering fidelity; an open-source-only deployment; affordable hosted reproducibility. |
| **Isaac Lab, optional** | BSD-3-Clause repository.[46] | Saved rollout/evaluation adapter, never an action wrapper. | Compatibility with Gymnasium-style observations/actions/events in saved rollouts. | Policy safety, deployment fitness, or runtime authority. |
| **MuJoCo, secondary micro-sim** | Apache-2.0.[48] | Fast, CPU-friendly contact/trajectory micro-fixtures when full ROS is unnecessary. | Portable dynamics regression for a narrow model. | ROS/industrial integration or plant fidelity. |
| **Webots, secondary cross-platform sim** | Apache-2.0.[49] | Windows-friendly interactive demo or second-engine differential check. | Cross-simulator adapter behavior and model discrepancy discovery. | Which simulator is physically correct. |
| **Safety Gymnasium, research-only** | Apache-2.0 safe-RL benchmark.[17] | Only if publishing a separate constrained-RL comparison; consume saved rollouts through the evidence contract. | Cost/constraint accounting for safe-RL algorithms in its benchmark tasks. | Industrial hazards, robot-cell validation, functional safety, or evidence-system quality. It is not a priority for the current product. |

### PLC and embedded alternatives

| Tool | Canonical URL and license/limitation | Recommended role | Evidence limit |
|---|---|---|---|
| **OpenPLC Runtime v4** | Current runtime is MIT.[10] The v4 editor is GPL-3.0.[11] The old v3 runtime is EOL and GPL-3.0, so do not start new work on it. | Headless IEC 61131-3 SIL fixture in a separate container. The harness may drive synthetic I/O and export scan/input/output events; Safety Ops reads only the export. | Demonstrates behavior of the pinned OpenPLC build and program, not a safety PLC, certified compiler/runtime, deterministic real-time execution, or IEC 61508 conformance. Respect editor/runtime license boundaries in redistributed images. |
| **Eclipse 4diac FORTE** | EPL-2.0 portable C++ IEC 61499 runtime for embedded/distributed control.[12] | Better open alternative when distributed function-block/event semantics are the experiment. Pair with its IDE only as a fixture authoring tool. | IEC 61499 experiment, not a drop-in IEC 61131/CODESYS equivalence or certified controller. |
| **CODESYS Development System** | Free of charge for end users but subject to an EULA; add-ons and SoftPLC/device runtimes use product/device licensing.[13] | Optional compatibility export produced by a user-owned installation. Keep it out of the default open demo and container images. | Shows compatibility with one licensed setup only. “Free to use” is not open source and does not grant redistribution rights. |
| **Renode** | MIT; runs unmodified embedded binaries in simulated SoCs and supports automated Robot Framework testing.[14] | Firmware-in-the-loop precursor for a sensor gateway or log exporter. | Binary/peripheral behavior in the modeled SoC, not analog behavior, electrical safety, or physical timing equivalence. |

**Do not integrate a real safety PLC, robot controller, interlock, or E-stop.** If a later hardware bench is built, use extra-low-voltage LEDs/relays or a loopback board with no machine, process energy, or mains load.

## 3. Deterministic reference architecture

```text
Scenario source                       Test/control plane (not product)
  synthetic YAML ─┐                   Gazebo / ARIAC / OpenPLC / Renode
  public bag ─────┼────> immutable export: MCAP / JSONL / Parquet / files
  public dataset ─┘                                  │
                                                     │ close + hash
                                                     v
Read-only product boundary
  bounded byte reader -> Physical Intelligence Evidence Envelope
      -> deterministic adapter normalization
      -> exact Safety Memory Packet + policy/config hash
      -> pure reconciliation/audit state machine
      -> immutable Audit / Episode Evaluation Report
      -> display/export sidecar

No publisher, action client, service client, controller address, write credential,
permit token, callback, replay path, or equipment command exists inside the product.
```

### Determinism contract

For identical input bytes, policy bytes, adapter version/configuration, locale, timezone, and package lock:

1. canonical JSON bytes are identical;
2. finding order and primary/contributing-state precedence are identical;
3. generated JSON Schemas are byte-identical;
4. source inputs are unchanged;
5. every payload, report, and release artifact has a declared byte count and SHA-256;
6. clocks and random seeds appear only in the test harness, never as implicit report inputs; and
7. simulator nondeterminism is captured as observed evidence rather than normalized away.

Use JSON as the control plane, MCAP as the episode container, and Parquet only for cohort/catalog analysis. LeRobot and HFlow are both Apache-2.0 candidates for later read-only finalized-dataset/catalog adapters, not replacements for the core evidence contract.[42][44] Do not invent one universal robot-plan ontology.

## 4. Concrete public demo fixtures

### Fixture A — `synthetic_press_v2` (fast, always-on)

Extend the current press/LOTO fixture rather than replacing it.

**Inputs:** synthetic nameplate, manual excerpt, site SOP, proposed plan, episode JSON/MCAP, exact manifest.  
**Seeded conditions:** wrong serial, stale SOP, omitted stored hydraulic energy, “press stop” without isolation evidence, missing verification, source conflict, ambiguous role, unreadable field, duplicate/out-of-order telemetry, and changed adapter configuration.  
**Expected evidence:** one deterministic report for each single fault, a pairwise interaction subset, and negative controls.  
**Public UX:** instant static demo and downloadable bundle.  
**Establishes:** contract behavior and no-authority invariants on project-authored bytes.  
**Does not establish:** whether the synthetic procedure is legally or operationally correct.

### Fixture B — `ariac_cell_line_001` (industrial SIL)

**Harness:** ROS 2 Jazzy + Gazebo Harmonic + a pinned ARIAC 2025 checkout/container.  
**Run:** one short EV-cell inspection/kitting scenario with a defective cell, noisy voltage, a good-cell negative control, and one collision or invalid-placement event. ARIAC natively supplies this manufacturing vocabulary.[6]  
**Export:** selected `/tf`, `/joint_states`, inspection, voltage, competition-state, and event topics to MCAP; a generated manifest records repo commit, container digest, SDF hash, ROS/Gazebo versions, physics parameters, seed, QoS, start/end simulation time, topic inventory, and any recorder loss events.  
**Product action:** offline envelope validation and evidence findings only. No ROS publisher, subscriber to a live graph, service client, action client, or replay command ships in the core package.  
**Rights:** generate the run locally; do not commit ARIAC assets until NIST clarifies the repository license. Commit only project-authored normalized metadata and, if legally cleared, a small output recording.  
**Establishes:** adapter and evidence-state behavior in a manufacturing-style ROS/Gazebo scenario.  
**Does not establish:** cell-manufacturing expertise, collision safety, or real-factory performance.

### Fixture C — `plc_isolation_loop_001` (PLC SIL)

**Plant:** project-authored, discrete synthetic hydraulic accumulator with `motor_running`, `supply_valve`, `pressure`, `guard`, and `bleed_confirmed` states.  
**Controller:** pinned OpenPLC Runtime v4 program. The fixture harness, not Safety Ops, controls the simulated plant and PLC inputs.  
**Scenarios:** nominal sequence; input stuck high; sensor chatter; delayed scan/export; Modbus/TCP latency and disconnect; stale recipe revision; restart with lost volatile state; contradictory pressure sensors; missing bleed verification.  
**Network injection:** Toxiproxy is MIT and supports deterministic latency, timeout, bandwidth, reset, packet loss, and related TCP conditions for test environments.[15]  
**Export:** append-only JSONL with scan sequence, monotonic and wall timestamps, quality, input/output images, program hash, runtime version, and loss/warning records.  
**Establishes:** bounded export/normalization/change-impact behavior under a simulated PLC and network.  
**Does not establish:** PLC real-time guarantees, safe shutdown, SIL/PL, compiler correctness, or machinery behavior.

### Fixture D — `mcap_fault_corpus_001` (adapter robustness)

Start from a tiny project-authored MCAP, then generate reproducible mutations:

- truncation at every record class boundary;
- bad/absent index or summary;
- unknown schema/channel;
- duplicate, reversed, skipped, or non-monotonic timestamps;
- declared message-loss event;
- wrong frame ID, missing calibration, NaN/Inf/out-of-range value;
- topic freeze, delay, drop, duplicate, reorder, and burst;
- oversized attachment/metadata and decompression-limit cases; and
- changed bytes under a reused external filename.

Bosch publishes an Apache-2.0 ROS 2 rosbag fault-injection tool that can inform the offline mutation harness.[16] Use it in a separate test image, pin its version, and preserve the unmodified base bag. Polymath's Apache-2.0 replay-testing project is a useful comparator for ROS-node replay tests, but Safety Ops should remain a closed-file reader.[47]

**Establishes:** parser, resource-bound, provenance, missing/unsupported-field, and deterministic failure behavior.  
**Does not establish:** correct response of a robot to those faults.

### Fixture E — `public_robot_logs_001` (real-recording compatibility)

Do not use public logs as “safety validation.” Use them as schema diversity and adapter stress tests.

1. Download exact upstream bytes on demand.
2. Verify the record DOI/revision, declared checksum, local SHA-256, license, and byte count.
3. Never silently mirror human images/voices or large archives to GitHub/HF.
4. Keep upstream annotations distinct from Oscillink findings.
5. Treat one episode/run as the independent statistical unit, not frames or messages.

## 5. Public datasets and robot logs

| Dataset | Canonical URL; rights/scale | Best fixture use | What it can support | What it cannot support |
|---|---|---|---|---|
| **Successful/failed placement executions** | Zenodo DOI record, CC BY 4.0, 8.1 GB; Toyota HSR RGB/depth, force-torque, joints, calibration, frame anomalies; test set includes 60 anomalous and 7 successful trials.[27] | On-demand adapter/evaluation benchmark for falling object, disturbed shelf, occlusion, and external collision. Publish downloader + manifest, not the archive. | Real recorded multimodal parser and episode-label evaluation on one lab task. | Industrial representativeness, causal labels, general hazard detection, or field validity. |
| **IMAD-DS v2** | CC BY-SA 4.0, 5.1 GB; scaled robot arm/brushless motor, normal/abnormal microphone, accelerometer, gyroscope under operational/environmental domain shifts.[28] | Multi-rate Parquet adapter, grouped source/target-domain benchmark, sensor-loss and calibration metadata tests. | Robustness to multi-rate data and predefined domain shifts on scaled lab machines. | Full-scale industrial robot behavior, arbitrary anomaly coverage, or safety significance of anomalies. Share-alike obligations apply to adaptations. |
| **RoHuCAD 1.0** | CC BY 4.0, 9.3 GB; two eight-minute ROS Noetic bags with RGB-D, UR10e/AMR poses, and author annotations for human/robot workshop behavior.[29] | ROS1-bag-to-MCAP conversion test, human-zone event timeline, annotation provenance. Use an on-demand workflow; do not mirror identifiable imagery. | Compatibility with a real collaborative-workshop recording and its published labels. | That labeled behavior is legally “unsafe,” complete scenario coverage, causality, or privacy clearance for every downstream use. |
| **RoboFAC** | HF dataset card states MIT; over 10,000 videos, 9,440 erroneous trajectories, 78,623 QA pairs, 16 manipulation tasks, mixed simulation/real data.[30] | Optional HF-facing failure-reasoning comparator kept outside the deterministic core. | Reproduction of its VQA/failure-reasoning benchmark and adapter compatibility. | Safety truth, control authority, industrial field validity, or independent validation of Oscillink. Verify included-media provenance before redistribution. |
| **BridgeData V2** | CC BY 4.0; 60,096 WidowX trajectories across 24 environments and 13 skills.[33] | Episode/metadata reader and OOD split design; use a small upstream-referenced sample only. | General robot-manipulation schema and environment/task holdout behavior. | Safety-event coverage; most trajectories are demonstrations rather than failures. |
| **DROID** | Official docs expose 100-episode/2 GB, 1.7 TB RLDS, and larger raw variants, but the inspected dataset page and GitHub repository did not state a clear dataset license.[31] | **Metadata-only/monitor** until rights are clarified; downloader must require user acknowledgement and must not mirror. | Schema-scale feasibility if the user separately has rights. | Redistribution rights, safety labels, or failure coverage. |
| **RH20T** | 110,000+ real contact-rich sequences; huge downloads; human faces/voices caution. RH20T-C is CC BY-SA 4.0; RH20T-NC is non-commercial and bars commercial use/models trained on it.[32] | Low-dimensional force/torque/calibration adapter experiment on the commercial-compatible subset only after episode classification and rights review. | Multimodal synchronization/calibration stress and contact-rich schema compatibility. | Unrestricted commercial use, privacy-free redistribution, failure/safety labels, or industrial validation. |
| **Open X-Embodiment** | Repository software Apache-2.0; repository “other materials” CC BY 4.0; constituent datasets are catalogued separately.[34] | Cross-dataset metadata normalization experiment, not a bundled redistribution. | Portability across RLDS schemas where the selected source dataset's rights are verified. | A single blanket license for every upstream dataset, common failure semantics, or safety evaluation. |

**Preferred public benchmark data:** project-authored synthetic MCAP/JSONL fixtures for CI and the HF viewer; Zenodo DOI-pinned data only in opt-in download jobs. This gives small, reliable, redistributable defaults while still showing compatibility with real recordings.

## 6. Scenario design: hazard, fault, and intended-function limits

Use three separate scenario ledgers; do not collapse them into one “safety test” score.

### A. Evidence-governance scenarios

- changed bytes with unchanged filename/revision;
- changed revision with identical bytes;
- stale external review after parser/config/source changes;
- duplicate/dangling/self-referential/cyclic identities;
- incomplete manifest, unknown fields, path escape, symlink/special file, size/decompression bomb;
- unapproved candidate promotion attempt;
- ambiguity, unreadability, conflict, missing evidence, and unsupported interpretation;
- attempts to smuggle command, permit, token, callback, or authority fields; and
- deterministic output and input immutability under retries/concurrency.

### B. Operational and communications faults

- sensor stuck-at, drift, bias, chatter, saturation, NaN/Inf, frame/calibration mismatch;
- missing, duplicate, late, reordered, bursty, or out-of-order records;
- clock reset, leap, wrap, timezone error, and simulation/wall-time disagreement;
- TCP latency, packet loss, timeout, bandwidth limit, reset, half-close, partition;
- recorder loss, truncated MCAP, corrupt summary/index, unknown schema;
- process crash/restart, watchdog event, stale configuration, software/version mismatch; and
- simultaneous faults, with pairwise and selected three-way interactions.

### C. Intended-function/unknown-scenario concepts

ISO 21448 SOTIF addresses hazards from functional/specification/performance insufficiencies in series-production road-vehicle E/E functions where situational awareness is essential; it is not an industrial-machinery standard.[23] Borrow only its experimental discipline:

- define an operating domain and foreseeable misuse;
- separate known-safe, known-unsafe, and insufficiently characterized regions;
- search for triggering conditions and performance limits;
- preserve unknown/unsupported states; and
- expand the scenario catalog when new boundary cases appear.

Call this **“SOTIF-inspired scenario discovery,” not “SOTIF compliance.”**

Use STPA to author a project-level control-structure and loss-scenario worksheet. MIT's handbook explicitly covers purpose, control structures, unsafe control actions, scenarios, requirements/constraints, and workplace-safety applications.[24] The result is an authored hazard-analysis input and review checklist, not proof that the hazard analysis is complete.

## 7. Fault injection and adversarial testing program

### Layered campaign

| Layer | Method | Frozen budget for every PR | Scheduled/deeper budget | Passing evidence |
|---|---|---:|---:|---|
| Schema/domain | Curated adversarial examples | all | all | exact expected state/error code |
| Property-based | Hypothesis stateful/domain tests | fixed seed + derandomized profile; ≥200 examples/property | 5,000+ examples/property and seed archive | invariant holds; minimal counterexample retained |
| Parser fuzz | Atheris | corpus regression only | time-bounded campaign per parser | no uncaught crash, hang, unbounded allocation, or authority widening |
| API/schema | Schemathesis if an HTTP API is later added | not applicable now | bounded negative/stateful API suite | schema conformance and no unexpected 5xx |
| Network | Toxiproxy | small deterministic matrix | packet-loss/latency/partition grid | typed unavailable/partial result; no silent success |
| ROS log | Offline rosbag/MCAP mutation | small corpus | expanded message/topic matrix | typed failure/finding and preserved bytes |
| SIL | Gazebo/OpenPLC scenario | smoke fixture | full scenario matrix | frozen scenario-specific oracle only |

Hypothesis generates and shrinks edge cases and is MPL-2.0.[21] Atheris is Apache-2.0 coverage-guided Python fuzzing and supports Python 3.11 on Linux/macOS; keep it in a Linux scheduled job and commit minimized crash corpus only.[22] Schemathesis is MIT and uses generated/stateful property-based tests for OpenAPI/GraphQL; it is unnecessary until a real API exists.[45]

### Required invariants

- serialized output never contains `safe`, `compliant`, `certified`, `approved_to_operate`, control callbacks, or write credentials as an attainable state;
- unapproved candidates never enter approved memory;
- any relevant source/adapter/policy change deterministically stales every dependent review/result;
- missing/conflicting/ambiguous/unreadable evidence cannot become a pass through aggregation;
- normalized output always binds exact input, policy, adapter config, schema, and product versions;
- identical complete inputs yield identical bytes on repeated runs;
- source bytes are immutable; and
- invalid evaluator fixtures are classified invalid, not counted as product failures or successes.

Property/fuzz success increases tested input coverage; it does not prove the absence of defects.

## 8. Formal methods and model checking

### TLA+ as the first formal artifact

TLC is an MIT-licensed model checker for TLA+.[18] Model the smallest consequential state machine:

```text
Source = current | superseded | retracted | missing
Candidate = unreviewed | accepted | rejected | retracted
Review = current | stale
Finding = matched | missing | mismatch | stale | conflict | ambiguous | unreadable | unsupported | review
Authority = none
```

Check these invariants over bounded identities/revisions and every transition ordering:

1. `Authority = none` always;
2. accepted review is bound to exactly one candidate hash;
3. changed source, adapter config, policy, or candidate bytes imply stale review;
4. no stale/retracted review can authorize current memory;
5. conflict/ambiguity/missing/unreadable cannot auto-resolve;
6. supersession is acyclic and refers to included identities; and
7. every report binds the exact current packet/policy/input identity.

Publish the `.tla`, `.cfg`, state-count/diameter output, tool/JDK hashes, and a deliberately broken variant whose counterexample is documented. Apalache is an Apache-2.0 symbolic TLA+ checker for inductive invariants and bounded executions; use it later only if TLC state explosion is a measured problem.[19]

**Evidence limit:** model checking proves the stated properties of the abstract finite model under its assumptions. It does not prove the Python implementation refines the model, that the model captures all hazards, or that an operation is safe.

### CBMC for generated/native code, only when justified

CBMC uses bounded model checking for C/C++ assertions, bounds, pointers, and exceptions and is BSD-4-Clause.[20] It is useful only if a later OpenPLC/native adapter produces a small C seam with explicit assertions. Record unwind bounds and failed unwinding assertions.

**Evidence limit:** bounded properties of the inspected C program; not PLC compiler qualification, real-time behavior, hardware, whole-system safety, or unbounded proof.

### Refinement bridge

Make each TLA+ invariant appear as:

- a named model property;
- one or more deterministic Python tests;
- one property-based state-machine test; and
- one assurance-case evidence node linking model output, implementation test, and relevant schema.

This creates traceability without claiming formal verification of the entire implementation.

## 9. Reproducible benchmark

### Public package

Create `benchmarks/safetyops-bench-v1/` containing:

```text
MANIFEST.json                 exact files, byte counts, SHA-256, licenses
PROTOCOL.md                   frozen tasks, budgets, exclusions, invalid-run policy
SCENARIOS.jsonl               public inputs without hidden expected labels
public-oracles/               obvious conformance examples only
private-oracle-manifest.json  hashes/counts only; full hidden bank kept outside public subject path
baseline/                     trivial hash/diff + raw JSON import comparator
runner.py                     offline, seed/config explicit, machine-readable output
schema/                       benchmark result and finding schemas
environment/                  uv.lock, container digests, OS/arch/tool versions
```

Use scenario/bundle as the independent unit. Freeze task-family counts and success/kill criteria before running. Keep future hidden labels outside agent-readable/public inputs. A solo-authored hidden bank is leakage resistance, not independent evaluation; invite later external scoring without calling the current result independent.

### Metrics

Report a vector, never one safety score:

- exact expected-state match rate by scenario family;
- false-positive rate on clean/negative controls;
- abstention/`requires_authorized_review` correctness;
- stale-propagation completeness;
- exact-citation/source-identity completeness;
- mutation attempts rejected before unsafe parsing or authority widening;
- deterministic-byte match over 100 repeats per OS;
- cross-OS semantic match and byte match separately;
- p50/p95/max latency, peak RSS, and input-size scaling;
- MCAP/topic/schema coverage and explicitly unsupported fields;
- malformed/oversized/fuzz corpus count and crash/hang count;
- model-check states explored, depth/diameter, and invariant results; and
- baseline delta versus raw import and trivial hashing/diff.

Use bootstrap intervals over scenario bundles only when there are enough independent bundles; do not treat frames, messages, repeated seeds, or fault variants from one base recording as independent observations.

### Benchmark evidence limits

A benchmark result supports behavior on the frozen task bank, implementation, environment, and scoring protocol. It cannot support field prevalence, hazard completeness, practitioner utility, incident reduction, certification, or generalization to a site/asset not represented.

## 10. Hosted CI and public artifacts

### Required GitHub checks before simulator work

1. **Fast PR gate, Ubuntu + Windows:** locked install, schema/fixture drift, Ruff, format, strict mypy, unit/integration/property corpus, package build, wheel/sdist install smoke, deterministic repeated CLI output.
2. **Security gate:** CodeQL, dependency review, pinned action SHAs, least-privilege `GITHUB_TOKEN`, secret scan, license inventory, wheel-content inspection, forbidden control-import/authority-string scan.
3. **Formal gate:** TLC model check and implementation correspondence tests.
4. **Nightly/scheduled Linux:** Atheris budget, expanded Hypothesis profile, MCAP mutations, OpenPLC/Toxiproxy SIL, and Gazebo smoke/full split.
5. **Release gate:** build in hosted CI from a tag; verify isolated artifacts; generate hashes, SBOM, attestations, and release manifest; rerun install/demo from downloaded release artifacts.

### Publish these artifacts

- JUnit XML and coverage XML/HTML;
- `ruff`, `mypy`, schema-drift, and repository-surface logs;
- canonical benchmark result JSON plus Markdown summary;
- minimized fuzz corpus/crash reproducers (never silently delete failures);
- TLC/Apalache output and counterexample traces;
- Gazebo/OpenPLC scenario manifest and selected small project-owned recordings;
- wheel, sdist, `SHA256SUMS`, release manifest, and isolated-install transcript;
- CycloneDX SBOM; CycloneDX can represent components, dependencies, services, formulations, annotations, declarations, and citations.[40]
- signed GitHub artifact and SBOM attestations; GitHub documents creation and `gh attestation verify` for binaries/SBOMs.[37]
- OpenSSF Scorecard SARIF and badge, while stating that Scorecard checks are heuristics rather than definitive assurance.[41]

SLSA Build levels concern provenance and resistance to supply-chain tampering, not product safety.[38] GitHub likewise warns that artifact attestations link artifacts to source/build instructions but do not guarantee security. Reproducible builds require deterministic outputs, a recorded/predefined toolchain, and an independently recreatable environment.[39]

### Status badge language

Good:

- `CI: Ubuntu / Windows`
- `Benchmark: SafetyOps-Bench v1 (synthetic + simulation)`
- `Formal model: authority/staleness invariants checked`
- `Artifacts: SBOM + build provenance`
- `Validation: synthetic/SIL only; no field or certification claim`

Bad:

- `Safety verified`
- `SIL validated` (confusable with Safety Integrity Level)
- `Industrial grade`
- `Certified architecture`

Use **software-in-the-loop** in full; avoid the acronym “SIL” near functional-safety audiences unless the meaning is explicit.

## 11. Safety-case documentation without certification theatre

Create `assurance/` as a living, reviewable **assurance evidence case**, not a “certified safety case.”

```text
assurance/
  CLAIMS.md                    allowed and explicitly unsupported claims
  SYSTEM_BOUNDARY.md           no-control architecture and trust boundaries
  ASSUMPTIONS.md               environment, data, reviewer, and tool assumptions
  HAZARD_LOG.md                project/software hazards; status and owner
  STPA.md                      authored control structure and scenarios
  evidence-index.json          claim -> exact immutable artifact hashes
  limitations.md               simulator/data/external-validity limits
  change-impact.md             release-to-release affected claims/evidence
  gsn/                         source diagram plus generated SVG
  sacm/                        optional machine-readable interchange export
```

The GSN Working Group publishes GSN materials under CC BY 4.0 and warns users to rely on professional judgment.[25] OMG SACM 2.3 formally defines a metamodel and graphical notation for auditable claims, arguments, and evidence.[26] Use GSN for the human-readable argument and a minimal SACM-compatible export only after the internal claim/evidence model stabilizes.

Top claim should be narrow:

> “For release X, under the declared assumptions, the software preserves the specified read-only/no-authority and evidence-lineage invariants on the published verification suite.”

Explicit undeveloped/rebuttal nodes:

- no qualified practitioner review;
- no industrial partner/tester;
- no site/asset applicability evidence;
- no field behavior or incident outcome evidence;
- no functional-safety lifecycle/certification evidence;
- simulator and dataset representativeness unknown; and
- solo author/tester/common-toolchain dependence.

A complete-looking diagram is not sufficient evidence. Every evidence node must resolve to an exact release artifact, CI run, benchmark manifest, source revision, and hash.

## 12. Demo UX for GitHub and Hugging Face

### Recommended interface

Use a no-backend static viewer first:

1. **Choose a scenario:** Synthetic Press, ARIAC Cell Line, PLC Isolation Loop, Public Log Metadata.
2. **Inspect immutable inputs:** source class, rights, revision, asset/task, byte count, SHA-256, simulator/tool versions.
3. **Toggle a project-authored fault:** stale revision, missing verification, record loss, wrong serial, time jump, sensor freeze.
4. **Run deterministic audit locally in the browser** or select a precomputed signed result.
5. **See three synchronized panes:** event timeline; evidence/source graph; finding detail with exact citation and contributing states.
6. **Compare runs:** byte/config/revision diff and deterministic stale propagation.
7. **Export:** report JSON, manifest, and “What this run establishes / does not establish.”

Never present a chatbot prompt such as “Is this operation safe?” Do not color the whole run green/red. Use neutral evidence-state colors, persistent unresolved counters, and a permanent banner:

> Synthetic/simulation evidence only. No compliance, certification, safe-operation, field-validation, or work-authorization conclusion.

### Distribution

- **GitHub Pages:** canonical static demo, versioned to release artifacts.
- **Hugging Face Space:** mirror the static viewer. HF documents static HTML as free; Gradio/Docker compute creation requires a paid plan, with limited ZeroGPU exceptions, and default runtime storage is non-persistent.[35] A static Space avoids sleep, backend cost, uploads, secrets, and server-side processing.
- **HF Dataset:** `oscillink/safetyops-bench-v1`, containing only project-authored synthetic scenarios/results and small legally cleared derivatives. The dataset card should declare license, size, provenance, intended use, non-uses, generated/synthetic status, biases, limitations, checksums, and benchmark split logic; HF renders those fields from YAML/README dataset cards.[36]
- **HF Collection:** link Space, Dataset, GitHub repo, release, and technical report. Do not publish a token model merely to obtain a Model card.
- **Optional Gradio:** only if a paid/eligible runtime is justified. Run the same offline core, cap bytes, disable network/subprocesses, delete temporary files, and never accept confidential/customer uploads.

### First 90-second demo script

1. Open `synthetic_press_v2`; show all source hashes and fixed `operational_authority = none`.
2. Toggle “SOP revision changed”; rerun.
3. Highlight every dependent review/result that became stale and the exact changed hash.
4. Open ARIAC precomputed recording; show ROS/MCAP provenance and one missing/calibration or collision-related evidence event.
5. Download the report and reproduce its hash with one command.
6. End on the validation ladder, not a marketing claim.

This showcases the product's distinctive behavior—identity, applicability, lineage, conflicts, and staleness—rather than generic robot animation.

## 13. Isolated HIL strategy

### Low-cost bench

- one Raspberry Pi or x86 mini-PC running pinned OpenPLC Runtime v4;
- one inexpensive microcontroller/sensor node or dry-contact/LED loopback board;
- opto-isolated extra-low-voltage I/O only;
- network switch/USB serial capture;
- independent logic-analyzer or oscilloscope timestamps where possible;
- no mains, actuator, pressure, stored energy, machine, or safety circuit; and
- Safety Ops on a separate observer machine reading only copied, finalized logs.

### Frozen HIL scenarios

- cold boot and recovery;
- input chatter/stuck-at/disconnect;
- clock drift/reset;
- packet delay/loss/partition;
- power interruption during export;
- exporter crash/restart and partial-file rejection;
- firmware/config revision change with unchanged logical values; and
- 1,000 repeated loopback cycles with timing distribution and zero silent record substitution.

Publish exact BOM/serials, wiring diagram, photos, firmware and build hashes, calibration record, ambient conditions, run protocol, raw captures, invalid runs, and result bundle.

**Can establish:** compatibility and observed timing/recovery behavior on that isolated bench.  
**Cannot establish:** independent reproduction, industrial EMC/environmental robustness, electrical safety, machinery behavior, certified diagnostic coverage, Safety Integrity Level, Performance Level, or field reliability.

Do not run HIL in ordinary GitHub-hosted CI. A self-hosted runner attached to hardware widens supply-chain and physical risk; prefer manually dispatched, isolated collection with signed immutable outputs and no repository write token.

## 14. Staged GitHub/HF credibility plan

| Stage | Deliverables and public acceptance gates | Honest claim |
|---|---|---|
| **0 — Hosted baseline (now, 1–2 weeks)** | Clean publication scope; Ubuntu/Windows GitHub Actions; current 173 tests; repeated-byte check; wheel/sdist install smoke; coverage/JUnit; pinned actions; CodeQL/dependency review; release manifest. Do not add ROS yet. | “Hosted CI reproduces the deterministic core on two OS families.” |
| **1 — Reproducible alpha (2–4 weeks)** | Hypothesis invariants; bounded parser fuzz corpus; TLC authority/staleness model; CycloneDX SBOM; GitHub attestations; exact v0.1 alpha release; GSN claim/evidence skeleton; baseline comparator. | “Public release provenance and abstract/model + implementation evidence for named invariants.” |
| **2 — Public benchmark + static UX (4–7 weeks)** | SafetyOps-Bench v1; synthetic MCAP fault corpus; 100-repeat determinism results; GitHub Pages; HF static Space + Apache-2.0 synthetic Dataset card; downloadable evidence bundles. | “Reproducible results on a frozen project-authored benchmark.” |
| **3 — Industrial SIL adapters (7–12 weeks)** | ARIAC-generated closed MCAP and OpenPLC v4 JSONL fixture; Toxiproxy faults; nightly headless jobs; explicit third-party rights manifest; public-log opt-in adapter test. | “Compatibility and scenario behavior in named, pinned simulation/log environments.” |
| **4 — Isolated HIL (optional, 12–16 weeks)** | Extra-low-voltage loopback bench; frozen protocol; 1,000-cycle result; photos/wiring/calibration/raw captures; signed bundle. | “Observed behavior on one identified non-industrial isolated bench.” |
| **5 — External-readiness package** | Contributor reproduction kit; one-command verifier; issue template for external run bundles; public scoring protocol; examiner/practitioner review checklist; known-gaps ledger. | “Ready for independent reproduction; none claimed until a separate party completes it.” |
| **6 — Real validation/certification path (blocked)** | Qualified safety engineer, OT owner, legal/standards rights, exact target system, hazard/risk analysis, lifecycle plan, independent assessment, controlled configuration, test facilities, incident/change process. | Claims only as authorized by the resulting evidence and assessor. |

### Kill/defer criteria

- Defer Isaac Sim if no reproducible GPU budget or license-clean fixture output exists.
- Defer HIL if it would become a disguised control path or if independent timing instrumentation is unavailable.
- Reject Safety Gymnasium unless a separate safe-RL research question exists.
- Reject public mirroring of ARIAC/DROID or human-video data without verified rights/privacy treatment.
- Stop adding scenarios if the benchmark lacks frozen oracles, negative controls, or an invalid-run policy.
- Prefer a second independent implementation/reproduction of the verifier over a tenth visualization.

## 15. Build / Experiment / Monitor / Reject portfolio

### Build now

- hosted Ubuntu/Windows CI and release provenance;
- deterministic benchmark harness and project-authored synthetic MCAP corpus;
- Hypothesis state machine and bounded Atheris parser campaigns;
- TLC authority/staleness model with implementation traceability;
- static GitHub Pages/HF demo and rigorous Dataset card;
- living claim/evidence/limitation graph; and
- exact third-party rights/provenance manifest.

### Experiment next

- ARIAC closed-recording adapter;
- OpenPLC v4 synthetic isolation loop;
- RoHuCAD or placement-data on-demand compatibility test;
- differential Gazebo/MuJoCo/Webots run to expose simulator sensitivity; and
- isolated low-voltage HIL only after SIL semantics are stable.

### Monitor

- Isaac Sim/Isaac Lab license and hardware costs;
- DROID/Open X/RH20T component-level rights and privacy terms;
- NIST ARIAC repository licensing clarification;
- ROS/Gazebo supported release pairings;
- public external reproductions and bug reports; and
- eventual ISO 10218/IEC 61508/ISO 13849 applicability only with qualified experts and lawfully accessed standards.

### Reject as credibility theatre

- safety/compliance scores;
- simulator screenshots without manifests/results;
- generated “certificates”;
- unpinned `latest` containers;
- hidden failures or cherry-picked runs;
- calling a solo replay independent validation;
- treating formal notation as implementation proof;
- claiming real-world evidence from synthetic or public research data; and
- any live controller, permit, interlock, E-stop, robot, or actuator integration.

## Bottom line

A mature GitHub/HF project can be built without partners, but only at the **engineering-evidence** layers: deterministic contracts, adversarial tests, formalized invariants, reproducible artifacts, simulation/log compatibility, transparent limitations, and an examiner-friendly public demo. It cannot honestly cross the external-validity, field, practitioner, safety-rating, or certification layers alone.

The highest-return order is:

1. hosted CI and release provenance;
2. frozen benchmark + property/fuzz/model-check evidence;
3. static GitHub/HF evidence viewer;
4. one ARIAC MCAP fixture and one OpenPLC JSONL fixture;
5. optional isolated HIL; then
6. stop and seek qualified external validation before any stronger safety claim.

## Sources

[1] https://gazebosim.org/docs/latest/ros_installation — Gazebo: Installing Gazebo with ROS
[2] https://github.com/gazebosim/gz-sim — gazebosim/gz-sim
[3] https://www.openrobotics.org/blog/2024/5/ros-jazzy-jalisco-released — ROS 2 Jazzy Jalisco released
[4] https://github.com/ros2/rosbag2 — ros2/rosbag2
[5] http://docs.ros.org/en/rolling/Tutorials/Intermediate/Testing/Integration.html — ROS 2 launch_testing integration tests
[6] https://pages.nist.gov/ARIAC_docs/en/latest/pages/scenario.html — NIST ARIAC scenario
[7] https://github.com/usnistgov/ARIAC — usnistgov/ARIAC
[8] https://docs.isaacsim.omniverse.nvidia.com/6.0.0/common/license-faq.html — Isaac Sim 6.0 license FAQ
[9] https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html — Isaac Sim system requirements
[10] https://github.com/Autonomy-Logic/openplc-runtime — OpenPLC Runtime v4
[11] https://github.com/Autonomy-Logic/openplc-editor — OpenPLC Editor v4
[12] https://github.com/eclipse-4diac/4diac-forte — Eclipse 4diac FORTE
[13] https://codesys.com/the-system/licensing.html — CODESYS licensing
[14] https://github.com/renode/renode — Renode
[15] https://github.com/Shopify/toxiproxy — Toxiproxy
[16] https://github.com/boschresearch/rosbag-fault-injection — Bosch ROS 2 rosbag fault injection
[17] https://github.com/PKU-Alignment/safety-gymnasium — Safety Gymnasium
[18] https://github.com/tlaplus/tlaplus — TLA+ tools and TLC
[19] https://github.com/apalache-mc/apalache — Apalache model checker
[20] https://github.com/diffblue/cbmc — CBMC
[21] https://github.com/HypothesisWorks/hypothesis — Hypothesis
[22] https://github.com/google/atheris — Atheris
[23] https://www.iso.org/es/contents/data/standard/07/74/77490.html — ISO 21448:2022 catalogue
[24] https://psas.scripts.mit.edu/home/books-and-handbooks — MIT STPA handbook
[25] https://scsc.uk/gsn — SCSC Goal Structuring Notation
[26] https://www.omg.org/spec/SACM — OMG SACM 2.3
[27] https://zenodo.org/api/records/4578539 — Successful and failed placement robot dataset
[28] https://zenodo.org/api/records/12665499 — IMAD-DS
[29] https://zenodo.org/api/records/14142968 — RoHuCAD
[30] https://huggingface.co/datasets/MINT-SJTU/RoboFAC-dataset — RoboFAC dataset card
[31] https://droid-dataset.github.io/droid/the-droid-dataset — DROID dataset docs
[32] https://rh20t.github.io — RH20T dataset
[33] https://rail-berkeley.github.io/bridgedata — BridgeData V2
[34] https://github.com/google-deepmind/open_x_embodiment — Open X-Embodiment
[35] https://huggingface.co/docs/hub/main/en/spaces-overview — Hugging Face Spaces overview
[36] https://huggingface.co/docs/hub/main/datasets-cards — Hugging Face dataset cards
[37] https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations — GitHub artifact attestations
[38] https://slsa.dev/spec/v1.1/levels — SLSA v1.1 levels
[39] https://reproducible-builds.org — Reproducible Builds
[40] https://cyclonedx.org/specification/overview — CycloneDX specification
[41] https://github.com/ossf/scorecard — OpenSSF Scorecard
[42] https://github.com/huggingface/lerobot — Hugging Face LeRobot
[43] https://github.com/foxglove/mcap — MCAP
[44] https://github.com/Hebbian-Robotics/hflow — HFlow
[45] https://github.com/schemathesis/schemathesis — Schemathesis
[46] https://github.com/isaac-sim/IsaacLab — Isaac Lab
[47] https://github.com/polymathrobotics/replay_testing — Polymath ROS replay testing
[48] https://github.com/google-deepmind/mujoco — MuJoCo
[49] https://github.com/cyberbotics/webots — Webots
