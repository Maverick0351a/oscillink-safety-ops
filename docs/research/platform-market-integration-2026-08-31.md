# Physical-intelligence platform, market, and integration decision

**Evidence cutoff:** 2026-08-31
**Decision status:** Product direction is approved; integration and workflow recommendations remain
experiments until practitioner validation.
**Evidence labels:** **Verified fact** = checked in a canonical repository, first-party documentation,
or official record; **Author/vendor claim** = first-party statement not independently reproduced;
**Hypothesis** = Oscillink inference to test. GitHub activity dates are mutable snapshots, not adoption
or quality evidence.

## Executive decision

Build the portable governed contract and deterministic local CLI first. The easiest-adoption wedge is
an immutable **JSON Safety Memory Packet + JSON proposed-plan sidecar -> JSON audit report**. It needs
no robotics dependency, can sit beside any task/dataset/export, and preserves authority boundaries.
Make **closed MCAP/rosbag2 analysis** the first ecosystem experiment because MCAP is already a shared,
read-only recording boundary across ROS 2, HFlow, Rerun, and Foxglove. Add LeRobot-v3 metadata and
HFlow-catalog adapters before simulator/runtime hooks. Do not start inside a robot control loop.

The buyer hypothesis is a robot integrator's safety/validation lead or a physical-AI data/evaluation
team; an EHS or authorized safety reviewer owns approval decisions. Enter with one cell/AMR zone/high-
risk task and one bounded document/task bundle, run locally, and return an evidence-linked audit
packet. Distribution should be a one-command CLI and schemas first, local MCP second, then adapters
that attach to existing data systems. Paid value, if validated, is private connectors, review
workflow, change-impact propagation, retention, multi-site governance, on-premises deployment, and
support—not inference resale or generic document chat.

**Strongest counterargument:** a CMMS/work-instruction export plus ordinary deterministic checks may
solve the actual workflow more cheaply. Incumbents already own source documents, approvals, users,
and distribution; robotics metadata may not be a safety-budget problem. No external user validation
has occurred, so the present build proves a contract and authority boundary only.

## Safety memory, precisely

Safety memory is an append-only, provenance-bearing record of reviewed evidence, not model context or
a vector index. A portable packet must preserve:

1. immutable source bytes and SHA-256, source class, rights metadata, revision/edition, effective date,
   jurisdiction, site, asset/model/serial, role, task phase, and applicability unknowns;
2. extraction candidates separately from approved constraints, including provider/parser identity,
   exact configuration, raw text, page/frame/bounding-box or line citation, and quote hash;
3. an external authorized review decision with reviewer role/identity and time; agents and OCR can
   create candidates but cannot approve them;
4. correction, rejection, retraction, and supersession lineage without deleting prior revisions;
5. unresolved conflicts without an autonomous precedence rule;
6. deterministic stale propagation whenever source, applicability, review, or policy revisions change;
7. exact citations in every finding; and
8. an offline audit packet containing the input identities, policy hash, deterministic findings, and
   explicit unknowns.

Allowed automated finding states are `matched`, `missing_evidence`, `asset_mismatch`,
`revision_stale`, `source_conflict`, `ambiguous`, `unreadable`, `unsupported_interpretation`, and
`requires_authorized_review`. These are evidence states, not a risk score, legal result, permit,
release decision, or physical command.

## Platform integration ledger

