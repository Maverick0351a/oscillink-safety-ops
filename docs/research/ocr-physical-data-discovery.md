# OCR-to-physical-data workflow discovery

**Evidence cutoff:** 2026-08-31
**Status:** Component experiment under [Oscillink Safety Ops](oscillink-safety-ops-discovery.md);
no product-demand or safety claim.
**Governance:** The broader Governed OCR product thesis remains an unapproved Project Memory
candidate.

## Decision

**Retain one read-only Physical Evidence Reconciler component:** ingest a camera/robot label image,
a calibration or run-sheet document, and a LeRobot Dataset v3 metadata snapshot; emit a governed
sidecar receipt that identifies exact source regions, normalized physical fields, ambiguities,
missing values and cross-source mismatches.

The parent product direction is now **Oscillink Safety Ops**. Its first candidate workflow is a
LOTO/SOP Safety Evidence Reconciler connecting workplace procedures and equipment manuals to
offline physical-intelligence plans/evidence. The robotics-metadata workflow in this report remains
a possible later adapter, not the primary wedge.

Do **not** build a generic OCR engine, generic robotics data-quality platform, dataset editor,
training pipeline or actuator integration.

## Why this workflow

LeRobot Dataset v3 reconstructs episodes through metadata rather than file boundaries. The
canonical v3 documentation says metadata carries schema, frame rate, statistics and episode
segmentation, while `meta/episodes/` stores per-episode lengths, tasks and offsets. This makes
metadata correctness consequential to which physical evidence is associated with an episode.

Primary issue evidence shows several classes of failure:

1. **Calibration drift can survive training.** LeRobot issue
   [#3758](https://github.com/huggingface/lerobot/issues/3758) reports an approximately 17-degree
   leader/follower offset producing approximately 6 cm end-effector error. Training metrics looked
   healthy; deployment was broken. The proposed diagnostic uses already-recorded data and is
   read-only.
2. **Camera metadata has no settled canonical home.** LeRobot issue
   [#4417](https://github.com/huggingface/lerobot/issues/4417) asks where intrinsics and depth scale
   should live and describes competing `info.json`, `tools`, dedicated-file and external-file
   conventions.
3. **Camera pose evidence can disappear.** LeRobot issue
   [#4496](https://github.com/huggingface/lerobot/issues/4496) reports unnoticed mount drift inside
   one session and argues that a deliberate physical reference must be captured before the
   original pose becomes unrecoverable.
4. **Metadata conventions already conflict.** LeRobot issue
   [#4519](https://github.com/huggingface/lerobot/issues/4519) documents two official v3 task
   association layouts; one downstream linter produced 1,693 false positives before supporting
   both conventions.
5. **Published metadata defects are material.** LeRobot issue
   [#4401](https://github.com/huggingface/lerobot/issues/4401) reports a pinned census of 188
   official repositories and identifier contradictions across 11 snapshots representing more than
   432 million summed declared frame records. Its author explicitly avoids claiming raw trajectory
   corruption or policy-quality effects.
6. **Silent coordinate/schema failures exist.** Issues
   [#4524](https://github.com/huggingface/lerobot/issues/4524) and
   [#3863](https://github.com/huggingface/lerobot/issues/3863) describe dataset-global versus
   file-local timestamp confusion and implicit state/action positional alignment that can silently
   select wrong frames or corrupt training targets.

These sources support a need for stronger physical evidence and reconciliation. They do not prove
that OCR is the preferred acquisition method.

## Commodity and competitor boundary

### OCR is commodity infrastructure

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) already provides scene OCR, coordinates,
  tables, charts and structured JSON/Markdown across many languages.
- [Docling](https://github.com/docling-project/docling) already provides layout, reading order,
  tables, formulas, OCR and lossless JSON.
- Tesseract and Marker provide additional local extraction options.

Oscillink should adapt one or more reviewed extractors. Recognition models, document layout and
PDF-to-Markdown are not the product moat.

### Generic robot-data quality is already occupied

- [HFlow](https://github.com/Hebbian-Robotics/hflow) is an active Apache-2.0 YC S26 SDK for
  multimodal physical-AI pipelines. It already covers MCAP/LeRobot ingestion, quality checks,
  provenance, queryable evidence, SQL curation and planned LeRobot export. Issue
  [#191](https://github.com/Hebbian-Robotics/hflow/issues/191) specifies a real-camera
  import→quality→curate→export workflow; issue
  [#293](https://github.com/Hebbian-Robotics/hflow/issues/293) shows its own multi-shard metadata
  edge cases.
- [lerobot-doctor](https://github.com/jashshah999/lerobot-doctor),
  [trajlens](https://github.com/Kunal-Somani/trajlens) and
  [lerobot-metadata-health](https://github.com/sawhney17/lerobot-metadata-health) already cover
  broad diagnostics, repair and metadata census work.
- Rerun and Foxglove/MCAP already provide strong multimodal visualization and telemetry formats.

Oscillink should not reimplement their general pipeline or position Data Doctor as a broad dataset
linter.

## Differentiated contract

The experiment owns the governed bridge between **out-of-band physical evidence** and **digital
physical-AI metadata**:

1. Hash every original document/image and record its source revision.
2. Call a replaceable OCR/layout adapter.
3. Preserve every extracted value with page/frame, bounding box, extractor identity and raw text.
4. Normalize only a small typed vocabulary:
   - equipment role, manufacturer, model and serial number;
   - calibration identity, timestamp and validity window;
   - camera intrinsics, depth scale and declared units;
   - robot/controller/sensor identifiers;
   - task/run/operator identifiers where explicitly present.
5. Keep unit conversions and ambiguous mappings as separate evidence-bearing transformations.
6. Compare extracted candidates with one immutable LeRobot metadata snapshot.
7. Emit typed outcomes: `matched`, `missing_in_dataset`, `missing_in_evidence`, `mismatch`,
   `ambiguous`, `unreadable` and `unsupported`.
8. Never mutate the dataset. Produce a sidecar receipt and proposed corrections only.
9. Require external human review before any corrected value becomes approved memory or a published
   dataset revision.
10. Preserve retractions, supersession and exact lineage.

## First pinned fixture

Use synthetic or permissively licensed bytes only:

- one camera/robot asset-label image;
- one camera calibration sheet;
- one operator run card;
- one minimal LeRobot v3 metadata snapshot.

Seed transparent defects:

- label serial differs from dataset sensor ID;
- calibration timestamp predates a declared validity window;
- depth scale has an explicit millimetre/metre ambiguity;
- intrinsics exist in the sheet but are absent from dataset metadata;
- run-card task text differs from the episode task association.

Expected labels stay outside agent-readable inputs. Deterministic evaluation scores exact field
extraction, source-region citation, abstention, mismatch classification and proposed-correction
lineage under the same fixture and OCR adapter version.

## Success criteria

A one-command read-only experiment passes only if:

- original bytes and extracted spans are SHA-256/revision bound;
- every normalized field cites an exact source region;
- seeded defects are found without mutating source data;
- ambiguous units and unreadable fields cause abstention rather than invention;
- rerunning identical inputs yields the same receipt;
- changing OCR engines does not change the receipt schema or governance rules;
- a human can correct one extracted value and the old value remains explainable;
- at least three external physical-AI users recognize the input bundle as representative of their
  workflow; and
- at least two users receive an actionable mismatch on their own sanitized/local evidence.

## Kill criteria

Stop or narrow the OCR lane if:

- target users already keep authoritative metadata digitally and have no scanned/image evidence;
- direct structured import is cheaper and more reliable than OCR for the selected workflow;
- HFlow, LeRobot or another existing tool can add the same bridge as a trivial check;
- source-region confidence cannot support useful human review;
- review time exceeds avoided data-repair or failed-training time;
- users want generic document search rather than physical-data reconciliation; or
- no user will run the experiment on their own local evidence.

## Strongest counterargument

The observed failures establish metadata and calibration pain, not OCR demand. A disciplined team
could capture camera intrinsics, serials and calibration facts directly as structured metadata and
then use LeRobot/HFlow validation. OCR adds recognition error, ambiguity and review cost. The
experiment is justified only where physical evidence genuinely arrives as labels, sheets, photos
or legacy reports that cannot be replaced immediately by structured capture.

## Portfolio decision

| Action | Decision |
| --- | --- |
| Build | A tiny pinned Physical Evidence Reconciler contract/fixture after workflow interviews |
| Experiment | OCR adapter interchangeability, source-region citations, unit abstention and cross-source mismatch detection |
| Monitor | LeRobot metadata conventions; HFlow import/curation/export; camera calibration/mount tooling |
| Reject | Generic OCR, generic Data Doctor, training/policy promotion, live robot integration and actuator control |

## Next evidence action

Interview or observe five physical-AI practitioners—at least two hobbyist/LeRobot users, two lab or
data engineers and one deployment/collection operator. Ask whether calibration sheets, asset labels,
run cards or maintenance records actually sit outside the dataset, how mismatches are found today,
and what one read-only local report they would run this week.
