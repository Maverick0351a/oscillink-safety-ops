"""Export canonical JSON Schemas for portable adapter contracts."""

from __future__ import annotations

import json
from pathlib import Path

from oscillink_safety_ops.domain import (
    AuditReport,
    FederalRegisterChangeCandidate,
    FederalRegisterChangeChain,
    LsaCoverageCandidate,
    OperationalChangeImpact,
    OperationalEvidenceBatch,
    OperationalImpactReport,
    OperationalInterpretationCandidate,
    OperationalReviewLedger,
    PhysicalIntelligenceEvidenceEnvelope,
    ProposedPlan,
    RegulatoryArtifactVerification,
    RegulatoryChangeEvidenceBundle,
    RegulatoryDifferenceReview,
    RegulatorySectionComparison,
    RegulatorySectionSnapshot,
    RegulatorySourceImpactReport,
    RegulatorySourceVerificationCandidate,
    RegulatorySourceVerificationReview,
    ReviewedRegulatoryDifference,
    SafetyEvidencePacket,
    SafetyMemoryPacket,
    VerifiedRegulatorySource,
)

SCHEMAS = {
    "audit-report.schema.json": AuditReport.model_json_schema(),
    "federal-register-change-chain.schema.json": FederalRegisterChangeChain.model_json_schema(),
    "federal-register-change-candidate.schema.json": (
        FederalRegisterChangeCandidate.model_json_schema()
    ),
    "lsa-coverage-candidate.schema.json": LsaCoverageCandidate.model_json_schema(),
    "operational-change-impact.schema.json": OperationalChangeImpact.model_json_schema(),
    "operational-evidence-batch.schema.json": OperationalEvidenceBatch.model_json_schema(),
    "operational-interpretation-candidate.schema.json": (
        OperationalInterpretationCandidate.model_json_schema()
    ),
    "operational-impact-report.schema.json": OperationalImpactReport.model_json_schema(),
    "operational-review-ledger.schema.json": OperationalReviewLedger.model_json_schema(),
    "physical-intelligence-evidence-envelope.schema.json": (
        PhysicalIntelligenceEvidenceEnvelope.model_json_schema()
    ),
    "proposed-plan.schema.json": ProposedPlan.model_json_schema(),
    "regulatory-change-evidence-bundle.schema.json": (
        RegulatoryChangeEvidenceBundle.model_json_schema()
    ),
    "regulatory-difference-review.schema.json": RegulatoryDifferenceReview.model_json_schema(),
    "regulatory-artifact-verification.schema.json": (
        RegulatoryArtifactVerification.model_json_schema()
    ),
    "regulatory-section-comparison.schema.json": RegulatorySectionComparison.model_json_schema(),
    "regulatory-section-snapshot.schema.json": RegulatorySectionSnapshot.model_json_schema(),
    "regulatory-source-impact-report.schema.json": RegulatorySourceImpactReport.model_json_schema(),
    "regulatory-source-verification-candidate.schema.json": (
        RegulatorySourceVerificationCandidate.model_json_schema()
    ),
    "regulatory-source-verification-review.schema.json": (
        RegulatorySourceVerificationReview.model_json_schema()
    ),
    "safety-memory-packet.schema.json": SafetyMemoryPacket.model_json_schema(),
    "reviewed-regulatory-difference.schema.json": ReviewedRegulatoryDifference.model_json_schema(),
    "safety-evidence-packet-v1.schema.json": SafetyEvidencePacket.model_json_schema(),
    "verified-regulatory-source.schema.json": VerifiedRegulatorySource.model_json_schema(),
}


def render(schema: dict[str, object]) -> str:
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "schemas"
    root.mkdir(exist_ok=True)
    for name, schema in SCHEMAS.items():
        (root / name).write_text(render(schema), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
