# Independent runtime safety for autonomous robots and AI-controlled machinery

**Market/competitor map — research cutoff 2026-09-02**

## Scope and evidence rules

This map separates: (1) certified or safety-rated controllers/sensors that implement bounded machine-safety functions; (2) commercial autonomy-assurance, runtime-monitoring, and V&V products; and (3) research/standards architectures for Runtime Assurance (RTA), Simplex, safety cages, and runtime verification.

**Evidence labels:** **OFFICIAL-CERT** = certificate/declaration or manufacturer document explicitly stating certification/type approval; **VENDOR-RATING** = live manufacturer page states SIL/PL/ASIL, but the independent certificate was not separately inspected; **LIVE-PRODUCT** = current product/documentation page or request-information page; **EA** = early access/preview/alpha; **TOOL-QUALIFIED** = development tool qualification, not a runtime safety function; **PAPER** = peer-reviewed publication/official research record; **PREPRINT** = author claim, not independent validation; **INFERENCE** = synthesis from the cited evidence.

A component's SIL/PL/ASIL rating or certificate does **not** certify the finished machine or complete safety function. Integration, sensors, actuators, fault assumptions, response time, validation, proof testing, and application architecture remain system-level responsibilities. Oscillink Safety Ops currently makes **no safety rating, certification, conformity, or permission-to-operate claim**.

## Executive finding

The market is split across a conspicuous seam:

1. **Certified machine-safety vendors** can reliably evaluate hardwired/safe-network inputs and execute configured stop, safe-motion, or restart-inhibit functions, but their public materials do not show semantic observation of an AI planner's requested action and intent.
2. **Autonomy V&V and safety-case vendors** connect hazards, requirements, tests, telemetry, and evidence, but usually do not own an independent production stop path.
3. **RTA research** explicitly wraps an untrusted advanced controller with an independent monitor and trusted fallback, but most implementations remain papers, open frameworks, simulation/lab prototypes, or aviation-specific systems.
4. **NVIDIA Halos Outside-In Safety** is the closest current architecture-level competitor: independent camera-stream health monitoring, safety-event fusion, a decision maker, black-box/UI components, and actionable control signals. Its current public release is EA and says some features remain alpha and should not be used in production.[16][17][18]
5. **Veo FreeMove/Symbotic** is the strongest evidenced certified physical-state analogue: independently sensed 3D workcell state plus autonomous restriction/resumption of robot motion, certified by TÜV Rheinland to ISO 13849 PL d, Category 3. Its availability appears tied to Symbotic after the 2024 asset acquisition rather than a broad independent platform sale.[12]

**Product opening:** a vendor-neutral, production-AI supervisor that observes both **what the AI is asking the machine to do** and **what the physical system is independently observed to be doing**, explains allow/inhibit/degrade/stop recommendations to a safety manager, and hands any safety-rated final action to an established certified controller. No reviewed incumbent clearly demonstrates that complete combination as a generally available, certified industrial product. This is an **evidence-backed gap hypothesis**, not proof of unmet demand.

---

## 1. Certified/safety-rated PLCs, controllers, sensors, and stop-path products

