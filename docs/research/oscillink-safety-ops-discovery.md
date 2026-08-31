# Oscillink Safety Ops discovery

**Evidence cutoff:** 2026-08-31
**Status:** Strategic direction approved; first workflow remains an experiment candidate.

## Product thesis

**Oscillink Safety Ops is a governed safety-evidence control plane for physical intelligence.** It
connects workplace regulations, company SOPs, equipment manuals, labels, risk assessments and task
or episode evidence without converting extracted text directly into equipment authority.

The first outcome is:

> Given one identified asset, a proposed maintenance/operation task and a bounded source set,
> produce a reviewable Safety Evidence Packet showing applicable cited requirements, stale or
> mismatched documents, unresolved conflicts and missing evidence before offline planning or
> evaluation.

Safety Ops is not a safety PLC, interlock, emergency stop, work-permit issuer, legal-compliance
certificate, autonomous safety officer or robot controller.

## Why safety documents matter to physical intelligence

Physical-intelligence systems operate inside an authority environment that model weights and
sensor data do not contain:

- jurisdictional requirements;
- site-specific procedures and role assignments;
- manufacturer-defined intended use, limits and precautions;
- asset/model/serial-specific instructions;
- hazardous energy sources and isolation points;
- training, inspection and authorization state;
- equipment and procedure revisions;
- temporary work instructions, permits and change notices; and
- incident-derived corrections and prohibited approaches.

A physical model can identify a control or predict a trajectory while still selecting a task that
is procedurally unauthorized, tied to the wrong asset revision or missing a required isolation or
verification step. These are evidence and governance failures, not merely perception failures.

## Primary authority evidence

### OSHA hazardous energy control

[OSHA 29 CFR 1910.147](https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.147)
is direct US regulatory text for servicing and maintenance involving unexpected energization,
startup or stored-energy release.

Relevant requirements include:

- an employer energy-control program consisting of procedures, training and periodic inspections
  (`1910.147(c)(1)`);
- documented and used energy-control procedures (`1910.147(c)(4)`), subject to a narrow exception;
- procedures that clearly specify scope, purpose, authorization, rules and techniques;
- specific shutdown, isolation, blocking and securing steps (`1910.147(c)(4)(ii)(B)`);
- lock/tag placement, removal, transfer and responsibility (`1910.147(c)(4)(ii)(C)`);
- testing to verify the effectiveness of energy-control measures (`1910.147(c)(4)(ii)(D)`);
- annual periodic inspection by an authorized employee other than the employees using the
  procedure (`1910.147(c)(6)`); and
- training so employees understand the program and acquire the knowledge and skills required for
  safe application, use and removal of controls (`1910.147(c)(7)`).

The regulation also distinguishes energy-isolating devices from control-circuit devices: push
buttons and selector switches are not energy-isolating devices. That distinction is suitable for a
seeded evidence-reconciliation fixture, but Safety Ops must cite the live authoritative source and
must not independently declare compliance.

### Current industrial robot safety standards

The official ISO catalogue search identifies:

- [ISO 10218-1:2025](https://www.iso.org/standard/73933.html), covering inherently safe design,
  risk reduction and information for use of industrial robots; and
- [ISO 10218-2:2025](https://www.iso.org/standard/73934.html), covering integration, commissioning,
  operation, maintenance, decommissioning and disposal of industrial robot applications and cells.

The standard text is licensed and was not retrieved during this reconnaissance. Safety Ops must
not redistribute standards or infer requirements from catalogue summaries. Organizations must
supply documents they are authorized to use, and exact edition/applicability must be preserved.

### EU machinery regulation

[Regulation (EU) 2023/1230](https://eur-lex.europa.eu/eli/reg/2023/1230/oj) explicitly addresses
increasingly autonomous machinery and safety risks from new digital technologies. It requires risk
assessment across intended use, foreseeable misuse, lifecycle and intended evolution of autonomous
behaviour. It defines instructions for use as including intended/proper use, precautions and how
to keep equipment safe throughout its lifetime.

The regulation also establishes evidence-management implications:

- instructions must identify the product model to which they correspond;
- digital instructions must be printable/downloadable and accessible during breakdown;
- online instructions must remain available for the expected lifetime and at least ten years after
  market placement; and
- a physical or digital modification that creates a new hazard or increases risk can become a
  substantial modification with manufacturer obligations and conformity-assessment consequences.

Safety Ops can preserve model/revision/applicability evidence and flag potential change impact. It
must not decide whether a modification is legally “substantial” or certify conformity.

## Technical adjacency—not deployment evidence

[MaCoPlanner, arXiv:2608.28300v1](https://arxiv.org/abs/2608.28300v1) is a recent preprint that
compiles equipment manuals into a typed intermediate representation, retrieves task/state evidence,
rolls out candidate plans symbolically and checks procedural/state-transition constraints before
actuation. The authors report a 2.7% final violation rate, reject 26.3% of repair-analysis runs after
budget exhaustion and report task-success improvements over a raw-manual baseline.

These are author claims from a controller-panel simulator without an attached industrial load; the
paper explicitly does not claim industrial deployment readiness. It supports typed manual evidence
and abstention/rejection as useful research directions. It does not validate live Safety Ops control.

## Existing market boundary

Safety and frontline operations software is already crowded:

- [Tulip Digital Guidance](https://tulip.co/digital-guidance/) offers SOP-to-digital guidance,
  version control, AI Composer, PDF-to-app conversion, OCR, operator copilots, AI vision,
  inspections and connected devices.
- [MaintainX checklists and inspections](https://www.getmaintainx.com/use-cases/checklists-and-inspections)
  offers global procedures, conditional checklists, work approvals, inspection scheduling,
  corrective actions, photos, audit trails and AI-assisted fault detection.
- [Mitti/SafetyCulture template upload](https://safetyculture.com/template-upload) converts PDF,
  Word and Excel forms into digital inspection templates.

Oscillink should not compete as another CMMS, work-instruction authoring suite, inspection form,
training platform or PDF chatbot. Safety Ops should accept reviewed exports/connectors from those
systems and bind their exact revisions to physical-intelligence tasks, datasets, plans and
evaluations.

## Differentiated contract

### Source classes

Preserve source class without inventing a universal legal hierarchy:

- regulation or regulator guidance;
- licensed standard;
- manufacturer manual or safety bulletin;
- site risk assessment;
- company SOP or energy-control procedure;
- work order, permit or temporary instruction;
- equipment label/nameplate/photo;
- training/authorization evidence; and
- task plan, simulation trace, dataset episode or incident record.

Jurisdiction, site, asset, model, serial number, role, task phase, edition, effective date and
supersession state determine applicability. Conflicts go to an authorized EHS/safety reviewer;
Safety Ops never resolves legal precedence autonomously.

### Safety Evidence Packet

Every packet should contain:

1. SHA-256 and revision identity for every source byte sequence.
2. OCR/parser/provider identity and exact configuration.
3. Page/frame and bounding-box citation for each extracted candidate.
4. Raw text separated from normalized fields.
5. Typed fields for asset identity, task phase, role, hazard, energy source, prerequisite, PPE,
   isolation, verification, prohibited condition and emergency action.
6. Applicability facts and explicit unknowns.
7. Conflicts, stale revisions, missing evidence and unsupported interpretations.
8. Human review decisions, corrections, retractions and supersession lineage.
9. A deterministic packet policy/configuration hash.
10. A machine-readable sidecar plus a human-readable review report.

Extracted requirements are candidates. Only externally reviewed revisions can enter an approved
Safety Evidence Packet.

## First workflow: LOTO/SOP Safety Evidence Reconciler

### Inputs

Use a pinned synthetic/public fixture containing:

- an asset-nameplate image;
- a manufacturer manual excerpt for the exact model;
- a site-specific hazardous-energy/LOTO SOP;
- a maintenance work order or proposed task plan; and
- the applicable public OSHA excerpt.

Do not include full licensed standards, real employee records, private facility layouts or customer
SOPs in the public fixture.

### Seeded evidence defects

- work order references a different model/serial than the manual and label;
- task plan says “press stop” but cites no energy-isolating device;
- hydraulic or pneumatic stored energy is absent from the site procedure;
- SOP revision is superseded by a later approved revision;
- required verification step is absent from the task plan;
- role/authorization is missing or ambiguous; and
- one OCR field is deliberately unreadable and must produce abstention.

Expected answers remain outside agent-readable fixture inputs.

### Output states

Use closed, evidence-oriented states such as:

- `matched`;
- `missing_evidence`;
- `asset_mismatch`;
- `revision_stale`;
- `source_conflict`;
- `ambiguous`;
- `unreadable`;
- `unsupported_interpretation`; and
- `requires_authorized_review`.

Do not emit `safe`, `compliant`, `certified` or `approved_to_operate` from automated extraction.

## Physical-intelligence integration

The first integration remains offline and read-only:

1. Convert approved Safety Evidence Packets into evaluation constraints and scenario prompts.
2. Compare a proposed symbolic task plan or recorded episode with applicable evidence.
3. Return exact violations, missing evidence and citations for human review.
4. Preserve plan, source and review revisions under equal evaluation budgets.
5. Never dispatch motion, issue a permit, clear a lockout or alter a safety-rated system.

Only after independent safety engineering, simulation, formal hazard analysis and a separately
approved deployment case could any bounded operational integration be considered. A future system
must still leave deterministic safety-rated control, interlocks and emergency stops outside Hermes
and outside model authority.

## Commercial hypothesis

Potential users and buyers:

- EHS and workplace-safety teams;
- maintenance/reliability organizations;
- industrial robot integrators;
- physical-AI data and evaluation teams;
- OEM technical-publication and safety engineering teams; and
- insurers/auditors only as evidence consumers, not as automated certification targets.

The open local wedge can be source intake, versioning, citations, review and offline evaluation.
Potential paid layers are private connectors, multi-site policy distribution, approved-review
workflows, change-impact analysis, retention, audit export, on-prem deployment and support.

The likely disadvantage is longer enterprise sales, high liability sensitivity and a requirement
for domain experts. Safety Ops must earn trust through narrow evidence tooling before using broader
“safety” claims.

## Validation questions

Interview at least:

- two EHS/safety professionals;
- two maintenance/reliability managers or technicians;
- two industrial robot integrators;
- two physical-AI/robotics data engineers; and
- two technical-publication, compliance or equipment-manual owners.

Ask:

- Which documents govern one real maintenance or robot-cell task?
- How are asset/model/serial and procedure revision matched today?
- What happens when the manual, SOP and work order disagree?
- Which steps require an authorized person rather than a checklist?
- How are changes propagated to training, evaluation and deployed task plans?
- Which evidence is still paper/image/PDF versus structured?
- What false positive or missed requirement would make the tool unusable?
- Would they run a local read-only reconciliation report this week?
- Who owns budget and liability for the workflow?

## Success criteria

Proceed beyond the fixture only if:

- every extracted candidate cites exact source bytes and location;
- unreadable/ambiguous content abstains;
- unapproved text cannot become an operational constraint;
- source revision changes make derived packets explicitly stale;
- conflicts remain unresolved until authorized human review;
- the seeded fixture defects are found without compliance/safety claims;
- at least five practitioners validate the document/task bundle as realistic;
- at least three run it locally on sanitized or private evidence;
- at least two receive an actionable mismatch; and
- review time is lower than the avoided manual reconciliation burden.

## Kill criteria

Stop or narrow Safety Ops if:

- customers primarily need ordinary digital work instructions or CMMS forms;
- current systems already export sufficient structured constraints;
- site/legal variability prevents a bounded reusable contract;
- users expect certification, live authorization or safety-rated control;
- document rights prevent lawful processing;
- OCR uncertainty creates unmanageable review work;
- no safety professional will own review decisions; or
- the product cannot demonstrate value without taking operational authority.

## Portfolio decision

| Action | Decision |
| --- | --- |
| Build | A contract/fixture for the read-only LOTO/SOP Safety Evidence Reconciler after practitioner review |
| Experiment | OCR citations, applicability, conflict detection, stale revision propagation and offline plan/episode comparison |
| Monitor | ISO 10218:2025 adoption, EU Machinery Regulation implementation, MaCoPlanner follow-up and connected-worker APIs |
| Integrate | Existing CMMS/work-instruction exports and physical-AI dataset/evaluation tools |
| Reject | Generic checklist software, legal certification, permit issuance, safety PLC/interlock control and live actuation |

## Immediate next action

Use the synthetic fixture specification to conduct five problem interviews before implementing the
runtime. If at least three interviewees recognize the bundle and two can provide a sanitized/local
example, freeze the Safety Evidence Packet contract with adversarial tests before adding an OCR
adapter.
