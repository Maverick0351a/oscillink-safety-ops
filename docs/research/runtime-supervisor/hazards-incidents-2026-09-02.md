# Physical-intelligence safety evidence for an independent parallel supervisor

**Research cutoff:** 2026-09-02  
**Evidence policy:** Incidents are described only to the level established by the cited source. None of the OSHA, NIOSH FACE, or HSE incidents below is attributed to AI; their sources establish robot/automation, sensor, control, safeguarding, maintenance, communication, or human-action failures. AI-specific evidence is separated from conventional automation evidence.

## Executive conclusion

The strongest evidence for Oscillink is not a verified epidemic of “AI-caused robot accidents.” It is a recurring control pattern across conventional automated equipment: a person is physically inside or near a hazard; a sensor, reset, command, or control fault initiates motion; the production controller behaves consistently with its own inputs; and the observed physical situation is unsafe. Recent AI governance and research add three reasons this pattern becomes harder: deployment data can drift from training data, adaptive behavior can change during operation, and cyber compromise can corrupt both control and safety if they share components or networks.

A defensible product thesis is therefore **independent observation plus bounded authority**: observe command, controller mode, physical motion, human presence, sensor health, and safety-channel state through sufficiently independent paths; compare expected and observed state; and invoke a hardwired, fail-to-known-state inhibit when invariants are violated. Do not present the supervisor as safety-rated until its sensing, logic, final element, independence, diagnostic coverage, response time, and lifecycle evidence meet the applicable machinery/functional-safety regime.

## A. Verified incidents and surveillance