| Vendor / product | Commercial status and dated evidence | Safety evidence | Observes | Can stop/inhibit? | Short primary-source quote | Caveat for Oscillink |
|---|---|---|---|---|---|---|
| **Siemens SIMATIC S7-1500 F ecosystem** | **LIVE-PRODUCT**; live catalog accessed 2026-09-02 | **VENDOR-RATING** for reviewed F-DI module: up to PL e / SIL 3 | Configured safe digital inputs via PROFIsafe | **Yes, when engineered as a complete safety function** through fail-safe controller/I/O/actuator chain | “up to PL E (ISO 13849-1)/ SIL 3 (IEC 61508)”[1] | The reviewed source is an F input module page, not a certificate for an entire AI-supervision system. Strong integration/installed-base target, not evidence of AI-command semantics. |
| **Pilz PNOZmulti 2** | **LIVE-PRODUCT**; UL announcement 2024-11-14 | **OFFICIAL-CERT claim in manufacturer announcement**: UL listing as Programmable Safety Controller; page also states up to PL e / SIL 3 depending on application | E-stop, guard, position/motion and configured safe inputs | **Yes**: safety-related shutdown, controlled stopping, restart prevention | “received UL listing in the ‘Programmable Safety Controllers’ category.”[2] | Good partner for bounded stop/inhibit output. Configuration remains application-specific and protected from production AI. |
| **Rockwell GuardLogix 5580 + safety partner** | **LIVE-PRODUCT**; installation instructions July 2025 | **OFFICIAL-CERT** in manufacturer instructions: SIL 3 IEC 61508; PLe Cat. 4 EN ISO 13849-1 with safety partner | Safety I/O, machine state, motion and configured logic | **Yes** | “Type-approved and certified for use in safety applications up to and including SIL 3 per IEC 61508.”[3] | Strong North American integration target. A primary controller alone is lower-rated; the complete safety function must be validated. |
| **SICK Flexi Soft** | **LIVE-PRODUCT**; data sheet 2026-05-07 | **VENDOR-RATING**: SIL 3, Cat. 4, PL e | Safe sensors, analog/motion values, safe network signals | **Yes** through safe outputs; reviewed I/O module advertises 8 ms fast shut-off | “Safety integrity level SIL 3 … Performance level PL e”[4] | Controller + broad sensor portfolio makes SICK a partner and an adjacent platform threat. No public evidence reviewed of semantic AI-plan inspection. |
| **SICK microScan3** | **LIVE-PRODUCT**; live page accessed 2026-09-02 | **VENDOR-RATING**: Type 3, PL d, SIL 2/SILCL2 | Independent 2D protective fields; detailed measurement/diagnostic data | **Yes**, via OSSD or safe network to controller | “Safety level Type 3, PL d, SIL2, SILCL2”[5] | Valuable independent physical-state input, but it detects field intrusion rather than whether an AI command is contextually valid. |
| **ABB Pluto Safety PLC** | **LIVE-PRODUCT**; EU declaration revision 2022 | **OFFICIAL-CERT**: EC type-examination certificate 01/205/5304.02/22; notified body TÜV Rheinland | Configured machinery-safety inputs, safe bus, encoder/motion signals | **Yes** | “Programmable electronic safety system, Safety PLC system Pluto”[6] | Useful independent stop controller. Certification scope is named Pluto versions, not arbitrary external AI logic. |
| **ABB SafeMove** | **LIVE-PRODUCT**; live page accessed 2026-09-02 | **VENDOR SAFETY CLAIM**; a separate certificate was not validated in this pass | Robot position/speed and virtual zones; commonly paired with external laser scanners | **Yes**: page explicitly describes stopping before collision | “the robot will stop before the collision happens.”[7] | Strong integrated safe-motion substitute, but ABB-robot-centric and not an independent AI-command observer. |
| **KEYENCE GC-1000** | **LIVE-PRODUCT**; live model page accessed 2026-09-02 | **VENDOR-RATING**: IEC 61508 SIL3, IEC 62061 SILCL3, ISO/EN 13849-1 Cat. 4 PL e, UL1998 | Safety devices and configured start/stop conditions | **Yes**, through six safety outputs | “IEC 61508 … SIL3 … Cat. 4, PL e”[8] | Compact integration target; certificate not separately inspected. |
| **Beckhoff TwinSAFE EL6930** | **LIVE-PRODUCT**, “regular delivery”; accessed 2026-09-02 | **VENDOR-RATING**: Cat. 4 PL e; SIL 3; certified function blocks | Safe Boolean inputs; TwinSAFE/FSoE/PROFIsafe | **Yes**, generates safe output signals; use drive STO/SS1 modules for actuation | “a dedicated safety controller” with “certified function blocks”[9] | Attractive EtherCAT/FSoE partner for robot cells. Public page shows predefined safe logic, not semantic command analysis. |
| **FORT Robotics Endpoint Controller** | **LIVE-PRODUCT**; exida certificate rev. 1.4, 2025-04-28; surveillance due 2028-05-01 | **OFFICIAL-CERT**: IEC 61508 SC3 / SIL 3 capable component | Wireless/wired emergency-stop requests and endpoint status | **Yes**: transmitter/controller or receiver that acts on E-stop requests | “receives and acts on emergency stop requests.”[10] | Strong partner for independent remote/fleet stop edge. Certificate explicitly requires PFH and architecture verification for the complete SIF. |
| **Inxpect LBK safety radar** | **LIVE-PRODUCT**; accessed 2026-09-02 | **VENDOR-RATING**: SIL 2, PL d; independent certificate not inspected here | Volumetric operator access/presence, including adverse optical conditions | **Yes**: secure signal can slow/stop and prevent restart | “a secure signal that can slow down or stop the machine.”[11] | Good complementary physical-state sensor where cameras/lidar are weak. It is not an AI-command monitor. |
| **Veo FreeMove, now Symbotic assets** | Acquisition announced 2024-08-09; evidence of active Symbotic safety-team work exists, but broad standalone availability was not established | **OFFICIAL-CERT claim**: TÜV Rheinland ISO 13849 PL d, Cat. 3 | External 3D sensors estimate human/object future position in robot workcells | **Yes**: autonomously restricts or resumes motion | “monitor … workcells … and autonomously restrict or resume motion”[12] | Closest certified physical-state product. Commercial/channel scope after acquisition is a material caveat. |

