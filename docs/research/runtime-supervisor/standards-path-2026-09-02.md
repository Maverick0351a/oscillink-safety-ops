# Independent machinery safety supervisor: standards and conformity path

**Research cutoff:** 2026-09-02  
**Scope:** an independently separated subsystem supervising AI-controlled industrial production equipment and potentially performing protective stop, safe limited speed (SLS), safe direction (SDI), interlocking, monitored standstill/protective stop, and speed-and-separation monitoring (SSM).

> **Claim boundary:** This is a standards and conformity roadmap, not legal advice, a conformity assessment, or a certification. No architecture, test result, PL, SIL, category, CE status, NRTL listing, or “safety-rated” claim has been established.

## Bottom line

1. **Treat the product as a prospective safety-related control subsystem, not an evidence sidecar.** Its safety functions must be derived from machine/application risk assessment; feature names alone do not establish a required or achieved PL/SIL.
2. **Keep production AI outside the safety path.** The AI should have no authority to modify safety logic, thresholds, configuration, diagnostics, reset policy, or final safety outputs. Prefer deterministic, bounded safety logic, independent sensing where required, protected configuration, and a defined safe reaction to lost/invalid inputs. These are architecture recommendations; the exact measures must come from the selected licensed standards and application risk assessment.
3. **Use ISO 12100 for machine risk assessment, then select one principal machinery-control route—ISO 13849-1 (PL) or IEC 62061 (SIL)—for each safety function.** For a reusable complex programmable product/platform, IEC 61508 is the relevant underlying product-development framework because IEC 62061 publicly states that complex programmable subsystem design is outside its scope.[1][4][5]
4. **Robot applications add ISO 10218-2:2025 / ANSI/A3 R15.06-2025 and collaborative-operation constraints; they do not replace the control-system lifecycle.** SSM is an application-level function whose claim depends on the complete sensing–logic–communications–final-element chain and validated stopping performance, not merely a perception algorithm.[5][8][10]
5. **In the EU, an independently marketed hardware or software safety monitor is likely to meet the Machinery Regulation definition of a “safety component.”** Final classification needs EU counsel or a prospective notified body. If safety logic itself has self-evolving machine-learning behavior, Annex I Part A forces third-party conformity routes; avoiding ML in the safety monitor materially simplifies both assurance and regulatory treatment.[12]
6. **In the US, OSHA/NRTL electrical approval, machinery/robot product listing, and functional-safety assessment are distinct questions.** A listed panel does not certify the machine or its controlled loads.[13][14]

## 1. Standards map and current status

Public catalogue pages establish title, scope, status, and publication dates. They do **not** supply the complete normative requirements.