| Date | Verified claim and short exact quote | Failure-mode relevance | Caveat | Product implication / test |
|---|---|---|---|---|
| 2024-12-02 | An 18-year-old was inside a robotic enclosure cleaning a sensor. Entry sensors had stopped the robot, but “a coworker reset the machine from the control panel, unaware that Employee #1 was still inside the enclosure.” The arm activated and killed him.[1] | Restart/recovery; mode/occupancy mismatch; human proximity; single-person knowledge failure. | OSHA accident abstract, not a full causal investigation. It does **not** identify AI. | A reset must not clear an occupied-zone latch. Test remote/local reset while an independently sensed person remains inside; inhibit until zone-clear is independently proved and a deliberate restart sequence completes. |
| 2022-11-29 | During lubrication inside an energized palletizer cell, the worker “unknowingly activated the photo eye,” which commanded the arm into motion and killed him.[2] | Command-versus-world mismatch; perception semantics; maintenance with energy present. | OSHA abstract; photo-eye logic and LOTO exposure are established, not AI causation. | Inject human/tool occlusions and maintenance artifacts into production sensors. Supervisor should distinguish “product-ready” from “person/tool present,” or conservatively inhibit when semantics are ambiguous. |
| 2020-08-16 | While a worker unstuck a pallet and adjusted sensors, “The sensors were activated causing the robot to begin its cycle. The robot grabbed the employee and pulled him to the floor attempting to complete its cycle.”[3] | Sensor-triggered unexpected motion; human proximity; production goal continuing despite abnormal physical state. | OSHA abstract; no evidence of AI. | Test sensor restoration, alignment, cleaning, and stuck-part recovery with a human in the envelope. Require independent occupancy veto and abnormal-force/motion trip. |
| 2020-02-20 | A worker entered a gated press area to free stuck parts; “a coworker (press operator) reset the machine faults causing the robotic plate-unloader (shuttle) to move and strike the employee.”[4] | Fault reset, communication failure, restart from unknown state. | OSHA abstract; no evidence of AI. | Fault-clear must be separate from motion-enable. Preserve person/door/lock state across reset and power cycle; test stale operator assumptions and simultaneous actions at different HMIs. |
| 1999-06-08 | A worker’s foot broke a light beam; a roughly 300-pound computer-controlled platform descended 10–15 ft and killed him. FACE states that power remained to “the light sensors and the robotic platform” because the entire system was not locked out.[5] | Partial isolation; latent energized subsystems; sensor false semantics. | FACE report describes a computer-controlled platform, not AI. The worker was observing maintenance, not performing it. | Build an energy-and-authority inventory spanning conveyors, sensors, platform, PLC, and final elements. Test partial LOTO and hidden powered branches; the supervisor must not infer safety from one stopped subsystem. |
| 1984-07-21 | A die-cast operator entered a robot envelope and was pinned. “The robot stalled when it contacted the man’s body and continued to apply pressure on the chest area.” NIOSH’s training warning was: “If the robot is stopped, don’t assume that it will remain stopped.”[6] | Unexpected motion; dangerous sustained force after stall; stopped-versus-safe confusion. | Historical conventional robot; entry and guarding failures were central. Not AI. | Monitor torque/current/contact duration independently and trip on sustained abnormal load, not only velocity. Treat stopped, stalled, paused, and de-energized as distinct states. |
| 2011-11-02 safety alert (fatal incident predates alert) | HSE found an exposed conductor intermittently contacted the chassis; “This fault caused a voltage change that acted as a signal” to a track valve, producing unintended track movement and a fatal trapping during maintenance.[7] | Command-versus-observed mismatch caused below software; degraded wiring; unintended motion. | Mobile crusher, not an AI robot. HSE says risk may exist in similar control systems. | The supervisor needs physical-motion sensing and final-element feedback independent of command telemetry. Test electrical faults that mimic valid commands; software-only monitoring on the same signal path can miss them. |
| 2025-08 safety notice | A slinger was fatally crushed after the excavator operator inadvertently contacted a joystick while leaning out to communicate; “The safety control lever had not been applied to isolate the machine.”[8] | Human proximity; inadvertent command; mode/isolation confusion. | Excavator, not autonomous or AI. Event date is not given on the notice. | Test inadvertent input while a person is in the swept volume. Human-presence veto should dominate ordinary motion commands; proximity communication must not depend only on operator memory. |
| 1992–2017 data, paper accepted 2023-02-17 | NIOSH identified 41 U.S. occupational robot-related fatalities; “Most of the cases involved stationary robots (83%) and robots striking the decedents while operating under their own power (78%).” Many strikes occurred during maintenance.[10] | Establishes burden and maintenance concentration; supports prioritizing powered intervention states. | Keyword search of restricted CFOI research files; counts can miss cases and are not an exposure-adjusted rate. “Robot-related” does not mean robot- or AI-caused. | Make maintenance, setup, teaching, cleaning, jam-clearing, and recovery first-class operating modes in the safety model, not edge cases. |
| 2001–2020 data, paper accepted 2026-02-17 | Ohio workers’ compensation analysis found 1,076 robot-related claims; 57.9% involved contact with objects/equipment, 75.1% were in manufacturing, and 91% of cost came from lost-time claims.[11] | Empirical injury distribution supports contact, caught-between, and abnormal interaction tests. | One state, keyword-screened claims, no exposure denominator; 54.8% lacked cage-status information and 32.7% lacked power-status information. The study’s “collaborative” coding must not be read as proof that each system was a certified cobot. | Event capture must retain robot model, power/mode, guarding, command, occupancy, sensor health, and time-synchronized physical telemetry—fields often absent from injury narratives. |

### Incident pattern

The incident evidence repeatedly shows a **semantic gap**: the ordinary controller had an input that permitted or requested motion, while the physically relevant fact was that a person was exposed. In several cases the command path was internally “correct” (photo eye, reset, joystick, voltage interpreted as valve command). A parallel supervisor is useful only if it observes information not defeated by the same mistaken semantics or component fault.

## B. AI/autonomy-specific failure evidence