### Certified software substrates, not independent safety supervisors

| Product | Evidence | What it provides | What it does **not** establish |
|---|---|---|---|
| **QNX OS/Hypervisor for Safety** | **VENDOR-CERT**; live robotics page says IEC 61508 SIL 3.[13] | Deterministic, partitioned, safety-certified runtime substrate | No evidence on the reviewed page of semantic AI-command observation or an independent sensor-to-stop safety application. |
| **Apex.Grace** | **VENDOR-CERT**; live page states ISO 26262 ASIL D.[14] | Safety-certified ROS 2-compatible application runtime/SDK | Certification is automotive and as a software platform/component; it is not a complete industrial robot safety function. |
| **TTTech/TrustMotion MotionWise** | Manufacturer says latest functional-safety assessment is ISO 26262 ASIL D.[15] | Deterministic mixed-criticality scheduling, health management, error handling | Automotive platform; no reviewed evidence of independent external physical sensing or generic industrial stop authority. |

**Bottom line:** do not build a new PLC, safe I/O family, laser scanner, radar, or E-stop transport. These are mature, certified, application-engineered layers. Build a narrow independent supervisor and partner into them.

---

## 2. Commercial autonomous-system assurance, runtime monitoring, and V&V

| Vendor/system | Availability / evidence label | Runtime role | Monitor only or stop/inhibit? | Safety-certification status found | Short quote and implication |
|---|---|---|---|---|---|
| **NVIDIA Halos Outside-In Safety Blueprint 1.3 EA** | **EA**, current docs accessed 2026-09-02 | External AI perception, sensor-health monitor, perception-container monitor, event fusion, deployment-specific decision maker, black box, UI, SIL/HIL harness | **Can emit actionable control signals**; reference logic can slow/stop or inhibit/enable a safety function | **No certificate for the complete blueprint found**; release notes say EA, some alpha, not for production | “Some features remain in an alpha state and should not be used in production.”[16] SAIM “independently observes the same camera streams”[17]; SDM “produces actionable control signals.”[18] **Closest architectural competitor.** |
| **Edge Case Research Guardian / DevSafeOps** | **LIVE COMMERCIAL/SERVICES** | Connects vehicle data, hazards, V&V, safety indicators and continuous safety case/operations intelligence | **Monitoring/decision support in reviewed materials**; no public production stop interface established | No product safety-function certificate found | “real-time safety and operational intelligence layer”[19] Strong safety-manager/evidence competitor; likely partner or data interchange target, not stop-path supplier. |
| **Foretellix Foretify** | **LIVE COMMERCIAL** | Coverage-driven V&V, real/simulated scenarios, ODD/KPI coverage, safety-case evidence, post-deployment field-data feedback | **No direct production stop authority shown** | No runtime safety-function certification found | “combines real-world test drives and virtual simulation”[20] Strong pre-deployment and continuous-validation competitor, not an independent controller. |
| **ResilienX FRAIHMWORK / AAM OptiX** | **LIVE COMMERCIAL**, aviation/UAS deployments claimed | System-of-systems health/integrity/performance monitoring, off-nominal detection, mitigation workflows, operational evidence | **Triggers mitigations**, but reviewed material does not prove direct actuator/E-stop control | No product safety certificate found in reviewed sources | “detects off nominal conditions, triggers mitigations”[21] Closest commercial RTA analogue, but aviation-specific and primarily data-layer/in-time assurance. |
| **Saphira** | **LIVE COMMERCIAL STARTUP** | Failure analysis, assurance graph, requirements, validation plans, change impact | **Evidence/engineering layer**, not runtime enforcement in reviewed page | No safety-function certificate found | “turn risks into traceable requirements and validation plans.”[22] Direct UX/evidence competitor; not a stop-path product. |
| **Fennec ASAP** | **LIVE COMMERCIAL** | Functional-safety system of record plus automated physical test cells | **Offline development/test**, not production runtime control | **TOOL-QUALIFIED**: specified tools TÜV Rheinland T2 under IEC 61508-3; this is not SIL/PL certification of a safety function | “Tool Class 2 (T2) offline support tools”[23] Important certification-readiness partner/competitor; do not conflate T2 with runtime safety rating. |
| **General Autonomy** | **LIVE COMMERCIAL STARTUP** | AI-assisted hazard analysis, scenario generation, digital-twin V&V, coverage and safety cases | **Offline/pre-deployment decision support** | No safety-function certificate found | “Every output is structured, traceable, and reviewed by your engineers.”[24] Competes on AI safety-engineering workflow, not independent physical-state monitoring. |
| **Applied Intuition Basis/Test Suites** | Public product URLs: https://www.applied.co/products/basis and https://www.applied.co/products/test-suites | Requirements/tests, SIL/HIL/VIL/test-track workflows and evidence | **Pre-deployment V&V**; no direct production stop authority established in this pass | No safety-function certificate established | The Basis page was initially fetch-blocked, then not re-collected after user requested synthesis. Treat as adjacent with lower evidence confidence in this report. |

