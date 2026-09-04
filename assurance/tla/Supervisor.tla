---- MODULE Supervisor ----
EXTENDS Naturals, TLC

CONSTANT FaultEvents

VARIABLES mode,
          latched,
          everLatched,
          recoveryStage,
          recoveryCompleted,
          acknowledged,
          authority,
          lastEvent,
          latchBeforeEvent,
          motionCommand

vars == <<mode, latched, everLatched, recoveryStage, recoveryCompleted,
          acknowledged, authority, lastEvent, latchBeforeEvent, motionCommand>>

Modes == {"monitoring", "intervention_latched", "stopped_unverified",
          "reset_ready", "rearm_pending", "recovery_pending", "initializing"}
RecoveryModes == {"stopped_unverified", "reset_ready", "rearm_pending",
                   "recovery_pending", "initializing"}
Authorities == {"none", "production_observer", "fixture_observer",
                 "independent_safety_authority", "supervisor"}
Events == {"init", "production_attempt", "ack", "assess_reset", "reset",
           "rearm", "recovery_confirmed", "fresh_start", "fresh_evidence",
           "reboot", "noop"} \cup FaultEvents
AttributionFaultEvents == {"attribution_identity_reused",
                           "attribution_response_precedes_command",
                           "attribution_response_late"}

Init ==
    /\ mode = "monitoring"
    /\ latched = FALSE
    /\ everLatched = FALSE
    /\ recoveryStage = 0
    /\ recoveryCompleted = FALSE
    /\ acknowledged = FALSE
    /\ authority = "none"
    /\ lastEvent = "init"
    /\ latchBeforeEvent = FALSE
    /\ motionCommand = FALSE

Trip(event) ==
    /\ event \in FaultEvents
    /\ mode' = "intervention_latched"
    /\ latched' = TRUE
    /\ everLatched' = TRUE
    /\ recoveryStage' = 0
    /\ recoveryCompleted' = FALSE
    /\ acknowledged' = FALSE
    /\ authority' = "supervisor"
    /\ lastEvent' = event
    /\ latchBeforeEvent' = latched
    /\ motionCommand' = FALSE

ProductionAttempt ==
    /\ lastEvent' = "production_attempt"
    /\ authority' = "production_observer"
    /\ latchBeforeEvent' = latched
    /\ UNCHANGED <<mode, latched, everLatched, recoveryStage,
                   recoveryCompleted, acknowledged, motionCommand>>

Acknowledge ==
    /\ latched
    /\ mode = "intervention_latched"
    /\ mode' = "stopped_unverified"
    /\ acknowledged' = TRUE
    /\ recoveryStage' = 0
    /\ recoveryCompleted' = FALSE
    /\ authority' = "fixture_observer"
    /\ lastEvent' = "ack"
    /\ latchBeforeEvent' = latched
    /\ motionCommand' = FALSE
    /\ UNCHANGED <<latched, everLatched>>

AssessReset ==
    /\ latched
    /\ mode = "stopped_unverified"
    /\ acknowledged
    /\ mode' = "reset_ready"
    /\ authority' = "independent_safety_authority"
    /\ lastEvent' = "assess_reset"
    /\ latchBeforeEvent' = latched
    /\ motionCommand' = FALSE
    /\ UNCHANGED <<latched, everLatched, recoveryStage,
                   recoveryCompleted, acknowledged>>

Reset ==
    /\ latched
    /\ mode = "reset_ready"
    /\ acknowledged
    /\ mode' = "rearm_pending"
    /\ recoveryStage' = 1
    /\ recoveryCompleted' = FALSE
    /\ authority' = "independent_safety_authority"
    /\ lastEvent' = "reset"
    /\ latchBeforeEvent' = latched
    /\ motionCommand' = FALSE
    /\ UNCHANGED <<latched, everLatched, acknowledged>>

Rearm ==
    /\ latched
    /\ mode = "rearm_pending"
    /\ recoveryStage = 1
    /\ mode' = "recovery_pending"
    /\ recoveryStage' = 2
    /\ authority' = "independent_safety_authority"
    /\ lastEvent' = "rearm"
    /\ latchBeforeEvent' = latched
    /\ motionCommand' = FALSE
    /\ UNCHANGED <<latched, everLatched, recoveryCompleted, acknowledged>>