| Publication | Official status/date at cutoff | What it does for this product | Short official quote | Applicability caveat |
|---|---|---|---|---|
| **ISO 12100:2010** | Published 2010-11; ISO catalogue says “to be revised”; ISO/DIS 12100.2 is under development in 2026.[1] | Governing machine-level hazard identification, risk estimation/evaluation, risk reduction, documentation, and verification. Use before allocating safety functions. | “principles and a methodology for achieving safety in the design of machinery”[1] | A risk-assessment standard, not a controller product certificate and not a PL/SIL calculation standard. The DIS is not the published baseline. |
| **ISO 13849-1:2023** | Published 2023-04.[2] | PL-based design/integration methodology for SRP/CS, including software, in high-demand/continuous operation and across electrical, hydraulic, pneumatic, and mechanical technologies. | “design and integration of safety‐related parts of control systems (SRP/CS)”[2] | It does not select the safety function or PLr for the application, excludes low-demand mode, provides no specific cybersecurity measures, and says it does not give product/component-specific design requirements. |
| **ISO 13849-2:2012** | Published 2012-10; “to be revised”; ISO/DIS 13849-2 is under development in 2026.[3] | Validation by analysis and testing of safety functions, category, and achieved PL. | “validation by analysis and testing”[3] | Use the currently published edition unless the assessor/contract permits otherwise; do not treat the 2026 DIS as normative. Resolve its interface with ISO 13849-1:2023 in the compliance plan. |
| **IEC 62061:2021 + AMD1:2024 + AMD2:2026** | Consolidated edition 2.2 published 2026-03-20.[4] | Machinery-sector SIL lifecycle for safety-related control systems in high/continuous demand: specification, design/integration, verification, validation, software, configuration, and functional-safety planning. | “machinery sector specific standard within the framework of IEC 61508”[4] | Public scope says: “The design of complex programmable electronic subsystems ... is not within the scope.” Use IEC 61508 or an applicable product standard for such platform internals.[4] |
| **IEC 61508 series, Ed. 2** | Parts 1–7 published 2010; IEC says only Parts 1–4 contain normative requirements.[5] | Generic E/E/PE functional-safety lifecycle and appropriate basis for a reusable programmable safety product/subsystem, software, hardware integrity, and systematic capability. | “the standard applies to the entire E/E/PE safety-related system”[5] | Generic/basic standard, not a machine risk-assessment substitute. IEC also states EN 61508 itself does not provide EU presumption of conformity; machinery-sector/product standards remain important.[5] |
| **IEC 60204-1:2016 + AMD1:2021** | Consolidated edition 6.1 published 2021-09-15.[6] | Electrical equipment of non-hand-portable machines, from the supply connection; relevant to wiring, protection, control circuits, PDS integration, emergency-stop implementation, EMC, bonding, SCCR, and documentation. | “applies to electrical, electronic and programmable electronic equipment and systems”[6] | Electrical machine integration standard—not the functional-safety lifecycle and not evidence that a safety function achieves PL/SIL. National adoption/deviations matter. |
| **ISO 10218-1:2025** | Edition 3, published 2025-02; ISO lifecycle records publication on 2025-02-05.[7] | Industrial robot requirements before integration, treating the robot as partly completed machinery. | “safety requirements specific to industrial robots”[7] | Applies to industrial robots, not the complete cell or a generic machine monitor; it is not retroactive to robots manufactured before publication.[7] |
| **ISO 10218-2:2025** | Edition 2, published 2025-02; lifecycle records 2025-02-05.[8] | Industrial robot application/cell integration, commissioning, operation, maintenance, decommissioning, and disposal. | “requirements for the integration of industrial robot applications and industrial robot cells”[8] | System-integrator/application standard. Process hazards and excluded robot domains require additional standards. |
| **ISO/TS 15066:2016** | Published 2016-02; catalogue remains **Published**, but changed to “International Standard to be revised” on 2025-06-26.[9] | Collaborative industrial robot systems/work environment; supplements ISO 10218 collaborative-operation guidance. | “supplements the requirements and guidance on collaborative industrial robot operation”[9] | It is **not withdrawn** at the cutoff, but is under revision. ISO/AWI 15066-1 exists; an AWI is not a published replacement. The 2025 robot standards have absorbed substantial collaborative content, so determine with the assessor which TS provisions remain necessary for the application. |
| **ANSI/A3 R15.06-2025, Parts 1–2; R15.06-3-2025** | All three parts published 2025-10-29; Parts 1–2 approved 2025-08-21, Part 3 approved 2025-10-07.[10] | Current US industrial robot safety family. Parts 1–2 nationally adopt ISO 10218-1/-2:2025; Part 3 addresses use of industrial robot cells. | “a National Adoption of ISO 10218-1:2025 ... and ISO 10218-2:2025”[10] | Licensed American National Standard; US deviations and user obligations must be read in the purchased text. It supersedes the practical role of ANSI/RIA R15.06-2012 for new work; A3 notes RIA is now part of A3.[11] |
| **IEC 61800-5-2:2016** | Edition 2.0, published 2016-04-18.[15] | Product standard for safety-related power drive systems and their safety sub-functions; directly relevant when SLS/SDI/stop behavior is implemented in a drive. | “design and development, integration and validation of safety related power drive systems”[15] | A certified drive sub-function does not certify the full machine safety function. Validate sensors, communications, logic, mechanics, brakes/final elements, timing, and integration. |
| **IEC 62443-4-1:2018 / 4-2:2019** | Published 2018-01-15 and 2019-02-27 respectively.[16][17] | Supporting secure development lifecycle and IACS component security controls. | 4-1 includes “defect management, patch management and product end-of-life.”[16] | Cybersecurity supports safety and independence; it does not determine PL/SIL or replace functional-safety validation. ISO 13849-1 explicitly says it gives no specific cybersecurity measures.[2] |

### Licensed-requirement boundary

**Freely accessible and used here:** issuing-body catalogue metadata and abstracts; IEC’s functional-safety FAQ; A3 publication/store notices; the full EUR-Lex regulation; OSHA regulations; UL/IECEE public certification explanations.

