# Community voice-of-user: safety around automated and AI-controlled industrial equipment

**Research cutoff:** 2026-09-02  
**Scope:** PLCtalk, Robot-Forum, Control.com, Eng-Tips, ROS Discourse, GitHub issues, and Reddit r/PLC.  
**Interpretation rule:** these are practitioner reports and discussions, not authoritative standards guidance. Anonymous claims are evidence of perceptions, workarounds, and operational pressure—not proof that a design is compliant or that an incident occurred as described.

## Executive findings

1. **The most repeated pain is not “we need another stop.” It is poor diagnosis and recovery after a stop.** Operators and technicians struggle to identify the exact device, channel, zone, stale command, communication layer, or state-machine condition preventing restart. That uncertainty turns every minute of downtime into pressure to reset, force, jumper, raise a limit, or power-cycle.[3][7][20]
2. **Separation is an operational boundary as much as a technical one.** Practitioners repeatedly distinguish the rated safety chain from the standard PLC/HMI/ROS layer. The standard layer may observe, explain, coordinate process shutdown, or suggest recovery, but should not silently become part of the essential safety function.[1][14][15]
3. **Bypasses become dangerous when they are informal, invisible, ownerless, or permanent.** Threads contain key switches, permits, muting, standstill monitoring, maintenance modes, software forces, shared passwords, and crude environmental shields. The counterexamples are controlled, time-limited, risk-assessed modes with reduced functionality and conspicuous indication—not “never any bypass under any condition.”[2][4][6]
4. **Nuisance trips are often system-level symptoms.** Reported causes include EMC/grounding, environmental light, mechanical contact timing, dirt/wear, transient power loss, incompatible safety-network roles, stale UI commands, and configuration misuse. Simply increasing a threshold or suppressing an alarm can erase evidence and increase risk.[4][7][11]
5. **Reset, rearm, start, and recover are frequently conflated.** Users want fewer button presses and less pendant work, but community responses repeatedly separate clearing the condition, rearming the rated system, restoring controller/driver state, and issuing a fresh start command.[3][5][20]
6. **Safe-speed/separation behavior creates a productivity/safety tension that must be explained.** A robot that stops when a reduced-speed zone becomes active above its limit is behaving as a monitor should; users experience it as a nuisance when the ordinary controller failed to decelerate in advance. The practical need is predictive coordination without weakening immediate enforcement.[6][16]
7. **Open robotics/AI stacks are treated as useful supervisory logic, not a substitute for certified safety.** ROS practitioners describe parallel isolated safety systems and call Nav2 collision monitoring “safety-like.” GitHub evidence also shows that malformed or stale sensor/control state can affect monitor availability or recovery.[15][16][21]
8. **Production pressure is a control-system hazard amplifier.** The strongest accounts describe repeated limit increases, forced bits, disabled E-stops, and permanent bypass requests. Safety PLCs improve diagnostics and change control, but do not eliminate physical jumpering or a “get it working now” culture.[2][11][23]

## Strongest directly verified voices