| Date/source | Verified finding and exact quote | Caveat | Product implication / test |
|---|---|---|---|
| 2019-11-19 NTSB report on 2018-03-18 Tempe crash | The developmental automated driving system detected the pedestrian 5.6 s before impact but “never accurately classified her as a pedestrian or predicted her path.” NTSB also found inadequate safety risk assessment and ineffective oversight.[12] | Road-vehicle testing, not industrial production. NTSB’s probable cause included the distracted safety operator and pedestrian behavior; this is not a general robot failure rate. | Use as a perception/oversight test archetype: detection without correct classification must not equal safety. Test unusual pose, carried object, partial occlusion, low contrast, route boundary, and late reclassification. An independent occupancy envelope should not require the same semantic class as the primary AI. |
| 2020 laboratory HRC paper | The authors state pure vision is insufficient in some cases and propose tactile supervision because vision “can fail due to occlusion effects.” Their classifier explicitly includes a `Fail` state when cameras cannot detect the person due to occlusion.[13] | Structured lab, fixed cameras, stationary Franka Panda, intentional contacts and no high-speed data; the combined network was a research proposal, not a certified safety function. | Sensor degradation must become an explicit safety state. Test self-occlusion, tools/workpieces blocking people, camera freeze, stale frames, lighting, multi-person scenes, and clock desynchronization. Default to reduced energy or inhibit, not continued nominal speed. |
| 2025-10-24 preprint survey | Moving autonomous systems from closed to open worlds requires detecting “novel inputs, unexpected situations and uncertainty.” The paper states safety guarantees cannot be assumed outside the operational design domain and calls for runtime monitoring and logging of requirement violations.[14] | Preprint review, not an incident study or proof that a particular OOD detector is adequate. OOD detectors themselves have false positives/negatives and distribution assumptions. | Monitor ODD assumptions separately from the production model. Test site/time/device/lighting/tooling/worker-clothing holdouts; unknown-person pose; unseen object; sensor aging; latency; cyber-altered inputs. An OOD alert should trigger a defined safe policy, not merely a dashboard warning. |
| 2026 Nature Communications study | The authors define inoperability as behavior induced by a command not following operator expectations: “unexpected perturbations can cause vehicles to exhibit behaviours that deviate from the originally designed behaviours.” Their FLAIR method adapts an onboard model every 225 ms.[15] | Author-reported experiments on tracked mobile robots and perturbations; not a safety-rated industrial deployment. The paper demonstrates adaptation as recovery, not an actual harmful incident. | Directly motivates command/response residuals: compare commanded velocity/turning with independent pose/velocity. If online adaptation is allowed, bound outputs with invariant limits, version/log updates, detect oscillation or regression, and require safe rollback. Never let the adapting controller modify the supervisor’s limits. |
| 2023 NIST AI RMF | NIST notes training data can change “significantly and unexpectedly,” affecting trustworthiness. It recommends “real-time monitoring, and the ability to shut down, modify, or have human intervention into systems that deviate from intended or expected functionality.”[16] | Voluntary, non-sector-specific framework; not a machinery functional-safety standard or certification basis. | Preserve a separate runtime assurance layer that measures deviation from expected function and has an enforceable stop/inhibit path. Use AI RMF for governance evidence, not as a substitute for safety integrity engineering. |
| 2024 NIOSH-affiliated systematic review | Of 50 human-participant AMR studies, “Almost all of the reported experiments were conducted in a controlled laboratory setting”; only two used commercially available industrial mobile robots.[22] | Review is mostly perceived safety/trust, not collision injury incidence; studies through August 2022. | Treat claimed HRI comfort/safety behaviors as low external-validity evidence until field-tested. Validate multi-robot traffic, real workers, noise, clutter, forklifts, PPE, blind intersections, shift fatigue, and atypical pedestrian behavior. |

## C. Conventional robot guidance that maps directly to supervisor requirements

Oregon OSHA’s industrial-robot technical manual was updated with the federal OSHA revision in January 2023. It identifies “Unpredicted or unexpected movements, component malfunctions, or unexpected program changes” as contact hazards; notes that an IMR can drive into a worker; and states that sensor/circuit malfunctions create additional hazards.[9] It also identifies several concrete mode and control problems:

- A robot program may call another program with different velocity, acceleration, deceleration, or position parameters, “not be expected by workers.”[9]
- A common direction misunderstanding is that a worker commands left but the robot moves right because the robot pose/frame differs from the worker’s perspective.[9]
- Time pressure during restart can cause safety functions, startup steps, and other workers’ positions to be overlooked.[9]
- A cleaned photobeam can cause a system in automatic mode to resume and strike the service worker.[9]
- Safety settings should be periodically checked; the manual specifically mentions checking safety-parameter checksums to detect change.[9]

**Implication:** model not just `RUN/STOP`, but at least automatic, manual/teach, maintenance, protective stop, emergency stop, faulted, reset-pending, recovery, unknown, and degraded-sensing states. The supervisor should verify coordinate frame, selected program/task, velocity/force envelope, guarding/occupancy, and parameter integrity before motion permission.

## D. Cybersecurity common-cause and independence

NIST SP 800-82 Rev. 3 (September 2023) provides the strongest architecture-level support for a genuinely parallel safety path:

> “While these systems are traditionally implemented to be fully redundant and independent from the primary OT, some architectures combine control and safety functions, components, or networks. Combining control and safety could allow a sophisticated attacker access to both control and safety systems if the OT were compromised.”[17]

