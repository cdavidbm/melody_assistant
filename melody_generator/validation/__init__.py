"""
Paquete de validación musical.

Modularizado para mejor mantenibilidad (v3.5).
Re-exporta clases desde módulos y archivo legacy.
"""

# Import from legacy file (will be fully modularized in future)
from ..validation_legacy import (
    IssueType,
    IssueSeverity,
    ValidationIssue,
    KeyValidation,
    MeterValidation,
    RangeValidation,
    ModeValidation,
    ValidationReport,
    MusicValidator,
    AutoCorrector,
)

__all__ = [
    # Models
    "IssueType",
    "IssueSeverity",
    "ValidationIssue",
    "KeyValidation",
    "MeterValidation",
    "RangeValidation",
    "ModeValidation",
    "ValidationReport",
    # Validators
    "MusicValidator",
    "AutoCorrector",
]
