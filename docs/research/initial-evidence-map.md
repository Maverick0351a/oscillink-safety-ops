# Initial Safety Ops evidence map

**Evidence cutoff:** 2026-08-31
**Status:** Discovery evidence; no safety/compliance/deployment claim.

## Direct authority and standards records

### OSHA hazardous energy control

[29 CFR 1910.147](https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.147)
requires an employer energy-control program with procedures, training, and periodic inspections.
It requires specific shutdown/isolation/blocking/securing steps, lock/tag responsibilities, and
verification of energy-control effectiveness. Push buttons and selector switches are not energy-
isolating devices.

### Industrial robot safety

The official ISO catalogue identifies:

- [ISO 10218-1:2025](https://www.iso.org/standard/73933.html): industrial robot design, risk
  reduction, and information for use; and
- [ISO 10218-2:2025](https://www.iso.org/standard/73934.html): integration, commissioning,
  operation, maintenance, decommissioning, and disposal of robot applications/cells.

The licensed standard text is not included. Catalogue summaries do not establish detailed
requirements.

### EU machinery regulation

[Regulation (EU) 2023/1230](https://eur-lex.europa.eu/eli/reg/2023/1230/oj) addresses autonomous
machinery, digital instructions, model applicability, lifecycle risk, software evolution, and
safety-affecting physical/digital modifications. It requires digital instructions to be available,
printable/downloadable, model-specific, and retained online for the expected lifetime and at least
ten years after market placement.

Safety Ops may preserve applicability/revision evidence and flag potential change impact. It must
not decide legal conformity or whether a modification is legally substantial.

## Technical adjacency

[MaCoPlanner, arXiv:2608.28300v1](https://arxiv.org/abs/2608.28300v1) compiles equipment manuals
into a typed intermediate representation and checks candidate plans against procedural/state
constraints. The authors report improved simulator task success, a 2.7% final violation rate, and
rejection of 26.3% of repair-analysis runs after budget exhaustion. These are preprint author claims
from a controller-panel simulator without an attached industrial load—not deployment evidence.

## Physical-data failure evidence

LeRobot primary issues show:

- calibration drift invisible through healthy training metrics but broken at deployment
  ([#3758](https://github.com/huggingface/lerobot/issues/3758));
- unresolved storage of camera intrinsics/depth scale
  ([#4417](https://github.com/huggingface/lerobot/issues/4417));
- unnoticed and later-unrecoverable camera mount drift
  ([#4496](https://github.com/huggingface/lerobot/issues/4496));
- inconsistent official task-association metadata
  ([#4519](https://github.com/huggingface/lerobot/issues/4519)); and
- pinned metadata contradictions across official datasets
  ([#4401](https://github.com/huggingface/lerobot/issues/4401)).

This supports evidence/applicability pain. It does not prove OCR demand or Safety Ops product demand.

## Competitor boundary

- [Tulip Digital Guidance](https://tulip.co/digital-guidance/) already offers SOP-to-digital
  guidance, versioning, PDF-to-app conversion, OCR, AI vision, connected devices, and copilots.
- [MaintainX](https://www.getmaintainx.com/use-cases/checklists-and-inspections) offers procedures,
  inspections, scheduling, approvals, corrective actions, audit trails, and AI fault detection.
- [Mitti/SafetyCulture](https://safetyculture.com/template-upload) converts forms into inspection
  templates.
- [HFlow](https://github.com/Hebbian-Robotics/hflow), lerobot-doctor, trajlens, and metadata-health
  cover broad robotics data quality/provenance/curation.
- PaddleOCR, Docling, Marker, and Tesseract already cover OCR/document parsing.

Safety Ops should integrate existing systems and own the governed binding between exact safety
evidence and offline physical-intelligence tasks/evaluations. It should not recreate their general
products.

## Build / experiment / monitor / reject

| Action | Decision |
| --- | --- |
| Build | Contract and synthetic fixture only after practitioner gate |
| Experiment | source-region citations, applicability, stale propagation, conflict review, offline task comparison |
| Monitor | ISO 10218:2025 adoption, EU implementation, MaCoPlanner follow-up, connected-worker APIs |
| Integrate | CMMS/work-instruction exports, OCR providers, robotics dataset/evaluation tools |
| Reject | generic OCR/checklists/CMMS, certification, permits, safety control, live actuation |