**Category caveat:** “safety case,” “continuous assurance,” “standards-aligned,” “certification-ready,” or a qualified development tool does not mean the deployed software performs a certified safety function.

---

## 3. RTA, Simplex, safety-cage, and runtime-verification architectures

| Architecture / date | Evidence label | Core mechanism | Monitor vs intervention | Commercial/certified status | Short quote / caveat |
|---|---|---|---|---|---|
| **Simplex architecture — 1998** | **PAPER**, IEEE Control Systems, DOI 10.1109/37.710880 | Unverified advanced controller + simple trusted safety controller + decision/switching module | **Intervenes by switching** to trusted controller | Architecture, not a product or certificate | “fundamental properties … guaranteed by the ‘simple’ components.”[25] Requires a valid recoverable region, trustworthy state, sufficient switching horizon, and verified fallback. |
| **NASA Verification Framework for RTA of Autonomous UAS — acquired 2024-06-24; DASC 2024** | **OFFICIAL RESEARCH/PAPER** | Formalizes Simplex RTA; monitor checks property and switches from advanced to reversionary controller | **Switches control** | Research/verification framework, not commercial certification | “an internal monitor acts upon detecting a violation”[26] Sensor sample rate and recovery assumptions are safety-critical. |
| **ASTM F3269-21 — updated 2021-11-19** | **ACTIVE STANDARD** | Architectural practice for safely bounding complex aircraft functions using RTA | Defines monitor/recovery architecture | Standard practice, **not** certification of an implementation | Active RTA standard record.[27] Aviation scope; components still require assurance commensurate with safety assessment. |
| **SOTER — submitted 2018-08-23, revised 2019-04-19; DSN 2019** | **PAPER** | Declarative composition of uncertified advanced controller, trusted safe controller and safety specification | **Controller switching/fallback** | Research prototype; drone case study, no product certification | “advanced … controller (uncertified), a safe … controller (certified)”[28] The framework claim depends on well-formed modules and trusted safe controller. |
| **ReSonAte — submitted/revised 2021-02-18/2021-03-24** | **PAPER/PREPRINT RECORD** | Runtime risk estimation from Bow-Tie diagrams, system/environment state and failure distributions | **Monitors/estimates risk**; mitigation must be supplied by surrounding system | Research; simulations including CARLA/UUV | “dynamic risk estimation framework”[29] Useful for safety-manager risk context, but probabilistic risk is not a deterministic stop guarantee. |
| **Monitoring ROS2 / FRET→Ogma→Copilot — 2022-09-28** | **PAPER/PREPRINT** | Structured requirements compile to hard-real-time C99 ROS 2 monitor nodes | **Publishes violations**; action is external | Research toolchain, no certification claim found | Monitors “publish the results of any violations.”[30] Good command/state monitor generator; not a complete independent stop system. |
| **RTAMT for CPS/robotics — 2025-01-22** | **PAPER/OPEN TOOL** | Quantitative Signal Temporal Logic runtime monitors; ROS 2 and Simulink integrations | Primarily **monitor**; can feed a recovery mechanism | Research/open library; no safety certification found | “quantitative monitoring of Signal Temporal Logic”[31] Valuable component, but dynamic language/runtime and monitor correctness need separate assurance. |
| **Connected Dependability Cage — submitted 2026-04-30** | **PREPRINT** | Heterogeneous perception voting + anomaly monitor + independent perception path | **Graceful degradation/minimal-risk maneuver** | Author reports vehicle testing; no independent validation or certificate established | “two complementary monitoring mechanisms”[32] Strong architectural analogue for physical-state diversity, automotive rather than industrial machinery. |
| **ROSClaw — submitted 2026-03-27** | **PREPRINT** | Model-agnostic executive layer interposes validation/logging between foundation models and ROS 2 actions | **Blocks invalid actions before execution** | Research infrastructure on three robot types; no safety certification | “pre-execution action validation within a configurable safety envelope”[33] Closest evidence for AI-command observation, but the envelope and executor remain within the robot software stack unless separately isolated. |
| **MaCoPlanner — submitted 2026-08-28** | **PREPRINT** | Compiles manuals to typed constraints; symbolically rolls out plans before actuation | **Rejects unresolved plans** | Controller-panel simulator, no attached industrial load, explicitly no deployment-readiness claim | “Before actuation … checked … unresolved plans are rejected.”[34] Strong component evidence for semantic/procedural command checks, not runtime certified control. |
| **Mission-Level RTA for LLM-assisted swarms — submitted 2026-07-26** | **PREPRINT** | Compositional platform/squad/mission monitors with provenance and explicit unknown on missing evidence | **Monitoring/verdicts** in presented work; intervention not established | Simulated ISR mission, no certification | “unsupported negative verdicts are downgraded to an explicit unknown”[35] Useful for fleet-wide command/policy observation and fail-unknown UX. |