| Platform | Canonical source, version/activity, license | Native interfaces and boundary | Smallest Safety Ops seam |
| --- | --- | --- | --- |
| NVIDIA Isaac Sim | [repo](https://github.com/isaac-sim/IsaacSim), [6.0.1 release](https://github.com/isaac-sim/IsaacSim/releases/tag/v6.0.1), [docs](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/). **Verified fact:** repo pushed 2026-07-02. GitHub reports `NOASSERTION`; the repo license requires separate licenses for Omniverse Kit and assets. | USD simulation; URDF/MJCF/CAD import; ROS 2, OmniGraph, Replicator annotators/writers. No universal plan schema. | **Hypothesis:** post-run Replicator output/recording reader. A custom writer is later and must copy only; no timeline/controller mutation. |
| NVIDIA Isaac Lab | [repo](https://github.com/isaac-sim/IsaacLab), [3.0 beta release](https://github.com/isaac-sim/IsaacLab/releases/tag/v3.0.0-beta2.patch1), [architecture](https://isaac-sim.github.io/IsaacLab/release/3.0.0-beta2/source/refs/reference_architecture/index.html). Core BSD-3-Clause with separately licensed dependencies; active 2026-08. | Gymnasium environments; observations/actions and manager terms for commands, rewards, termination, curriculum, and simulation events. | **Hypothesis:** evaluate saved rollouts first; later a pure Gymnasium observer wrapper that returns inputs/outputs unchanged. |
| NVIDIA Isaac GR00T | [repo](https://github.com/NVIDIA/Isaac-GR00T), [N1.7](https://github.com/NVIDIA/Isaac-GR00T/releases/tag/n1.7-release). Code Apache-2.0; weights use NVIDIA Open Model License. | LeRobot-derived metadata (`info.json`, `episodes.jsonl`, `tasks.jsonl`, `modality.json`), Parquet state/action, MP4, policy observation/action chunks, ZMQ policy service. | **Hypothesis:** open-loop dataset audit. Mirror request/response envelopes only after offline evidence; never alter action chunks. |
| NVIDIA Cosmos | [Predict 2.5](https://github.com/nvidia-cosmos/cosmos-predict2.5), [Transfer 2.5](https://github.com/nvidia-cosmos/cosmos-transfer2.5), [Cosmos NIM API](https://docs.nvidia.com/nim/cosmos/3.0.0/api-reference.html). Repos Apache-2.0; weights/NIM have separate NVIDIA terms. | Text/image/video/world conditioning, generated video/world trajectories; NIM inference, health, metadata, and manifest endpoints. **Vendor claim:** world foundation models for physical AI. | **Hypothesis:** hash and audit completed NIM request/response artifacts asynchronously; generated trajectories remain model output, never approved evidence. |
| NeMo Curator / NIM | [Curator repo](https://github.com/NVIDIA-NeMo/Curator), [v1.3.0](https://github.com/NVIDIA-NeMo/Curator/releases/tag/v1.3.0), [video abstractions](https://docs.nvidia.com/nemo/curator/latest/about/concepts/video/abstractions.html). Curator Apache-2.0; NIM containers retain product terms. | Typed pipeline tasks/stages; video/clip objects; MP4, JSON, embeddings, and Parquet exports. It is a curation surface, not a robot planner. | **Hypothesis:** read completed Parquet/metadata exports as candidates; do not add authority to a processing stage. |
| Hugging Face LeRobot | [repo](https://github.com/huggingface/lerobot), [v0.6.1](https://github.com/huggingface/lerobot/releases/tag/v0.6.1), [dataset v3](https://huggingface.co/docs/lerobot/lerobot-dataset-v3). **Verified fact:** Apache-2.0, pushed 2026-08-31. | Parquet state/action/timestamps, MP4 media, `meta/info.json`, `stats.json`, `tasks.jsonl`, episode offsets; robot and policy interfaces. | **Build-next hypothesis:** read finalized v3 metadata/shards and emit a JSON sidecar. Do not wrap `send_action`. |
| Physical Intelligence openpi | [repo](https://github.com/Physical-Intelligence/openpi), [remote inference](https://github.com/Physical-Intelligence/openpi/blob/main/docs/remote_inference.md). **Verified fact:** Apache-2.0, no formal releases, pushed 2026-08-24. | LeRobot datasets, robot-specific input/output adapters, `policy.infer`, WebSocket/MsgPack remote inference returning action chunks. | **Hypothesis:** offline dataset/checkpoint envelope audit. A network tap is deferred because delay or mutation could affect operation. |
| ROS 2 + rosbag2 | [rosbag2 repo](https://github.com/ros2/rosbag2), [documentation](https://github.com/ros2/rosbag2#readme). **Verified fact:** Apache-2.0 and active 2026-08-31. | Topics, services, actions; timestamped serialized recordings; storage/serialization plugins; MCAP default storage; message-loss events. Plans remain application-defined. | **Experiment:** read closed bags and message-loss metadata. No publisher, service client, replay, recorder control, or robot graph mutation. |
| MCAP | [repo](https://github.com/foxglove/mcap), [specification](https://mcap.dev/spec). **Verified fact:** MIT and active 2026-08-31. | Serialization-neutral Schema, Channel, Message, Attachment, Chunk, Metadata, Index, Statistics, Summary records. No inherent task semantics. | **First ecosystem experiment:** inspect footer/summary/channel/schema metadata, then decode only selected evidence topics. Portable range-readable boundary. |
| Rerun | [repo](https://github.com/rerun-io/rerun), [importers](https://rerun.io/docs/concepts/logging-and-ingestion/importers/overview). **Verified fact:** Apache-2.0 and active 2026-08-31; project also publishes MIT-licensed components. | Timestamped entity/component logs, RRD, MCAP and LeRobot import, SDK sinks, DataFrame/SQL query, external importers. | **Hypothesis:** query existing RRD/MCAP through readers; present findings as a separate artifact. Avoid logging hooks in controllers. |
| Foxglove | [SDK repo](https://github.com/foxglove/foxglove-sdk), [export docs](https://docs.foxglove.dev/docs/data/exporting-data), [extension API](https://docs.foxglove.dev/docs/extensions). SDK/MCAP are MIT; current desktop/cloud product is commercial and the old Studio repo is archived. | Live/recorded topics, schemas, message events, MCAP export, TypeScript panel/converter extensions. | **Hypothesis:** headless MCAP audit first; later a display-only panel using recorded message ranges and no advertise/publish capability. |
| HFlow | [repo](https://github.com/Hebbian-Robotics/hflow), [integration map](https://github.com/Hebbian-Robotics/hflow/blob/main/docs/INTEGRATIONS.md), [v0.2.4](https://github.com/Hebbian-Robotics/hflow/releases/tag/v0.2.4). **Verified fact:** Apache-2.0, pre-v1, active 2026-08-31. | Synchronized MCAP episodes; Python checks/transforms; Parquet catalog; DuckDB manifests; provenance/artifacts; LeRobot v3 import. | **Best ready-made adapter seam:** read catalog Parquet with DuckDB and emit separate findings. HFlow's evidence/measurement orientation is complementary. |
| NVIDIA Halos for Robotics | [official page](https://www.nvidia.com/en-us/ai-trust-center/halos/robotics/), [architecture](https://developer.nvidia.com/blog/inside-nvidia-halos-for-robotics-a-full-stack-functional-safety-system-for-physical-ai/), [Outside-In docs](https://docs.nvidia.com/halos-outside-in/latest/index.html). **Vendor claim:** full-stack functional-safety platform; parts remain early access. | Runtime safe-compute/OS/middleware/application and outside-in perception-to-safe-state paths. | **Monitor/partner, do not imitate:** Safety Ops supplies governed enterprise evidence offline and never enters Halos control/safe-state paths. |

### Cross-platform conclusion

**Verified fact:** MCAP is shared by ROS 2, HFlow, Rerun, and Foxglove; LeRobot/HFlow use
Parquet/JSON metadata; Isaac, GR00T, Cosmos, and openpi expose distinct simulation, dataset, or policy
interfaces. **Hypothesis:** portable JSON contracts should be the control plane, MCAP the immutable
episode envelope, and Parquet the cohort/catalog layer. Do not invent a universal “plan” by flattening
language tasks, trajectories, commands, and recorded actions.

## Competitor and adjacency map

| Lane | Products and canonical sources | Classification and implication |
| --- | --- | --- |
| Operational safety intelligence | [Intenseye Chief](https://www.intenseye.com/chief), [Voxel](https://www.voxelai.com/), [Protex AI](https://www.protex.ai/) | **Direct/converging:** camera observations, procedures, analytics, recommendations, and corrective workflows. Vendor outcome claims are not independent validation. They own retrofit distribution; public material is less explicit about immutable source applicability and correction lineage. |
| Autonomous-system safety evidence | [Edge Case Research](https://www.ecr.ai/product-services), [Ketryx Physical AI](https://www.ketryx.com/industries/physical-ai), [Foretellix](https://www.foretellix.com/), [Applied Intuition](https://www.applied.co/products/basis) | **Direct or near-direct:** living safety cases, traceability/change impact, scenario/coverage evidence, and V&V. Strongest competitive threat. Safety Ops must complement their engineering evidence rather than claim a universal safety case. |
| EHS/CMMS systems of record | [Cority Cortex AI](https://www.cority.com/cortex-ai/), [SafetyCulture AI](https://safetyculture.com/ai-tools/), [MaintainX](https://www.maintainx.com/) | **Adjacent with distribution power:** incidents, inspections, actions, assets, work orders, manuals, and approvals. Integrate reviewed exports; do not rebuild their workflows. |
| Digital work instructions / SOP extraction | [Tulip AI Composer](https://support.tulip.co/docs/tulip-ai-composer), [Poka Industrial AI](https://www.poka.io/en/industrial-ai-factory-floor), [Augmentir](https://www.augmentir.com/) | **Adjacent/commodity boundary:** PDF/SOP conversion, guidance, copilots, and skills. Reject generic authoring, OCR, training, and document chat. Imported text remains a candidate. |
| Industrial copilots | [Siemens Industrial Copilot](https://press.siemens.com/global/en/pressrelease/siemens-and-microsoft-scale-industrial-ai) | **Adjacent/platform threat:** manual retrieval, maintenance and engineering within an installed automation estate. A connector/channel is more credible than replacement. |
| Robot runtime safety | [NVIDIA Halos](https://www.nvidia.com/en-us/ai-trust-center/halos/robotics/) | **Complement and boundary:** runtime functional-safety/control path. Safety Ops must stay offline and read-only. |
| Robotics data quality | [HFlow](https://github.com/Hebbian-Robotics/hflow), Rerun, Foxglove | **Complement:** recording, provenance, curation, visualization. Safety Ops should add approved-memory applicability and findings, not duplicate ingestion/visualization. |

No reviewed public product was verified to combine approved manual/SOP applicability, immutable revision
and correction lineage, unresolved conflicts, deterministic stale propagation, physical-AI task and
episode reconciliation, and portable offline packets. That is a **hypothesized white space**, not proof
of demand or absence: product internals are not fully public and the market is converging quickly.

## Adoption map

1. **Now — JSON/JSONL sidecar + CLI:** lowest dependency and authority footprint; works with exports
   from every platform. JSON Schema makes the contract inspectable. A JSONL envelope is appropriate
   for batches after the single-packet contract stabilizes.
2. **Next experiment — MCAP/ROS 2 recording analysis:** broadest existing episode boundary; post-hoc,
   no runtime subscriber, no replay, no command path.
3. **Next experiment — HFlow/Parquet and LeRobot-v3 metadata:** datasets already contain episode/task,
   state/action, timestamp, and provenance surfaces. Emit separate findings; never mutate source data.
4. **Later — Isaac evaluation export and visual panels:** useful distribution, but simulator and UI
   plugins add version/licensing burden without improving the core evidence contract.
5. **Local MCP:** expose packet recall/explain and audit only after the file contract is stable. MCP
   must not make an agent an approver or expose operational tools.

## Build / Experiment / Monitor / Reject

| Action | Decision and evidence gate |
| --- | --- |
| **Build** | Provider-neutral Pydantic contracts, JSON Schemas, content-addressed synthetic bytes, deterministic audit, exact citations, CLI, and canonical verifier. This proves technical integrity only. |
| **Experiment** | One closed-MCAP adapter and one LeRobot/HFlow metadata adapter against the same hidden expected findings. Measure setup time, decoded data volume, deterministic repeatability, false findings, missed findings, and reviewer time. |
| **Monitor** | Halos, Isaac/GR00T/Cosmos schema changes, ROS 2/MCAP releases, LeRobot v3 evolution, HFlow pre-v1 stability, EU Machinery Regulation implementation, and incumbent evidence-lineage features. |
| **Reject** | Runtime robot wrappers, ROS publishers/services/replay, policy action interception, safety PLC/interlock/E-stop integration, permits, certification, universal precedence, generic OCR/CMMS/work instructions, and model-generated approval. |

## Decisive validation and kill criteria

Pilot privately on one user-owned, rights-cleared task bundle. Preregister success: five practitioners
recognize the bundle; three can run the local report; two receive an actionable mismatch; all findings
retain exact citations; ambiguity abstains; source change propagates stale state; and review time is
less than manual reconciliation. Compare against a spreadsheet/CMMS-export baseline under equal data
and reviewer time.

Kill or narrow if ordinary structured checks match the result more cheaply; reviewers will not own
approval; rights prevent processing; site/legal variability defeats a bounded schema; false findings
or abstentions create more work than they remove; buyers demand certification or live authority; or
no value remains when all outputs are read-only.

## Source-status limitations

- Canonical GitHub repository metadata and selected licenses/activity were directly rechecked on
  2026-08-31. Repository existence/activity does not establish deployment, correctness, or revenue.
- Product capability and customer-outcome statements remain vendor claims unless explicitly tied to
  an official record; no independent customer interviews or reproductions were performed.
- Firecrawl extraction was unavailable in this environment. Canonical links were verified through
  repository APIs/direct pages during reconnaissance; unavailable deep-page extraction is recorded
  rather than replaced with search snippets.
- ISO catalogue metadata was used only to identify editions; licensed standards text was not
  retrieved or paraphrased into requirements.
- The local Project Memory MCP returned approved direction and authority-boundary revisions with
  exact hashes. It also reported one not-approved item and one superseded item in its exclusion
  summary; neither was promoted. MCP content was treated as cited untrusted data and checked against
  repository rules and direct sources.
