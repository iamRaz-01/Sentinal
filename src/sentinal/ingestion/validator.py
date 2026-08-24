"""
Validation and Ingestion Engine for Module 1 (Data Ingestion).
"""

from typing import Any, Dict, List, Tuple, Union
import pandas as pd
from pydantic import ValidationError

from .models import TransactionInput, ValidatedTransaction, TransactionValidationError


class IngestionBatchResult:
    """Encapsulates results of batch transaction ingestion."""

    def __init__(self, valid_records: List[ValidatedTransaction], errors: List[Dict[str, Any]]):
        self.valid_records = valid_records
        self.errors = errors

    @property
    def total_processed(self) -> int:
        return len(self.valid_records) + len(self.errors)

    @property
    def success_rate(self) -> float:
        if self.total_processed == 0:
            return 100.0
        return (len(self.valid_records) / self.total_processed) * 100.0


class TransactionIngestor:
    """
    Ingestor class that reads raw transaction data, validates structure & domain constraints,
    and returns ValidatedTransaction objects.
    """

    def validate_single(self, raw_data: Union[Dict[str, Any], TransactionInput]) -> ValidatedTransaction:
        """
        Validate a single transaction record (dictionary or Pydantic input).
        Raises TransactionValidationError if validation fails.
        """
        if isinstance(raw_data, TransactionInput):
            return ValidatedTransaction.from_input(raw_data)

        try:
            input_obj = TransactionInput(**raw_data)
            return ValidatedTransaction.from_input(input_obj)
        except ValidationError as ve:
            error_details = []
            for err in ve.errors():
                loc = " -> ".join(str(l) for l in err["loc"])
                error_details.append(f"{loc}: {err['msg']}")
            raise TransactionValidationError(
                f"Transaction validation failed: {'; '.join(error_details)}",
                errors=ve.errors(),
            ) from ve
        except Exception as e:
            raise TransactionValidationError(f"Unexpected validation error: {str(e)}") from e

    def validate_batch(
        self, records: List[Dict[str, Any]]
    ) -> IngestionBatchResult:
        """
        Validate a list of raw transaction records. Isolates invalid records while returning
        all valid ValidatedTransaction instances.
        """
        valid_records: List[ValidatedTransaction] = []
        errors: List[Dict[str, Any]] = []

        for idx, record in enumerate(records):
            try:
                valid_txn = self.validate_single(record)
                valid_records.append(valid_txn)
            except TransactionValidationError as err:
                errors.append({
                    "index": idx,
                    "record": record,
                    "error": str(err),
                    "details": err.errors
                })

        return IngestionBatchResult(valid_records=valid_records, errors=errors)

    def validate_csv(self, file_path: str) -> IngestionBatchResult:
        """
        Ingest and validate transactions directly from a CSV file.
        """
        df = pd.read_csv(file_path)
        # Convert NaN values to None for Pydantic compatibility
        records = df.where(pd.notnull(df), None).to_dict(orient="records")
        return self.validate_batch(records)