| Date | Community | Pain / short verbatim quote | What the thread adds | Verification |
|---|---|---|---|---|
| 2020-07-08 | PLCtalk | “connect the switch to the nearest PLC which would transmit the status to the Safety PLC along with a watchdog bit”[1] | Shows pressure to bridge non-safe and safe layers for convenience; poster also planned risk assessment and independent verification. | Direct body; date from indexed metadata. |
| 2017-03-29 | PLCtalk | “A couple of bits forced in the CPU … I'd be called day or night to move it and keep production.”[2] | Sensor failure plus logistics/production pressure drives forcing; counterexamples used permits, unique keys, reduced motion, and application-specific risk assessment. | Direct body; date from forum index/search metadata. |
| 2023-03-23 | PLCtalk | “if is reset safety, the action executes.”[3] | A stale HMI command survives the trip; replies recommend fixing PLC edge/state logic rather than hiding a button. | Direct body; date from indexed metadata. |
| 2024-04-03 | PLCtalk | “it was the amber beacon on the forkloift causing the trip”[4] | Environmental change created unexpected optical interference; a cardboard shield intended as temporary remained for two years. | Direct body; date from indexed metadata. |
| 2013-12-07 | Robot-Forum | “avoid picking up the TP and creating more downtime and work than what is needed.”[5] | User asks for a bypass; experienced replies preserve the door interlock and redesign recovery through PLC/UOP instead. | Direct body; date from indexed metadata. |
| 2021-11-18 | Robot-Forum | “not have to reset the whole system in each entry.”[6] | Frequent human entry motivates standstill/muting; replies require safety-rated confirmation, presence protection, and risk assessment. | Direct body; date from Robot-Forum index metadata. |
| 2020-05-06 | Robot-Forum | “dual channel safety error quite often, resetting the safety removes error.”[7] | Maintainer-style explanation points to channel discrepancy time, slow mechanical actuation, alignment, dirt, wear, and sensor type. | Direct body; date from Robot-Forum index metadata. |
| 2019-12-03 | Robot-Forum | “no documentation on either side of someone connecting one of these before.”[8] | Scanner and robot were both CIP Safety slaves; a safety-rated master was missing. | Direct body; date from indexed metadata. |
| n.d. | Control.com | “avoid unnecessary shut downs caused by possible faulty detections of failure”[9] | Redundant detection can reduce false trips, but the same discussion says TMR is not always required and emphasizes field diagnostics. | Direct body; legacy date not exposed. |
| 2003-10-02* | Control.com | “Using a single alarm acknowledge bit pulsed by the SCADA host is the wrong way to do it.”[10] | Shared acknowledgement and communication latency can erase causal evidence; per-alarm handshake is the counterexample. | Direct body; *dated reply in thread. |
| 2014-04-29 | Eng-Tips | “They had been crossed out in the PLC program”[11] | Nuisance AS-i stops were traced to EMC/grounding, but some E-stops had been disabled; customer later distributed a report and required documented testing. | Direct body; date from indexed metadata. |
| n.d. | Eng-Tips | “Brief power outages knocking out steam plant is causing major grief.”[12] | Transient power and manual reset burden prompted an auto-reset question; poster ultimately consulted the state inspector and changed hardware. | Direct body; date not exposed. |
| n.d. | Eng-Tips | “certain places can't be recovered from short of a power-cycle.”[13] | A fragile state machine and long servo boot time create production pressure; thread distinguishes recovery engineering from verified safety. | Direct body; date not exposed. |
| n.d. | Eng-Tips | “You do not require a safety PLC for aux contact input in to the PLC.”[14] | Clear counterexample: a standard PLC may receive diagnostic status while the actual E-stop function remains hardwired/rated. | Direct body; legacy date not exposed. |
| 2018-12-16 | ROS Discourse | “encapsulate the cell in a parallel, isolated safety system”[15] | Community frames ROS as coordinator/supervisor around lower-level safety-critical systems; others cite deployed examples using that architecture. | Direct body; date confirmed by Discourse JSON. |
| 2022-07-20 | ROS Discourse | “enact a safety-like system based on raw sensor data for low-latency.”[16] | Collision Monitor offers stop/slow/approach and 97% test coverage, but the author says “safety-like,” not certified safety. | Direct body; date confirmed by Discourse JSON. |
| 2024-05-06 | ROS Discourse | “it stops the robot and says what it is doing so that the operator is not confused.”[17] | Plain-language/audio state explanations improve field usability; contributor admits this is years of experience, not a formal study. | Direct body; date confirmed by Discourse JSON. |
| 2017-10-24 | GitHub ros-industrial/abb | “I need to do this with software.”[18] | User asks to acknowledge E-stop and restore motors remotely; maintainer recommends established fieldbus or ABB RWS/abb_librws rather than expanding the generic driver. | GitHub API + issue page. |
| 2024-02-21 | GitHub Navigation2 | “Controller server will not start again.”[19] | Post-stop recovery looked like a bug; maintainer found unsupported configuration and rejected “driving blind,” closing wontfix. | GitHub API + issue/comments. |
| 2026-02-09 | GitHub Universal Robots ROS2 Driver | “it will not move until I restart the robot-driver”[20] | Maintainer separates RTDE lifecycle recovery from resending the robot program and provides a minimal recovery sequence. | GitHub API + issue/comments. |
| 2026-06-19 | GitHub Navigation2 | “denial-of-service issue affecting the availability of the collision monitoring / speed control path.”[21] | Malformed Range input could consume CPU/memory; scope required a range source and DDS-domain access, and maintainers requested validation. | GitHub API + issue/comments. |
| n.d. | Reddit r/PLC | “Switching from a safety relay to a safety plc doesn't and can't stop someone from wiring around things.”[22] | Counterbalances claims that safety PLCs make bypass impossible; discussion values diagnostics and locks but says culture remains decisive. | Page body extracted by web backend; ordinary anonymous curl/Jina returned 403, so reproducibility is limited. |
| n.d. | Reddit r/PLC | “Boss says raise the trip limit.”[23] | Dramatic story thread illustrates threshold creep and management pressure; it cannot establish prevalence or verify causality. | Page body extracted by web backend; ordinary anonymous curl/Jina returned 403, so reproducibility is limited. |

## Implications for a safety-manager-friendly independent monitor

### Product boundary now

