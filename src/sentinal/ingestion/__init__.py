"""
Module 1 — Data Ingestion
Responsibilities: Read transactions from source (CSV/batch or simulated stream),
validate structural and domain constraints, and emit validated transaction objects.
"""

from .models import TransactionInput, ValidatedTransaction, TransactionValidationError
from .validator import TransactionIngestor, IngestionBatchResult

__all__ = [
    "TransactionInput",
    "ValidatedTransaction",
    "TransactionValidationError",
    "TransactionIngestor",
    "IngestionBatchResult",
]