### What these architectures teach

A credible supervisor needs all of the following, not just an anomaly score:

- an independently trusted state estimate;
- explicit safety properties and operational modes;
- a proven or conservatively validated intervention horizon;
- an allowed-command/filter/switch policy;
- a fallback or final stop path that does not depend on the production AI;
- health monitoring of the monitor, sensors, timing and communications;
- fail-safe/fail-unknown behavior when evidence is stale, missing or contradictory; and
- immutable records sufficient to reconstruct why a command was allowed, inhibited, degraded or stopped.

---

## 4. Competitive whitespace for Oscillink Safety Ops

### Defensible differentiation to test

1. **AI-command observation at the cognition→actuation boundary.** Parse and normalize task plans, tool calls, motion goals, mode changes, setpoints and requested safety-function changes before they reach the control stack. Evaluate deterministic limits plus reviewed procedural constraints. Log both the original command and transformed/inhibited result.
2. **Independent physical-state observation.** Use sensors not controlled or reconfigured by production AI—safety scanners/radar, external cameras, encoders, safety PLC state, zone occupancy, energy/isolation state, controller health—and compare requested action with observed reality.
3. **Two-channel reasoning, one conservative decision.** Distinguish command-policy mismatch, physical-state hazard, state/command disagreement, sensor-health failure and insufficient evidence. Unknown/stale inputs must not become “safe.”
4. **Safety-manager UX rather than an engineering log viewer.** Present hazard/rule → input provenance → command → physical evidence → decision → intervention → acknowledgement → change/review lineage. Include replay, false-trip burden, proof-test/calibration due dates, degraded-mode inventory, and signed policy/configuration revisions.
5. **Independence and non-reconfigurability.** Separate compute, credentials, configuration store and network boundary; production AI gets no write path to rules, sensor calibration, stop logic, identities, clocks or evidence retention. Treat production telemetry as untrusted input.
6. **Vendor-neutral bridge.** Normalize ROS 2, PLC, drive, AMR/fleet, camera/radar and autonomy logs, while leaving the certified final safety function with Siemens/Pilz/Rockwell/SICK/ABB/KEYENCE/Beckhoff/FORT or another established supplier.
7. **Evidence portability.** Export a time-synchronized evidence packet for integrator/assessor review without claiming the packet proves compliance or certification.

### Where not to differentiate

- generic camera PPE/near-miss analytics;
- a new safety PLC, scanner, radar or E-stop transport;
- generic HARA/FMEA/safety-case authoring;
- broad simulation/V&V infrastructure;
- “AI watches AI” anomaly scores without deterministic authority boundaries; or
- certification language before a defined product configuration, safety manual, lifecycle process and third-party assessment exist.

---

## 5. Build / Partner / Integrate recommendation

### BUILD — Oscillink-owned differentiation

1. **Independent command-observation gateway** with read-only/transparent taps first, then a tightly bounded one-way inhibit interface. Support command identity, issuer/model/version, asset/task/mode, requested parameters, deadline and expected physical effect.
2. **Deterministic safety-policy engine** for allow / inhibit / clamp / degrade / request-human / stop-request decisions. Learned models may propose findings, but cannot silently change policy, thresholds or authority.
3. **Independent state correlator** that time-aligns external sensor/PLC/drive observations with commands and checks freshness, disagreement and intervention horizon.
4. **Supervisor health and tamper boundary:** watchdogs, signed configuration, secure boot/attestation where practical, immutable event chain, fail-unknown behavior, clock/source provenance, and no production-AI administration channel.
5. **Safety-manager console and evidence packet:** explain each decision, show source health and uncertainty, support review/correction/retraction, configuration-change impact, proof-test workflow and incident replay.
6. **Fixture-first assurance program:** one robot cell, one bounded hazard set, hardware-in-loop stop-timing tests, seeded sensor/clock/network/command faults, independent red-team review, and explicit non-rated positioning.