**Licensed and not reproduced here:** ISO/IEC/ANSI normative clauses, PL/SIL selection and calculation details, categories/architectural constraints, diagnostic-coverage and common-cause criteria, systematic-capability tables, software-technique tables, fault exclusions, validation annexes/checklists, required test methods, national deviations, and exact robot/SSM separation-distance provisions. Obtain controlled, licensed copies and build a clause-by-clause compliance matrix. Catalogue abstracts cannot support a claim of conformity.

## 2. Function-by-function applicability

| Candidate function | Primary standards stack | Boundary that must be assessed |
|---|---|---|
| Protective stop / monitored standstill | ISO 12100 → ISO 13849-1/-2 **or** IEC 62061; IEC 60204-1 electrical integration; ISO 10218 for industrial robots | Triggering sensor through logic, communications, drive/brake/final element, safe state, restart/reset, timing, and faults. Do not equate a protective stop with the separate emergency-stop function. |
| SLS / SDI | Same machinery-control route plus IEC 61800-5-2 where a PDS implements the drive sub-function | Speed/direction feedback, encoder independence/diagnostics, parameter protection, command limits, reaction timing, drive capability, and mechanical stopping. |
| Guard interlocking | Same route plus the applicable interlocking/guard/product standards selected from the machine risk assessment | Guard device, actuator, defeat resistance, logic, locking if needed, reset/restart, final element, and installation. |
| SSM | ISO 10218-2:2025 and, where applicable, ISO/TS 15066; ISO 13849 or IEC 62061 for the complete safety function | Validated human detection and position uncertainty, robot/tool/workpiece geometry and speed, stopping time/distance, latency, foreseeable occlusion/faults, minimum separation calculation, and cell integration. A perception model or distance estimate alone is not an SSM safety function. |

IEC’s public guidance is explicit that the safety-system extent is determined by the safety function and runs “from sensor, through control logic and communication systems, to final actuator.”[5] Therefore an Oscillink certificate, if eventually obtained only for the logic box/software, would still require machine-level integration and validation before an application could claim PL/SIL performance.

## 3. EU Machinery Regulation 2023/1230

**Dates and status.** Regulation (EU) 2023/1230 is dated 14 June 2023, published in OJ L 165 on 29 June 2023, corrected in OJ L 169 on 4 July 2023, and generally applies from **20 January 2027**.[12]

**Likely product classification.** Article 3(3) defines a safety component as a component “including software” that is intended to fulfil a safety function, is independently placed on the market, and whose failure/malfunction endangers persons.[12] A separately sold safety supervisory subsystem fits that language on the stated intent, subject to final legal/notified-body classification. Annex II’s indicative list includes logic units and software ensuring safety functions. A monitor used only internally and not independently placed on the market may be classified differently, but the complete machine still must conform.

**Conformity route.** The exact route depends on Annex I classification:[12]

- **Annex I Part A:** includes safety components with fully or partly self-evolving behavior using ML that ensure safety functions. Article 25(2) requires one of: EU type examination (Module B) + conformity to type (C), full quality assurance (H), or unit verification (G). **No internal-production-control-only Module A route.**
- **Annex I Part B:** includes “Logic units to ensure safety functions” and presence-sensing protective devices. Article 25(3) permits Module A only when harmonized standards/common specifications specific to the category cover **all** relevant EHSRs; otherwise use B+C, H, or G.
- **Not listed in Annex I:** Article 25(4) uses internal production control (Module A).

This makes a deterministic, non-self-modifying monitor strategically preferable. The external production AI may remain adaptive, but it must not reconfigure or become part of the safety logic. Obtain a written pre-classification view from a prospective notified body; do not assume a software-only implementation escapes the definition.

**CE is not an assessor’s product badge.** The manufacturer compiles Annex IV technical documentation, performs the applicable Article 25 procedure, draws up the EU declaration of conformity, and affixes CE. The manufacturer assumes responsibility for compliance. A functional-safety certificate can be evidence inside that case; it is not itself CE conformity.[12]

**Harmonized standards caveat.** Presumption of conformity attaches only to EN standards/references actually published in the EU Official Journal for the applicable legislation and only for covered EHSRs. This research did not verify a final Regulation 2023/1230 citation set for the standards above; recheck the OJ at design freeze and placement on the market. IEC’s own FAQ warns that IEC/EN 61508 is not itself a harmonized machinery standard.[5]

