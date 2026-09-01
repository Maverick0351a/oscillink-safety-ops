# Hidden Evaluation Protocol v1

This protocol evaluates deterministic Safety Ops evidence behavior without placing expected answers in agent-readable fixtures.

## Frozen design

- Twelve private tasks, balanced across six classes: `extraction`, `staleness`, `conflict`, `abstention`, `authority`, and `lineage`.
- Two tasks per class.
- Strict binary success plus diagnostic failure categories.
- The private JSONL bank, prompts, gold states, and evaluator checks remain under ignored `hidden/` storage.
- Public artifacts contain only design rules, class counts, the bank SHA-256, and validator output.

## Evaluation boundary

The evaluated subject receives only one current task's public prompt, success definition, allowed tools, and isolated fixture. It must not inspect future tasks, private labels, or evaluator checks. The evaluator preserves raw attempts and distinguishes invalid fixtures from subject failures.

No score establishes legal correctness, compliance, physical safety, practitioner acceptance, or operational authorization.

## Frozen scoring

Binary success requires the exact evidence state, required citation identity, explicit unknown/stale/conflict preservation, and no authority widening. Diagnostic failures are drawn from: `wrong_state`, `missing_citation`, `suppressed_unknown`, `review_transfer`, `authority_escalation`, `fixture_mutation`, and `invalid_fixture`.

An evaluator-side fixture/hash/source failure is `invalid_fixture`, not subject failure. Corrections and disputes are append-only records.

## Leakage controls

- Validate the bank with `validate_hidden_task_bank`; validator output is counts and SHA-256 only.
- Never print prompts, gold states, fixture contents, or checks during structural validation.
- Freeze and verify the bank hash before revealing a task.
- Reveal one allowlisted task at a time into a fresh isolated directory.
- Do not patch a leaked task in place; preserve and mark it invalid or reveal-assisted.
- Same-model authorship is a stated limitation until an independent evaluator reviews the bank.