NIST says a safety instrumented system is often independent so failure of the basic process control system does not deleteriously affect it, and notes that physical rather than merely logical separation may be required.[17] It also warns that unauthorized physical or wireless access to sensors/final elements enables direct process manipulation, and that remote-command authentication matters because unauthorized commands can cause “injury, death, property damage” and other severe consequences.[17]

NIST SP 1800-10 (March 2022) adds manufacturing-specific threat evidence: once malicious actors gain access, they can compromise data/system integrity, damage ICS machinery, or cause physical injury; its demonstrated scenarios include detecting unauthorized PLC-logic modification and continuously monitoring network and asset behavior.[17]

**Caveat:** NIST OT publications are cybersecurity guidance and reference architectures, not proof of Oscillink’s safety integrity. Independence is a system property, not a marketing label. Shared cameras, time source, network switch, cloud identity, OS image, update channel, model supplier, or safety PLC can create common-cause failure.

**Required tests:**

1. Compromise or spoof the production command topic while physical state remains nominal, and vice versa.
2. Corrupt primary perception while independent occupancy sensing remains correct.
3. Partition network/time synchronization; replay stale frames and validly signed stale commands.
4. Alter PLC/robot program, safety parameters, calibration, model weights, and coordinate transforms; require integrity detection and a safe response.
5. Disable the production controller and supervisor simultaneously through each shared dependency; document residual common-cause paths.
6. Verify the inhibit final element under cyber isolation, loss of comms, brownout, reboot, and partial recovery.

## E. Restart, recovery, and safe-state requirements

The EU Machinery Regulation dated 2023-06-14 requires machinery restart after any stoppage to follow voluntary actuation unless automatic restart cannot create a hazard. It also states that disengaging an emergency stop “shall not restart the machinery ... but only permit restarting,” and that communication/power restoration must not cause unexpected start or uncontrolled parameter change.[19]

NIST SP 800-82 says OT recovery should “prioritize human safety and environmental safety prior to restarting the OT operation,” and calls for backup of system state, configurations, and programs to support recovery to a stable state.[17]

**Supervisor behavior:**

- Latch trips across PLC, robot, supervisor, and network reboot.
- Separate fault acknowledgment, reset, motion enable, and production resume.
- Re-establish trusted position, tool/workpiece state, guarded-space occupancy, mode, selected task, sensor health, safety-parameter hash, and communications freshness before movement.
- Permit only bounded recovery motion with independent occupancy veto.
- Require deliberate local authorization where the risk assessment demands it; remote software handshakes alone must not silently resume.
- Record why the trip occurred and preserve pre/post-event telemetry before state mutation or model update.

## F. Emerging governance requirements

### EU Machinery Regulation 2023/1230

The regulation explicitly addresses learning machinery. It says safety components with self-evolving behavior have risk factors including “data dependency, opacity, autonomy and connectivity,” which may increase probability/severity of harm and therefore require third-party conformity assessment in the specified cases.[19] Annex III is especially aligned with a supervisor:

- safety-critical software/data must be protected from accidental or intentional corruption, and intervention/modification evidence collected;
- faults or errors in control-system hardware/logic must not create hazards;
- safety limits established by risk assessment must not be modified during a learning phase when hazardous;
- systems with self-evolving logic must not act beyond defined task/movement space;
- safety-related decision data must be recorded; and
- “it shall be possible at all times to correct the machinery ... in order to maintain its inherent safety.”[19]

**Caveat:** legal applicability, transition dates, harmonized standards, conformity route, and any later amendments must be confirmed for the actual product and market. The regulation does not itself certify an independent supervisor.

### EU AI Act 2024/1689

An AI system is high-risk under Article 6(1) only when both conditions hold: it is a safety component (or product) covered by Annex I harmonization law, and the relevant product requires third-party conformity assessment.[20] For applicable high-risk systems, Article 14 requires effective human oversight able to monitor “anomalies, dysfunctions and unexpected performance,” override/reverse output, and interrupt operation through a stop procedure that reaches a safe state.[20] Article 15 requires lifecycle robustness, allows redundancy/fail-safe plans, and requires mitigation of feedback-loop risks for systems that continue learning.[20] Article 72 requires systematic lifetime post-market performance collection/analysis; Article 73 requires serious-incident reporting after a causal link or reasonable likelihood is established, with shorter deadlines for death and widespread incidents.[20]