### PARTNER — do not recreate mature certified infrastructure

- **Safety controller/stop edge:** Pilz PNOZmulti/PSS 4000, Rockwell GuardLogix, Beckhoff TwinSAFE, Siemens SIMATIC Safety, ABB Pluto/SafeMove, KEYENCE GC, SICK Flexi, or FORT EPC according to customer stack.
- **Independent physical sensing:** SICK/KEYENCE laser scanners, Inxpect radar, existing safety encoders/interlocks/light curtains, and where commercially accessible, certified 3D safeguarding such as FreeMove.
- **Functional-safety integrator/assessor:** define the safety requirements specification, allocation, response-time budget, independence argument, validation plan and certification roadmap. Oscillink should not self-declare rating scope.
- **Certified runtime substrate if a future rated version is justified:** QNX, Apex.Grace, or comparable partitioned platform; this is a later certification program, not an MVP prerequisite.

### INTEGRATE — narrow, versioned adapters

- **Read status/telemetry:** OPC UA, EtherNet/IP/CIP objects, EtherCAT/FSoE diagnostics, PROFINET/PROFIsafe diagnostics, ROS 2/MCAP, drive state, fleet-manager and V&V exports. A non-certified adapter must not be represented as a safe protocol endpoint.
- **One-way intervention:** initially send a non-safety inhibit/stop request to an existing validated controller and keep the certified protective function independent. If customers later allocate safety integrity to Oscillink inputs/logic, treat that as a new certified product/configuration with a complete safety lifecycle.
- **Evidence/V&V ecosystem:** export to Edge Case, Foretellix, Applied Intuition, Fennec, Saphira, Jira/ALM/QMS, rather than duplicating their authoring/test-management surfaces.
- **NVIDIA Halos:** support ingestion of its safety events/black-box output where customers deploy it, while preserving an independent Oscillink command-observation and governance plane. Compete on vendor neutrality, command semantics, hardened independence and safety-manager operations UX.

### Recommended first product boundary

**Phase 1 — supplemental independent risk-reduction layer, no rating claim:** observe AI commands and physical state; generate deterministic findings and a one-way inhibit/stop request; existing certified controls remain authoritative. Production AI cannot configure or disable the supervisor.

**Phase 2 — validated operational supervisor:** on-prem appliance, bounded adapters, deterministic policy packs, HIL-tested latency/fault coverage, integrator-reviewed evidence, and pilot deployments on one cell/AMR zone. Still no SIL/PL claim unless assessed.

**Phase 3 — certification decision gate:** pursue certification only after a stable configuration, repeated paid deployment, fixed safety-function allocation, measurable demand for rated authority, and assessor agreement on scope. Certification likely requires freezing hardware/software variants, lifecycle processes, safety manual, diagnostic coverage, systematic-capability evidence, cybersecurity controls and proof-test assumptions.

### Commercial thesis and kill test

Lead with **“independent production-AI supervision that correlates requested action with independently observed machine state”**, not “living safety case” or “AI safety analytics.” Sell one bounded cell/zone and one change/incident workflow to the safety/validation manager and controls integrator.

Kill or reposition if existing safety PLC logic plus a conventional scanner/radar and a small deterministic command whitelist produces equivalent detection, response time, reviewer clarity and evidence at materially lower lifecycle cost.

---

## 6. Priority competitive threats

1. **NVIDIA Halos Outside-In** — closest end-to-end architecture; monitor release maturity and certification evidence.
2. **Certified safeguarding incumbents expanding upward** — SICK, Pilz, Siemens, Rockwell, Beckhoff, ABB and KEYENCE can add richer analytics/UX around an installed safe-control base.
3. **Veo/FreeMove inside Symbotic** — strongest certified 3D physical-state precedent; watch whether it re-emerges as a broadly sold platform.
4. **Edge Case Guardian / ResilienX** — closest operational-assurance/evidence products; monitor industrial/robotics expansion and actuator authority.
5. **Fennec/Saphira/General Autonomy/Foretellix/Applied Intuition** — can own certification workflow and safety-manager relationships even without runtime control.
6. **Open RTA/ROS toolchains** — ROSClaw, SOTER, Copilot/Ogma and RTAMT lower the cost of basic command gating and monitoring; moat must be hardened independence, adapters, operations UX, validation evidence and partner distribution.

## Sources

