"""
HARDENING PATCH P14: Legal Reasoning State Machine
=================================================
Dedicated state machine for the legal reasoning lifecycle to ensure
transitions are strictly guarded and verifiable. Replaces ad-hoc
async orchestration for verdict generation.
"""

import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import threading

logger = logging.getLogger("legal_state_machine")

class LegalState(Enum):
    """Formal states of the legal reasoning lifecycle"""
    IDLE = "IDLE"
    INGESTING = "INGESTING"
    REASONING = "REASONING"
    VERDICT_GENERATION = "VERDICT_GENERATION"
    LEDGER_COMMIT = "LEDGER_COMMIT"
    ERROR = "ERROR"
    COMPLETED = "COMPLETED"

class LegalTrigger(Enum):
    """Triggers to transition between legal states"""
    START_INGESTION = "START_INGESTION"
    INGESTION_COMPLETE = "INGESTION_COMPLETE"
    START_REASONING = "START_REASONING"
    REASONING_COMPLETE = "REASONING_COMPLETE"
    GENERATE_VERDICT = "GENERATE_VERDICT"
    VERDICT_READY = "VERDICT_READY"
    COMMIT_SUCCESS = "COMMIT_SUCCESS"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    RESET = "RESET"

class LegalReasoningStateMachine:
    """
    Formal state machine for the Mahoun legal reasoning pipeline.
    Enforces that verdicts cannot be generated without proper reasoning,
    and cannot be committed without generation.
    """
    def __init__(self):
        self.state = LegalState.IDLE
        self.state_lock = threading.RLock()
        self.failed_transitions = 0
        self.history: List[str] = []
        
        # Define valid transitions: dict[CurrentState, dict[Trigger, NextState]]
        self.transitions: Dict[LegalState, Dict[LegalTrigger, LegalState]] = {
            LegalState.IDLE: {
                LegalTrigger.START_INGESTION: LegalState.INGESTING
            },
            LegalState.INGESTING: {
                LegalTrigger.INGESTION_COMPLETE: LegalState.REASONING,
                LegalTrigger.ERROR_OCCURRED: LegalState.ERROR
            },
            LegalState.REASONING: {
                LegalTrigger.REASONING_COMPLETE: LegalState.VERDICT_GENERATION,
                LegalTrigger.ERROR_OCCURRED: LegalState.ERROR
            },
            LegalState.VERDICT_GENERATION: {
                LegalTrigger.VERDICT_READY: LegalState.LEDGER_COMMIT,
                LegalTrigger.ERROR_OCCURRED: LegalState.ERROR
            },
            LegalState.LEDGER_COMMIT: {
                LegalTrigger.COMMIT_SUCCESS: LegalState.COMPLETED,
                LegalTrigger.ERROR_OCCURRED: LegalState.ERROR
            },
            LegalState.ERROR: {
                LegalTrigger.RESET: LegalState.IDLE
            },
            LegalState.COMPLETED: {
                LegalTrigger.RESET: LegalState.IDLE
            }
        }
    
    def transition(self, trigger: LegalTrigger, force: bool = False) -> tuple[bool, str]:
        """
        Transition to a new state based on a trigger.
        Force bypasses the transition check but logs a severe warning.
        """
        with self.state_lock:
            if trigger == LegalTrigger.ERROR_OCCURRED:
                self._do_transition(trigger, LegalState.ERROR)
                return True, "Emergency transition to ERROR"
                
            if trigger in self.transitions.get(self.state, {}):
                next_state = self.transitions[self.state][trigger]
                self._do_transition(trigger, next_state)
                return True, f"Transitioned to {next_state.value}"
                
            if force:
                logger.warning(f"FORCED transition ignoring rules: {self.state.value} via {trigger.value}")
                # We don't know the intended next state strictly, so we reject force
                # unless it's a known forced reset.
                if trigger == LegalTrigger.RESET:
                    self._do_transition(trigger, LegalState.IDLE)
                    return True, "Forced reset to IDLE"
                
            self.failed_transitions += 1
            msg = f"Invalid transition: cannot trigger {trigger.value} from {self.state.value}"
            logger.error(msg)
            return False, msg
            
    def _do_transition(self, trigger: LegalTrigger, next_state: LegalState):
        self.history.append(f"{self.state.value} -> {trigger.value} -> {next_state.value}")
        self.state = next_state
        logger.info(f"Legal state transitioned to {self.state.value}")