**Caveats:** not every robot with AI is automatically “high-risk”; applicability is conditional. The Act’s human-oversight language does not prove that a human alone is an adequate fast safety channel. This report quotes the official 2024 act; deployment counsel should verify effective dates and subsequent amendments at launch.

### EU-OSHA human-factors warning

EU-OSHA’s 2022 review treats advanced robotics as a source of both physical-safety benefits and new organizational risks. It identifies possible negative effects including “job insecurity and fear of job loss, peer pressure, loss of competencies or autonomy” and argues workers should be consulted early.[21] This is not incident-rate evidence, but it matters to supervisor design: opaque or nuisance-prone interventions can induce distrust, workarounds, alarm fatigue, and bypass pressure. Product evaluation should therefore measure legibility, override governance, workload, false-trip burden, and worker participation—not only collision metrics.

## G. Prioritized supervisor acceptance tests

| Priority | Hazard injection | Required safe outcome | Evidence basis |
|---|---|---|---|
| P0 | Person remains in enclosure while another station issues reset | No motion; latched occupied state; explicit local reset sequence | OSHA 2024 fatality.[1] |
| P0 | Human/tool breaks or restores product photo eye during maintenance | Production sensor cannot authorize hazardous motion; independent occupancy veto | OSHA 2022/2020 and NIOSH 1999.[2][3][5] |
| P0 | Electrical ground fault produces a valid-looking motion signal | Detect actual motion without valid trusted command; inhibit final element | HSE crusher fatality.[7] |
| P0 | Robot stalls against a person/object and continues torque | Trip on sustained force/current/zero-velocity mismatch; release strategy avoids secondary harm | NIOSH 1984.[6] |
| P0 | Primary PLC/AI, supervisor, and safety interface are attacked through shared dependencies | Demonstrate independence, safe-state transition, and bounded common-cause exposure | NIST SP 800-82.[17] |
| P0 | E-stop/protective stop, brownout, network restoration, controller reboot | No automatic hazardous restart; revalidate state; deliberate restart only | EU Machinery Regulation; NIST OT recovery.[17][19] |
| P1 | Person unusual pose/partial occlusion/carrying workpiece; detector sees object but misclassifies | Conservative occupancy envelope remains active; uncertainty produces slowdown/inhibit | NTSB; mixed-perception study.[12][13] |
| P1 | Camera frozen/stale, lidar dropout, dirty lens, lighting/noise degradation, clock skew | Declare degraded sensing; reduce energy/inhibit within response budget | Oregon OSHA; mixed perception; NIST IR 8604.[9][13][18] |
| P1 | Wrong frame, mirrored direction, unexpected subprogram, mode switch, teach/auto handoff | Detect command/envelope inconsistency; mode visible and unambiguous; bounded motion | Oregon OSHA; EU Machinery Regulation.[9][19] |
| P1 | OOD scene or plant reconfiguration | Detect ODD-assumption violation; log it; execute predeclared safe policy | OOD review; NIST AI RMF.[14][16] |
| P1 | Online learner changes policy, oscillates, or improves nominal tracking while violating a limit | Hard invariant remains immutable; adaptation logged/versioned; rollback and inhibit work | FLAIR study; EU Machinery Regulation/AI Act.[15][19][20] |
| P2 | Multi-robot aisle intersection, blind corner, forklift and pedestrian, real PPE/noise/clutter | No collision; intention signaling is legible, but safety does not depend solely on human interpretation | NIOSH AMR review.[22] |

## H. Build / experiment / monitor / reject

**Build now**

- Independent command-versus-motion residuals using motor current/torque, joint/axis position, external pose/velocity, and final-element feedback.
- Independently derived human/occupied-zone detection with explicit sensor-health and stale-data states.
- A deterministic safety kernel with immutable task/movement/force/speed/energy limits and a tested fail-to-known-state inhibit.
- A latched restart/recovery state machine that distinguishes acknowledgment, reset, recovery, and resume.
- Tamper-evident, time-synchronized logs of command, mode, selected program/model, sensor health, physical state, supervisor decision, and inhibit outcome.
- Common-cause analysis covering power, compute, network, time, sensors, software supply chain, updates, and final elements.

**Experiment before product claims**