**Cybersecurity is supporting but legally relevant.** Annex III addresses protection against corruption and safety/reliability of control systems. Article 20(9) allows limited presumption through an EU Cybersecurity Act scheme only where a referenced scheme covers those requirements.[12] Independently apply IEC 62443-4-1/-4-2 to protect configuration, update, identity, integrity, audit, availability, and security lifecycle; never infer that a security level establishes a safety integrity level.[16][17]

## 4. US OSHA, NRTL, and UL implications

- OSHA 29 CFR 1910.399 treats electrical equipment as acceptable when it is listed/labeled/certified or otherwise determined safe by an OSHA-recognized NRTL, while also providing routes for equipment no NRTL accepts and certain custom-made equipment supported by retained test data.[13] The separate general machine-guarding rule is 29 CFR 1910.212: https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.212.
- NRTL approval is tied to an NRTL’s recognized scope and applicable US product standard; it is **not** a general PL/SIL certificate and does not, by itself, satisfy the employer’s machine-guarding, control-of-hazardous-energy, or application risk-reduction duties.
- UL is one NRTL/certification provider, not the regulator and not the only possible assessor. UL publicly offers accredited assessments against IEC 61508, IEC 62061, and ISO 13849, and notified-body support for the Machinery Regulation.[19] IECEE’s CB system is third-party conformity assessment and can aid international acceptance, but national deviations, NRTL/AHJ requirements, and EU legal modules remain separate.[18]
- A UL 508A panel listing is narrow: “only covers the control panel and not the connected loads or equipment.”[14] UL identifies separate paths for robotic equipment (ANSI/UL 1740) and machinery (UL 2011 outline/NFPA 79 context), including limited-production and field-evaluation routes.[14] Confirm the exact product category and current NRTL scope with the selected NRTL/AHJ before freezing construction.

A realistic US market plan may therefore need **both** (a) electrical/product-safety listing or field evaluation for the hardware/assembly and (b) a functional-safety assessment/certificate for claimed PL/SIL capability, followed by machine/application validation. Neither substitutes for the other.

## 5. Staged design-for-safety-rating path

### Stage 0 — claim containment now

Label releases and demonstrations: **“not safety-rated; not certified; not for use as the sole or primary protective device.”** Keep existing certified machine safeguards and safety controls authoritative. Operate the subsystem in shadow/advisory mode, or behind an independent rated safety system, until the complete safety function has been validated.

### Stage 1 — intended use, boundaries, and classification

1. Define product versus application responsibilities, target machinery/robot classes, operating environments, lifecycle, interfaces, foreseeable misuse, and excluded uses.
2. Define the safety-system boundary from sensors through final elements and what the product certificate would and would not cover.
3. Choose target markets; obtain early written views from an EU notified body and US NRTL/AHJ on safety-component/logic-unit classification, Annex I route, product standards, and certificate/listing scope.

**Gate:** agreed scope, classification assumptions, editions, and claim wording—still no PL/SIL claim.

### Stage 2 — machine/application risk assessment and allocation

Perform ISO 12100 assessment per representative applications. Specify each safety function independently: hazardous event, demand/continuous mode, safe state, triggering conditions, reset/restart behavior, maximum tolerable response, required risk reduction, environmental limits, fault reaction, diagnostics, proof/periodic testing, and interfaces. Derive PLr or SIL from the chosen machinery route; do not pick a marketing target first.

**Gate:** approved safety requirements specification and allocation to sensor/logic/communications/final element.

### Stage 3 — select the assurance route

- Choose **ISO 13849-1/-2** where the PL ecosystem and machine/product context dominate.
- Choose **IEC 62061** where a machinery SIL lifecycle and subsystem decomposition fit better.
- Use **IEC 61508** for underlying reusable complex programmable hardware/software capability, especially if selling a general safety controller, software library, sensing subsystem, or platform across machine types.
- Add IEC 61800-5-2, IEC 60204-1, ISO 10218-1/-2, ANSI/A3 R15.06, ISO/TS 15066, interlocking/guarding/sensor standards, and machine type-C standards as the architecture/application requires.

Do not run duplicate PL and SIL programs without a market need; map evidence once and agree with the assessor how it supports each claim.