[1] https://mall.industry.siemens.com/mall/en/WW/Catalog/Product/6ES7526-1BH00-0AB0 — Product Details - Industry Mall
    > "SIMATIC S7-1500, F digital input module, F-DI 16x 24 V DC PROFIsafe; 35 mm width; up to PL E (ISO 13849-1)/ SIL 3 (IEC 61508)"
[2] https://www.pilz.com/en-US/company/news/articles/243516 — UL certification for the safe small controller PNOZmulti 2 from Pilz
    > "the configurable safety controller PNOZmulti 2 has received UL listing in the “Programmable Safety Controllers” category."
[3] https://literature.rockwellautomation.com/idc/groups/literature/documents/in/1756-in048_-en-p.pdf — GuardLogix 5580 Controllers Installation Instructions
    > "Type-approved and certified for use in safety applications up to and including SIL 3 per IEC 61508."
[4] https://www.sick.com/media/pdf/8/78/478/dataSheet_FX3-CPU130002_1043784_en.pdf — Flexi Soft FX3-CPU130002, Data sheet
    > "Safety integrity level SIL 3 (IEC 61508) Category Category 4 (EN ISO 13849) Performance level PL e (EN ISO 13849)"
[5] https://www.sick.com/ag/en/products/safety/safety-laser-scanners/microscan3/c/g295657 — SICK | Sensor Intelligence
    > "Safety levelType 3, PL d, SIL2, SILCL2"
[6] https://library.e.abb.com/public/123011dc75114efe94fdb93940bff4b3/Declaration_of_Conformity_Pluto_%28EN%29_2022_revB.pdf — Declaration of Conformity
    > "Programmable electronic safety system, Safety PLC system Pluto version A20, B20, S20, D20, B22, D45, B46, S46, AS-i, B42 AS-i, O2"
[7] https://www.abb.com/global/en/areas/robotics/products/controllers/safemove — SafeMove | ABB
    > "SafeMove safeguards operators by replacing physical barriers like fences with virtual barriers such as laser scanners that ensure that a moving robot will never collide with a human because the robot will stop before the collision happens."
[8] https://www.keyence.com/products/safety/safety-controller/gc/models/gc-1000 — Main controller Standard type - GC-1000
    > "IEC 61508, EN 61508 SIL3 IEC62061 SIL CL3 ISO/EN13849-1:2015 Cat. 4, PL e, UL1998"
[9] https://www.beckhoff.com/en-us/products/automation/twinsafe/twinsafe-hardware/el6930.html — EtherCAT Terminal communication interface, TwinSAFE Logic
    > "The EL6930 TwinSAFE component is a dedicated safety controller."
[10] https://www.exida.com/2025/FRT_22-10-010_C002_V1R3_Certificate_EPC_SIL3.pdf — 61508 Cert Template
    > "An EPC handles emergency stop requests - based on how it is configured by the customer (using FORT Manager), can act as a transmitter/controller (i.e., reads and transmits emergency stop requests) or as a receiver (i.e., receives and acts on emergency stop requests)."
[11] https://inxpect.com/en/products/lbk-system — LBK Sytem | Inxpect
    > "providing a secure signal that can slow down or stop the machine."
[12] https://ir.symbotic.com/news-releases/news-release-details/symbotic-acquires-veo-robotics-enhance-efficiency-and-safety — Symbotic Acquires Veo Robotics to Enhance Efficiency and Safety Innovation | Symbotic Inc.
    > "The FreeMove system’s patented sensors and software monitor collaborative robot workcells to dynamically anticipate the future position of humans and objects within the robot’s environment and autonomously restrict or resume motion"
[13] https://qnx.software/en/industries/robotics — Robotics Systems Software | QNX
    > "The QNX OS for Safety and QNX Hypervisor for Safety are certified to IEC 61508 SIL 3."
[14] https://www.apex.ai/apexgrace — Apex.Grace
    > "Certified to ISO 26262 ASIL D, the highest automotive safety level."
[15] https://www.trustmotion.com/newsroom/motionwise-completes-functional-safety-assessment — MotionWise completes functional safety assessment
    > "The latest functional safety assessment, according to ISO 26262 ASIL D, supports MotionWise and proves that the safety life cycle has been completed."
[16] https://docs.nvidia.com/halos-outside-in/latest/release-notes.html — NVIDIA Halos Outside-In Safety Blueprint
    > "This early access (EA) release builds on 1.2.1 and includes major safety-path, perception-trust, event-ingestion, packaging, and deployment updates."
[17] https://docs.nvidia.com/halos-outside-in/latest/integration/components/ai-monitor.html — Safety AI Monitor (SAIM) — NVIDIA Halos Outside-In Safety Blueprint
    > "It independently observes the same camera streams consumed by the perception pipeline (SIPP) and reports per-sensor trust verdicts to SEI"
