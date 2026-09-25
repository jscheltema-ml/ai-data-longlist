"""Shared by every check: the run loop, the verdict write, and how a buyer is put in a prompt."""

from stages.verify.utils.checks import Check, run_check, write_verdict
from stages.verify.utils.prompts import CANDIDATE_BLOCKS, candidate

__all__ = [
    "CANDIDATE_BLOCKS",
    "Check",
    "candidate",
    "run_check",
    "write_verdict",
]