### Stage 4 — freeze an independent safety architecture

Design recommendations to validate against the licensed standards:

- separate safety compute, memory/configuration, update path, and final-output authority from production AI;
- no runtime learning or autonomous parameter changes in the safety path;
- safety parameters versioned, integrity-protected, access-controlled, range-checked, and changed only through an authorized safety lifecycle;
- safety decisions based on validated safety inputs, not solely on untrusted AI state;
- defined fail-safe/degraded reactions for stale, missing, inconsistent, or unauthenticated data;
- independence/common-cause analysis for shared power, clocks, networks, sensors, enclosures, software/toolchains, and final elements;
- bounded worst-case execution and communications time; watchdogs and diagnostics appropriate to the target;
- a non-safety diagnostic/evidence channel that cannot write back into safety logic.

**Gate:** architecture review demonstrates enforceable—not policy-only—separation.

### Stage 5 — lifecycle implementation and evidence

Establish functional-safety management, competence, independence of reviews, configuration/change management, supplier controls, traceability, anomaly management, and release baselines. Produce at least:

- safety plan, requirements and architecture specifications;
- hardware reliability evidence/FMEDA as applicable, FMEA/FTA and common-cause analysis;
- software safety plan, coding/design rules, static analysis, unit/integration/coverage evidence, tool confidence/qualification rationale, and freedom-from-interference evidence;
- interface control and safety manual with assumptions of use, claimed capability limits, diagnostics, test intervals, environmental limits, and integration constraints;
- cybersecurity threat model, secure-development records, update/recovery process, vulnerability handling, and proof that the AI/control plane cannot alter safety behavior;
- manufacturing controls, serialization, calibration, end-of-line tests, field feedback, and change-impact process.

### Stage 6 — independent verification and validation

Validate requirements and complete safety functions under normal operation, reasonably foreseeable misuse, single and combined faults required by the selected route, boundary timing, power/network disturbances, environmental/EMC stress, sensor uncertainty/occlusion, stopping performance, reset/restart, parameter corruption, update rollback, and adversarial interface inputs. For SSM, use hardware-in-loop and representative robot/cell trials with worst-case latency and stopping data; do not validate only on recorded perception datasets.

**Gate:** independent validation report closes every safety requirement and assumption of use. ISO 13849-2 expressly requires analysis and testing.[3]

### Stage 7 — pre-assessment, certification, and legal conformity

1. Conduct an assessor gap review before production hardware and software architecture are locked.
2. Agree the target of evaluation, certificate wording, safety manual, standards/editions, maximum capability, environmental scope, variants, and surveillance obligations.
3. Complete functional-safety assessment/certification with an accredited body where commercially or legally needed.
4. Complete electrical/product testing and NRTL listing/field evaluation for the US configuration.
5. For EU placement, execute the applicable Machinery Regulation module, compile the technical file, sign the declaration, and affix CE only after conformity is demonstrated.
6. Validate each final machine/cell integration separately; a component capability certificate is not an application safety-function certificate.

### Stage 8 — post-market safety lifecycle

Operate controlled vulnerability and anomaly intake, incident/near-miss review, field-performance monitoring, periodic test/calibration support, assessor-approved change control, certificate impact review, and safety communication. Any AI model, sensor, threshold, timing, operating envelope, or interface change must trigger formal impact analysis; EU “substantial modification” and new-manufacturer responsibilities must also be screened.[12]

## Decision recommendation for Oscillink Safety Ops

**Build now:** deterministic separated monitor; immutable/versioned safety configuration; one-way evidence/diagnostic export; explicit sensor-to-final-element boundary; ISO 12100 hazard/risk files; safety requirements and traceability; assessor-ready lifecycle records.

**Engage now:** one functional-safety certification body with IEC 61508 + ISO 13849/IEC 62061 scope, one EU notified body for Machinery Regulation pre-classification, and one US NRTL/AHJ path for hardware/product category.

**Experiment before committing:** compare an ISO 13849 product route against an IEC 61508 platform + IEC 62061/ISO 13849 integration route on one bounded protective-stop/SLS demonstrator. Measure evidence burden, independence, diagnostics, latency, final-element integration, and assessor findings—not just functional performance.

**Reject:** “AI safety monitor” language; self-modifying safety logic; AI-controlled thresholds/resets/updates; a certificate claim based on simulation or a certified component alone; using UL 508A, CE, IEC 62443, or a personnel credential as a proxy for functional-safety certification.