- Hardware-in-loop fault injection for sensor semantics, wire faults, stuck actuators, stale telemetry, wrong frames, latency, and partial power/network recovery.
- Field trials stratified by site, shift, worker experience, PPE/clothing, layout, robot model, and process state—not random frame splits.
- Measured trip latency and stopping distance under worst payload, speed, tool, floor, and environmental conditions.
- False-negative/false-positive and availability tradeoffs at the system level, including whether nuisance trips create bypass pressure.

**Monitor**

- Applicable ISO/ANSI/A3 machinery and mobile-robot standards, harmonized EU standards, AI Act implementation/amendments, and safety-component conformity routes.
- Incident taxonomies and regulator reporting fields for mode, power, guarding, model/version, sensor health, and reset/recovery.
- Independent evidence for OOD monitors and learned perception under real industrial distribution shifts.

**Reject**

- Claims that conventional robot incidents were caused by AI without source evidence.
- A “parallel” supervisor that shares the same perception model, network path, credentials, update channel, or actuation authority without documented common-cause controls.
- Confidence score alone as a safety signal; softmax confidence is not proof that the scene is in-distribution or safe.
- Automatic “go home” or production restart from an unknown physical state.
- Online adaptation that can alter safety limits, disable the supervisor, or erase the evidence needed to reconstruct an event.

## Bottom line

The evidence supports Oscillink as a **runtime assurance and risk-reduction layer** if it is engineered around independent physical observation, explicit degraded/unknown states, immutable safety envelopes, fail-safe inhibit authority, secure separation, and conservative recovery. The incident record establishes the hazards; it does not yet establish that an AI supervisor reduces them. That reduction must be demonstrated with fault injection, hardware-in-loop testing, field holdouts, stopping-performance measurements, common-cause analysis, and an auditable safety case.

## Sources

[1] https://osha.gov/ords/imis/accidentsearch.accident_detail?id=172270.015 — OSHA Accident 172270.015
[2] https://osha.gov/ords/imis/accidentsearch.accident_detail?id=151758.015 — OSHA Accident 151758.015
[3] https://www.osha.gov/ords/imis/accidentsearch.accident_detail?id=129040.015 — OSHA Accident 129040.015
[4] https://osha.gov/ords/imis/accidentsearch.accident_detail?id=124448.015 — OSHA Accident 124448.015
[5] https://cdc.gov/niosh/face/stateface/ne/99ne017.html — NIOSH FACE 99NE017
[6] https://cdc.gov/niosh/face/In-house/full8420.html — NIOSH FACE 84-20
[7] https://www.hse.gov.uk/safetybulletins/mobilecrushingplant.htm — HSE Mobile crushing plant unintended movement
[8] https://www.hse.gov.uk/safetybulletins/excavators-safety-control-lever-isolation-devices.htm — HSE Excavators isolation safety notice
[9] https://osha.oregon.gov/OSHARules/technical-manual/Section4-Chapter4.pdf — Oregon OSHA Industrial Robots and Robot System Safety
[10] https://stacks.cdc.gov/view/cdc/230667/cdc_230667_DS1.pdf — NIOSH Robot-related fatalities 1992-2017
[11] https://stacks.cdc.gov/view/cdc/258698/cdc_258698_DS1.pdf — NIOSH Robot-Related Workers Compensation Claims Ohio 2001-2020
[12] https://www.ntsb.gov/investigations/AccidentReports/Reports/HAR1903.pdf — NTSB Tempe automated driving crash report
[13] https://pmc.ncbi.nlm.nih.gov/articles/PMC7664417 — Mixed-Perception Approach for Safe HRC
[14] https://arxiv.org/pdf/2510.21254v1 — OOD Detection for Safety Assurance of AI and Autonomous Systems
[15] https://nature.com/articles/s41467-026-70256-y.pdf — FLAIR online adaptation for immediate recovery
[16] https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf — NIST AI RMF 1.0
[17] https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf — NIST SP 800-82 Rev. 3
[18] https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=960050 — NIST IR 8604 Improved Robotic Workcell
[19] https://eur-lex.europa.eu/eli/reg/2023/1230/oj/eng — EU Machinery Regulation 2023/1230
[20] https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A32024R1689 — EU Artificial Intelligence Act 2024/1689
[21] https://osha.europa.eu/en/publications/summary-advanced-robotics-and-automation-implications-occupational-safety-and-health — EU-OSHA Advanced robotics and automation OSH summary
[22] https://stacks.cdc.gov/view/cdc/155558/cdc_155558_DS1.pdf — NIOSH review of safety and trust with industrial AMRs