[18] https://docs.nvidia.com/halos-outside-in/latest/integration/components/decision-maker.html — Safety Decision Maker (SDM) — NVIDIA Halos Outside-In Safety Blueprint
    > "SDM receives safety events identified and fused by SEI, then produces actionable control signals."
[19] https://www.ecr.ai/pwc-1-1-7 — Data-Driven Safety Tools & Operations | DevSafeOps | Edge Case
    > "Guardian serves as a real-time safety and operational intelligence layer within the Torc ecosystem."
[20] https://foretellix.com/technology — Technology - Foretellix
    > "Foretify provides a unified V&V flow that combines real-world test drives and virtual simulation in one platform."
[21] https://resilienx.com — Home - ResilienX
    > "FRAIHMWORK monitors health, integrity, and performance, detects off nominal conditions, triggers mitigations, and manages maintenance workflows."
[22] https://www.saphira.ai — AI agents for engineering complex physical systems
    > "Investigate failures, reason across system evidence, and turn risks into traceable requirements and validation plans."
[23] https://fennec-engineering.com/solutions/platform — ASAP is the System of Record for Functional Safety
    > "Fennec's specified ASAP tools are qualified by TÜV Rheinland as Tool Class 2 (T2) offline support tools under IEC 61508-3:2010, Clause 7.4.4."
[24] https://genauto.ai — General Autonomy — AI-Powered Safety Engineering for Autonomous Systems
    > "Every output is structured, traceable, and reviewed by your engineers."
[25] https://doi.org/10.1109/37.710880 — Dynamic control system upgrade using the Simplex architecture
    > "The fundamental properties of the combined system are guaranteed by the "simple" components."
[26] https://ntrs.nasa.gov/citations/20240007986 — A Verification Framework for Runtime Assurance of Autonomous UAS
    > "Runtime Assurance (RTA) is a design-time architecture for safety-critical systems where an internal monitor acts upon detecting a violation of a property."
[27] https://store.astm.org/f3269-21.html — Standard Practice for Methods to Safely Bound Behavior of Aircraft Systems Containing Complex Functions Using Run-Time Assurance
    > "StandardActiveLast Updated: Nov 19, 2021"
[28] https://arxiv.org/abs/1808.07921 — SOTER: A Runtime Assurance Framework for Programming Safe Robotics Systems
    > "SOTER provides language primitives to declaratively construct a RTA module consisting of an advanced, high-performance controller (uncertified), a safe, lower-performance controller (certified), and the desired safety specification."
[29] https://arxiv.org/abs/2102.09419 — ReSonAte: A Runtime Risk Assessment Framework for Autonomous Systems
    > "We introduce the ReSonAte dynamic risk estimation framework for autonomous systems."
[30] https://arxiv.org/abs/2209.14030 — Monitoring ROS2: from Requirements to Autonomous Robots
    > "publish the results of any violations."
[31] https://arxiv.org/abs/2501.18608 — RTAMT – Runtime Robustness Monitors with Application to CPS and Robotics
    > "we present Real-Time Analog Monitoring Tool (RTAMT), a tool for quantitative monitoring of Signal Temporal Logic (STL) specifications."
[32] https://arxiv.org/abs/2604.27728 — Connected Dependability Cage: Run-Time Function and Anomaly Monitoring for the Development and Operation of Safe Automated Vehicles
    > "This framework integrates two complementary monitoring mechanisms: a Function Monitor that oversees multiple heterogeneous AI-based perception pipelines and detects inconsistencies through a voting mechanism, and an Anomaly Monitor that evaluates the reliability of AI perception by detecting unknown or novel objects in scenes that may be excluded from the training dataset."
[33] https://arxiv.org/abs/2603.26997 — ROSClaw: An OpenClaw ROS 2 Framework for Agentic Robot Control and Interaction
    > "pre-execution action validation within a configurable safety envelope"
[34] https://arxiv.org/abs/2608.28300 — MaCoPlanner: LLM-Assisted Manual-Compiled Task Planning with Proactive Safety Verification for Robotic Industrial Panel Operation
    > "Before actuation, candidate plans are symbolically rolled out and checked against procedural and state-transition constraints; detected violations are localized and returned for targeted repair, while unresolved plans are rejected."
[35] https://arxiv.org/abs/2607.23532 — Mission-Level Runtime Assurance for LLM-Assisted ISR Swarms over a Verification-Aware Fabric
    > "unsupported negative verdicts are downgraded to an explicit unknown rather than reported as mission-wide all-clears."