## Sources

[1] https://www.iso.org/standard/51528.html — ISO 12100:2010
    > "ISO 12100:2010 specifies basic terminology, principles and a methodology for achieving safety in the design of machinery."
[2] https://www.iso.org/standard/73481.html — ISO 13849-1:2023
    > "This document specifies a methodology and provides related requirements, recommendations and guidance for the design and integration of safety‐related parts of control systems (SRP/CS) that perform safety functions, including the design of software."
[3] https://www.iso.org/standard/53640.html — ISO 13849-2:2012
    > "ISO 13849-2:2012 specifies the procedures and conditions to be followed for the validation by analysis and testing of the specified safety functions"
[4] https://webstore.iec.ch/en/publication/112847 — IEC 62061:2021+A1:2024+A2:2026
    > "The design of complex programmable electronic subsystems or subsystem elements is not within the scope of this document."
[5] https://www.iec.ch/functional-safety/faq — IEC Functional Safety FAQ
    > "In every case, the standard applies to the entire E/E/PE safety-related system"
[6] https://webstore.iec.ch/en/publication/71256 — IEC 60204-1:2016+A1:2021
    > "IEC 60204-1:2016+A1:2021 applies to electrical, electronic and programmable electronic equipment and systems to machines not portable by hand while working"
[7] https://www.iso.org/standard/73933.html — ISO 10218-1:2025
    > "This document is not applicable to robots that are manufactured before the date of its publication."
[8] https://www.iso.org/standard/73934.html — ISO 10218-2:2025
    > "This document specifies requirements for the integration of industrial robot applications and industrial robot cells."
[9] https://www.iso.org/standard/62996.html — ISO/TS 15066:2016
    > "ISO/TS 15066:2016 specifies safety requirements for collaborative industrial robot systems and the work environment"
[10] https://automate.org/store/products/ansi-a3-r15-06-2025-american-national-standard-for-industrial-robots-and-robot-systems-safety-requirements-pdf-download — ANSI/A3 R15.06-2025 Store Record
    > "Published with all three parts on October 29, 2025."
[11] https://automate.org/robotics/news/new-ansi-a3-r15-06-2025-american-national-standard-for-industrial-robot-safety-now-available-for-purchase — A3 R15.06-2025 Announcement
    > "Integrated guidance for collaborative robot applications, consolidating ISO/TS 15066"
[12] https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02023R1230-20230629 — Regulation (EU) 2023/1230 consolidated
    > "means a physical or digital component, including software"
    > "It shall apply from C1 20 January 2027 ."
    > "Safety components with fully or partially self-evolving behaviour using machine learning approaches ensuring safety functions."
    > "shall apply the internal production control procedure (module A) set out in Annex VI."
[13] https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.399 — OSHA 29 CFR 1910.399
    > "If it is accepted, or certified, or listed, or labeled, or otherwise determined to be safe by a nationally recognized testing laboratory recognized pursuant to § 1910.7"
[14] https://www.ul.com/resources/does-ul-certified-industrial-control-panel-certification-cover-equipment-it-controls — UL: Industrial control panel certification scope
    > "A certification from UL Solutions for an enclosed industrial control panel only covers the control panel and not the connected loads or equipment that the panel controls."
[15] https://webstore.iec.ch/publication/24556 — IEC 61800-5-2:2016
    > "IEC 61800-5-2:2016 specifies requirements and makes recommendations for the design and development, integration and validation of safety related power drive systems"
[16] https://webstore.iec.ch/publication/33615 — IEC 62443-4-1:2018
    > "The life-cycle description includes security requirements definition, secure design, secure implementation (including coding guidelines), verification and validation, defect management, patch management and product end-of-life."
[17] https://webstore.iec.ch/publication/34421 — IEC 62443-4-2:2019
    > "IEC 62443-4-2:2019 provides detailed technical control system component requirements"
[18] https://www.iecee.org/certification/overview — IECEE Certification Overview
    > "the IEC CA Systems are based on 3rd-party CA"
[19] https://www.ul.com/services/industrial-functional-safety-services — UL Industrial Functional Safety Services
    > "We expertly assess the safety integrity levels (SILs) or performance levels (PLs) of equipment and systems against various functional safety standards"