ConfirmRecovery ==
    /\ latched
    /\ mode = "recovery_pending"
    /\ recoveryStage = 2
    /\ recoveryStage' = 3
    /\ recoveryCompleted' = FALSE
    /\ authority' = "independent_safety_authority"
    /\ lastEvent' = "recovery_confirmed"
    /\ latchBeforeEvent' = latched
    /\ motionCommand' = FALSE
    /\ UNCHANGED <<mode, latched, everLatched, acknowledged>>

FreshStart ==
    /\ latched
    /\ mode = "recovery_pending"
    /\ recoveryStage = 3
    /\ mode' = "initializing"
    /\ latched' = FALSE
    /\ recoveryStage' = 4
    /\ recoveryCompleted' = TRUE
    /\ acknowledged' = FALSE
    /\ authority' = "independent_safety_authority"
    /\ lastEvent' = "fresh_start"
    /\ latchBeforeEvent' = latched
    /\ motionCommand' = FALSE
    /\ UNCHANGED everLatched

FreshEvidence ==
    /\ mode = "initializing"
    /\ ~latched
    /\ recoveryCompleted
    /\ recoveryStage = 4
    /\ mode' = "monitoring"
    /\ authority' = "supervisor"
    /\ lastEvent' = "fresh_evidence"
    /\ latchBeforeEvent' = latched
    /\ motionCommand' = FALSE
    /\ UNCHANGED <<latched, everLatched, recoveryStage,
                   recoveryCompleted, acknowledged>>

Reboot ==
    /\ mode' = IF latched THEN "intervention_latched" ELSE "initializing"
    /\ acknowledged' = FALSE
    /\ recoveryStage' = IF latched THEN 0 ELSE recoveryStage
    /\ recoveryCompleted' = IF latched THEN FALSE ELSE recoveryCompleted
    /\ authority' = "supervisor"
    /\ lastEvent' = "reboot"
    /\ latchBeforeEvent' = latched
    /\ motionCommand' = FALSE
    /\ UNCHANGED <<latched, everLatched>>

Noop ==
    /\ lastEvent' = "noop"
    /\ authority' = "none"
    /\ latchBeforeEvent' = latched
    /\ UNCHANGED <<mode, latched, everLatched, recoveryStage,
                   recoveryCompleted, acknowledged, motionCommand>>

Next ==
    \/ \E event \in FaultEvents : Trip(event)
    \/ ProductionAttempt
    \/ Acknowledge
    \/ AssessReset
    \/ Reset
    \/ Rearm
    \/ ConfirmRecovery
    \/ FreshStart
    \/ FreshEvidence
    \/ Reboot
    \/ Noop

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ mode \in Modes
    /\ latched \in BOOLEAN
    /\ everLatched \in BOOLEAN
    /\ recoveryStage \in 0..4
    /\ recoveryCompleted \in BOOLEAN
    /\ acknowledged \in BOOLEAN
    /\ authority \in Authorities
    /\ lastEvent \in Events
    /\ latchBeforeEvent \in BOOLEAN
    /\ motionCommand \in BOOLEAN

ProductionAuthoritySeparation ==
    /\ authority # "production_admin"
    /\ lastEvent = "production_attempt" => authority = "production_observer"

LatchClearRequiresFullRecovery ==
    (everLatched /\ ~latched) =>
        /\ recoveryCompleted
        /\ recoveryStage = 4
        /\ lastEvent \in {"fresh_start", "fresh_evidence", "reboot", "noop",
                           "production_attempt"}

AckIsNotReset ==
    lastEvent = "ack" =>
        /\ latched
        /\ mode = "stopped_unverified"
        /\ recoveryStage = 0
        /\ acknowledged
        /\ ~recoveryCompleted

ResetIsNotFreshStart ==
    lastEvent = "reset" =>
        /\ latched
        /\ mode = "rearm_pending"
        /\ recoveryStage = 1
        /\ ~recoveryCompleted

RebootPreservesLatch ==
    lastEvent = "reboot" => latched = latchBeforeEvent

NoMotionCommandDuringRecovery ==
    mode \in RecoveryModes => ~motionCommand

FaultsFailClosed ==
    lastEvent \in FaultEvents =>
        /\ latched
        /\ mode = "intervention_latched"
        /\ ~recoveryCompleted

AttributionUniquenessChronologyFailClosed ==
    lastEvent \in AttributionFaultEvents =>
        /\ lastEvent \in FaultEvents
        /\ latched
        /\ mode = "intervention_latched"
        /\ ~recoveryCompleted

====
