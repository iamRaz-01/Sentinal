"""
Pydantic schemas and dataclasses for Module 1 (Data Ingestion).
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Set
from pydantic import BaseModel, Field, field_validator, model_validator


VALID_TRANSACTION_TYPES: Set[str] = {"transfer", "withdrawal", "deposit", "payment"}
VALID_CHANNELS: Set[str] = {"online", "atm", "pos", "mobile", "branch"}
VALID_STATUSES: Set[str] = {"pending", "completed", "reversed"}


class TransactionValidationError(ValueError):
    """Custom exception for transaction validation failures."""

    def __init__(self, message: str, errors: Optional[list] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []


class TransactionInput(BaseModel):
    """
    Raw input representation for an incoming transaction (API payload or CSV row).
    Validates types, required fields, and domain constraints.
    """

    sender_account_id: str = Field(..., description="ID/Account Number of sender")
    receiver_account_id: str = Field(..., description="ID/Account Number of receiver")
    amount: float = Field(..., description="Transaction amount, must be > 0")
    currency: str = Field(default="USD", max_length=3, description="3-letter currency code")
    transaction_type: str = Field(..., description="Type of transaction: transfer, withdrawal, deposit, payment")
    channel: str = Field(default="online", description="Channel used: online, atm, pos, mobile, branch")
    merchant_name: Optional[str] = Field(default=None, max_length=120)
    merchant_category_at_txn: Optional[str] = Field(default=None, max_length=60)
    device_fingerprint: Optional[str] = Field(default=None, max_length=120)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    occurred_at: Optional[datetime] = Field(default=None, description="ISO timestamp of when transaction occurred")
    timestamp: Optional[datetime] = Field(default=None, description="Alias for occurred_at")
    status: str = Field(default="completed", description="Status: completed, pending, reversed")

    @field_validator("sender_account_id", "receiver_account_id")
    @classmethod
    def validate_non_empty_string(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must be a non-empty string")
        return v.strip()

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be strictly positive (> 0)")
        return round(float(v), 2)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if len(v_upper) != 3:
            raise ValueError("currency must be a 3-letter ISO code")
        return v_upper

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        v_lower = v.strip().lower()
        if v_lower not in VALID_TRANSACTION_TYPES:
            raise ValueError(
                f"invalid transaction_type '{v}'. Must be one of: {sorted(list(VALID_TRANSACTION_TYPES))}"
            )
        return v_lower

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        v_lower = v.strip().lower()
        if v_lower not in VALID_CHANNELS:
            raise ValueError(f"invalid channel '{v}'. Must be one of: {sorted(list(VALID_CHANNELS))}")
        return v_lower

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v_lower = v.strip().lower()
        if v_lower not in VALID_STATUSES:
            raise ValueError(f"invalid status '{v}'. Must be one of: {sorted(list(VALID_STATUSES))}")
        return v_lower

    @model_validator(mode="after")
    def validate_sender_not_receiver(self) -> "TransactionInput":
        if self.sender_account_id == self.receiver_account_id:
            raise ValueError("sender_account_id and receiver_account_id must not be identical")
        
        # Consolidate timestamp / occurred_at
        if self.occurred_at is None and self.timestamp is not None:
            self.occurred_at = self.timestamp
        elif self.occurred_at is None and self.timestamp is None:
            self.occurred_at = datetime.now(timezone.utc)
            
        return self


class ValidatedTransaction(BaseModel):
    """
    Immutable validated transaction object passed downstream to Module 2.
    """

    sender_account_id: str
    receiver_account_id: str
    amount: float
    currency: str
    transaction_type: str
    channel: str
    merchant_name: Optional[str] = None
    merchant_category_at_txn: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    occurred_at: datetime
    status: str

    @classmethod
    def from_input(cls, input_obj: TransactionInput) -> "ValidatedTransaction":
        assert input_obj.occurred_at is not None
        return cls(
            sender_account_id=input_obj.sender_account_id,
            receiver_account_id=input_obj.receiver_account_id,
            amount=input_obj.amount,
            currency=input_obj.currency,
            transaction_type=input_obj.transaction_type,
            channel=input_obj.channel,
            merchant_name=input_obj.merchant_name,
            merchant_category_at_txn=input_obj.merchant_category_at_txn,
            device_fingerprint=input_obj.device_fingerprint,
            ip_address=input_obj.ip_address,
            occurred_at=input_obj.occurred_at,
            status=input_obj.status,
        )
