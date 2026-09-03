# Product and authority boundary

## Product outcome

Oscillink Safety Ops is an independent safety and risk-mitigation supervisor for AI-controlled
industrial equipment, connecting machine intent, observed behavior, and safety-manager oversight.

The production AI runs the machine. The intended Oscillink architecture independently monitors
whether commanded and observed behavior remain within an approved operating envelope and requests a
protective response when they do not.

## Current implementation

The current package implements exact-byte governed evidence, external-review lineage, explicit
unknown and stale states, offline plan/episode evaluation, and a deterministic closed-file runtime
supervisor. The runtime correlates recorded command intent and independently modeled observations,
applies immutable signed configuration, preserves a latch, and writes local simulated one-way
protective-stop or inhibit request records.

The current primary artifact is a Safety Evidence Packet for one identified asset and task. It
preserves exact source revisions, extraction regions, typed candidates, applicability, conflicts,
human review, corrections, and lineage.

## Implemented simulated supervisor

The isolated runtime-supervision plane covers one simulated fenced robot cell. It uses closed replay
or simulation inputs to compare untrusted command intent, independently modeled occupancy and motion
observations, and immutable configuration. Outputs are local simulated advisory, inhibit, or
protective-stop request records plus a latched incident and recovery timeline.

This is current simulation/replay behavior, not a live integration. The public demonstrator does not
connect to or control real machinery.

## Active private-pilot workflow

The active product experiment is deliberately limited to one identified industrial asset or robot
cell, one bounded maintenance or integration task, one rights-cleared manual/SOP/asset/task evidence
bundle, and one externally authorized reviewer. The product output remains a reviewable packet and
offline evidence findings only.

New OCR providers, jurisdictions, regulatory parser breadth, live facility connectors, live robot
runtime adapters, hosted services, and real-machine interfaces remain deferred. The separately
approved synthetic runtime-supervisor batches do not change the private-pilot gate for real evidence
workflows.

## Source boundary

Supported source classes may include:

- regulation or regulator guidance;
- licensed standard metadata or customer-supplied licensed content;
- manufacturer manual or safety bulletin;
- site risk assessment;
- company SOP or hazardous-energy procedure;
- work order, permit, or temporary instruction;
- equipment label/nameplate/photo;
- training/authorization evidence; and
- task plan, simulation trace, dataset episode, or incident record.

Source class does not create a universal precedence hierarchy. Jurisdiction, site, asset,
model/serial, role, task phase, edition, effective date, and supersession determine applicability.
Conflicts require authorized review.

## Automated authority

Automated extraction can create candidates and evidence-oriented findings only. It cannot:

- approve a safety requirement;
- declare an asset/task safe or compliant;
- certify conformity;
- issue a permit or authorize lockout/tagout;
- identify a person as trained/authorized without reviewed evidence;
- resolve conflicting authority;
- modify a procedure or equipment configuration;
- control a safety function or physical system; or
- suppress ambiguity, missing evidence, retractions, or lineage.

## Physical boundary

No operational path may command a real robot, PLC, safety PLC, interlock, emergency stop, machine,
vehicle, tool, drive, or actuator. Simulation, replay, and shadow evaluation may write a one-way
request only to an in-memory fixture or closed local output. It may not acknowledge, reset, rearm,
start, or report successful physical stopping.

A future real-machine integration would require a separate authorization and configuration-specific
program with formal hazard analysis,
safety engineering, legal/insurance review, simulation and hardware-in-loop evidence, bounded
deterministic control, independent safety-rated mechanisms, incident response, and explicit human
approval. Restoring software state cannot reverse a physical action.

## Rights and privacy

- Do not redistribute licensed standards or equipment manuals without rights.
- Do not place real customer SOPs, employee records, permits, facility layouts, or incident data in
  public fixtures.
- Preserve document rights, retention, deletion, residency, and authorized-use metadata.
- Public evidence must use synthetic/permissively licensed bytes and hidden expected answers.

## Claim boundary

Allowed early claim:

> Safety Ops is being developed as an independent safety and risk-mitigation supervisor. The current
> release implements its governed evidence and offline-evaluation plane; runtime supervision remains
> planned.

Do not describe current behavior as “ensures safety,” “guarantees compliance,” “certifies
procedures,” “prevents incidents,” “validated in the field,” “achieves PL/SIL,” or “authorizes
operation.”

See [Assurance status and limitations](assurance-status.md) for the dedicated current status.