Oscillink Safety Ops is **not safety-rated**. Position it as an independent **observability, audit, workflow, and risk-escalation layer**, not as the essential safety function, safety PLC replacement, muting controller, restart authority, or safe-speed controller. Its own failure or disconnection must not prevent the rated system from reaching its designed safe state. Until an appropriate certified architecture exists, avoid writes that reset, start, bypass, widen limits, or suppress rated trips.[1][15][16]

### Minimum useful data model

- Asset → cell/zone → safety function → device → dual channels → safety controller/input → final element.
- Explicit provenance and assurance labels: safety-rated input, standard PLC diagnostic mirror, HMI command, ROS/AI inference, manual observation.
- Separate states for **hazard present**, **trip active**, **device fault**, **communications fault**, **safety reset permitted**, **safety rearmed**, **control recovery pending**, and **fresh start requested**.
- Millisecond source timestamps plus arrival time, time-sync health, sequence number, freshness, quality, and configuration/safety-signature hash.
- Sensor disagreement and confidence/uncertainty, but uncertainty must never silently widen a safe envelope or suppress a rated trip.

### Safety-manager interface

1. **One-sentence cause:** “Gate G12 channels disagreed for 43 ms after close; 8 repeats this shift; probable alignment/wear.”[7]
2. **Causal timeline:** first-out event, subsequent cascade, acknowledgements, resets, program changes, force/bypass activation, and restart.[10]
3. **Guided recovery, not remote restart:** show prerequisites and vendor-supported steps; require a fresh deliberate start outside Oscillink.[3][18][20]
4. **Bypass register:** named owner, approver, reason, risk-assessment reference, permit/work order, affected hazards, compensating controls, start/expiry, and automatic escalation on overrun.[2][6]
5. **Change/threshold drift:** alert on forces, excluded devices, repeated setpoint increases, disabled alarms, safety-signature changes, and “temporary” mitigations that outlive the work order.[2][11][23]
6. **Nuisance-trip workbench:** cluster by device, channel timing, environment, power quality, network role, firmware/configuration, and production context; do not label a trip “nuisance” until reviewed.[4][7][11]
7. **Monitor-health panel:** loss of source, stale data, malformed/out-of-range values, dropped events, CPU/memory pressure, and degraded time synchronization.[19][21]
8. **Plain language:** describe what stopped, why, whether the hazard or device fault remains, who must act, and what evidence is missing.[17]

### Design principles from the counterexamples

- **Preserve independence without hiding information:** read diagnostic mirrors from standard PLC/HMI/ROS and status from the rated system, while visually separating them from safety-authoritative signals.[14][15]
- **Reduce unsafe workarounds by reducing uncertainty and recovery time:** richer diagnostics are a safety control against pressure, but not a substitute for guarding, validation, training, or management accountability.[7][20][22]
- **Fail closed epistemically:** if sensing, map, timing, provenance, or monitor health is insufficient, say “cannot establish safe condition”; never convert missing evidence into a green state.[19][21]
- **Escalate patterns, not just events:** repeated trips, repeated reset attempts, limit increases, force duration, and bypass recurrence are more actionable than a single alarm.[2][11][23]

## Selection-bias and evidence caveats

- Forum participants self-select around problems; failures, near misses, and dramatic stories are overrepresented. Silence cannot be read as safe performance.
- Posters are often anonymous or pseudonymous. Credentials, jurisdiction, machine configuration, incident causality, and claimed outcomes were not independently verified.
- The sample is English-language and heavily weighted toward controls engineers/integrators. Operators, EHS staff, unions, OEM safety engineers, insurers, and non-Western plants are underrepresented.
- Older threads may describe obsolete controllers, firmware, interfaces, or editions of standards. They remain useful for recurring human/system patterns, not current compliance instructions.
- Search and extraction ranking favor text-rich, indexed pages. Closed groups, internal incident reports, deleted posts, and plants with weak reporting cultures are absent.
- Direct verification means the quoted text appeared in the retrieved page body or official GitHub/Discourse API. It does **not** authenticate the speaker or validate technical/legal advice.
- Reddit had no active agent-reach backend. Two Reddit pages were recovered through the web extraction backend, but anonymous curl/Jina returned 403; their dates were not exposed and reproducibility is weaker than the other sources. No Reddit passage is treated as standards guidance.[22][23]
- Dates marked **n.d.** were not exposed in the directly retrieved representation; they were not guessed.
- This is qualitative voice-of-user evidence, not a prevalence estimate. “Recurring” means the same mechanism appeared across multiple independent threads/communities, not that a statistically representative share of plants experiences it.

## Sources

[1] https://www.plctalk.net/forums/threads/implementing-an-override-on-safety-plc.125501
    > "I was wondering if it would be possible to connect the switch to the nearest PLC which would transmit the status to the Safety PLC along with a watchdog bit and so on."
