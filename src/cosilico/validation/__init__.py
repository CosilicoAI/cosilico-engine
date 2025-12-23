"""Validation module for Cosilico.

VALIDATION STRATEGY (see README.md for details):

1. Reference Validation: Validate Python output against PolicyEngine ONCE per variable
2. Cross-Compilation: Ensure all targets (JS, Python, WASM) produce IDENTICAL results

This module provides utilities for both phases.
"""

from .consistency import (
    CrossCompilationValidator,
    CompilationResult,
    ConsistencyReport,
)
from .reference import ReferenceValidator

__all__ = [
    "CrossCompilationValidator",
    "CompilationResult",
    "ConsistencyReport",
    "ReferenceValidator",
]