[2] https://www.plctalk.net/forums/threads/machine-safety-and-maintenance-bypass.108977
    > "Turns out that the position feedback of the machine was screwed and they did not know what to do to move the machine. A couple of bits forced in the CPU and the machine was where it was needed safely. And yes... until I figured that one out (a short cable at a gland) I'd be called day or night to move it and keep production."
[3] https://www.plctalk.net/forums/threads/question-disable-button-after-emergency-stop.135718
    > "My problem is when the emergency stop is activated and the operator toggle button, if is reset safety, the action executes."
[4] https://www.plctalk.net/forums/threads/question-about-sick-safety-laser-scanner-for-robot-arm.139817
    > "it was the amber beacon on the forkloift causing the trip, a quick fix was to place a screen (in my case a flattened cardboard box tied to the cell cage so the beacon would not interfere with the barrier), I informed them that my heath robinson fix should be replaced with something more appropriate, two years later it was still there."
[5] https://www.robot-forum.com/robotforum/thread/13027-bypassing-saftey-features
    > "I'm trying to avoid picking up the TP and creating more downtime and work than what is needed."
[6] https://www.robot-forum.com/robotforum/thread/39918-disable-safety-gate-error-under-certain-conditions
    > "I still want the robot to be stopped by the controller to ensure the safety but I'm looking for a way to not have to reset the whole system in each entry."
[7] https://www.robot-forum.com/robotforum/thread/34991-kuka-error-at-safe-input-safety-swithes
    > "With some of them I get dual channel safety error quite often, resetting the safety removes error."
[8] https://www.robot-forum.com/robotforum/thread/33763-emergency-stop-inoperative
    > "I am trying to use a SICK Safety SCANNER with CIP Safety to connect with the KRC4 but that is proving to be a challenge after SICK stated it was an easy thing to do, no documentation on either side of someone connecting one of these before."
[9] https://control.com/forums/threads/why-only-tmr-for-esd-applications.17278
    > "If you want to avoid unnecessary shut downs caused by possible faulty detections of failure, then you need to provide redundancy in the detection mechanism, and this is where TMR is used."
[10] https://control.com/forums/threads/alarms-management.14430
    > "Using a single alarm acknowledge bit pulsed by the SCADA host is the wrong way to do it."
[11] https://www.eng-tips.com/threads/emergency-stop-button-not-working.363988/page-2
    > "They had been crossed out in the PLC program, but left for anyone to see and press in the plant."
[12] https://www.eng-tips.com/threads/asme-csd-1-and-probe-style-lwco.418723
    > "Brief power outages knocking out steam plant is causing major grief."
[13] https://www.eng-tips.com/threads/click-restart.361328
    > "Currently certain places can't be recovered from short of a power-cycle."
[14] https://eng-tips.com/threads/overland-conveyor-e-stop-oull-cords-wired-through-plcs.209200
    > "You do not require a safety PLC for aux contact input in to the PLC. What is being assumed above is that you were running your e-stop string in to the plc, and in that scenariio yes it would require safety PLC."
[15] https://discourse.ros.org/t/reliability-safety-security-maintenance-and-support-in-ros/7146
    > "Right now it’s very difficult to integrate ROS safely in an industrial grade robot, having either to encapsulate the cell in a parallel, isolated safety system or making ROS act as a kind of supervisor, encapsulating more low level and safety critical systems."
[16] https://discourse.ros.org/t/nav2-collision-monitor-for-emergency-stopping/26554
    > "bypassing the trajectory planner to enact a safety-like system based on raw sensor data for low-latency."
[17] https://discourse.ros.org/t/guidelines-for-testing-ros-based-robots-in-the-real-world/37577
    > "it stops the robot and says what it is doing so that the operator is not confused."
[18] https://github.com/ros-industrial/abb/issues/136
    > "When an eStop is activated, for whatever reason, it is required to 'Acknowledge' the error on the FlexPendant and turn the motors back by pressing the blinking motors on switch to continue. I need to do this with software."
[19] https://github.com/ros-navigation/navigation2/issues/4132
    > "Controller server will not start again."
[20] https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/issues/1672
    > "If I now start sending movement commands, it will not move until I restart the robot-driver (not the robot or the motors)."
[21] https://github.com/ros-navigation/navigation2/issues/6216
    > "This is a denial-of-service issue affecting the availability of the collision monitoring / speed control path."
[22] https://reddit.com/r/PLC/comments/1ehjkav/safety_devices
    > "Switching from a safety relay to a safety plc doesn't and can't stop someone from wiring around things."
[23] https://reddit.com/r/PLC/comments/1ke8m1k/whats_your_horror_story_of_being_strongarmed
    > "Boss says raise the trip limit."
