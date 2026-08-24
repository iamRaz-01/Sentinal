"""
Feature configuration and schema definitions for Module 2 (Feature Engineering).
Guarantees consistent feature names and column ordering between batch training and live scoring.
"""

from typing import List, Dict

CATEGORICAL_CATEGORIES: Dict[str, List[str]] = {
    "transaction_type": ["transfer", "withdrawal", "deposit", "payment"],
    "channel": ["online", "atm", "pos", "mobile", "branch"],
}

# Explicit order of output feature columns in feature vector
FEATURE_COLUMNS: List[str] = [
    # Numerical features
    "amount",
    "amount_log",
    # Temporal features
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_night",
    # One-hot encoded transaction_type
    "type_transfer",
    "type_withdrawal",
    "type_deposit",
    "type_payment",
    # One-hot encoded channel
    "channel_online",
    "channel_atm",
    "channel_pos",
    "channel_mobile",
    "channel_branch",
    # Aggregated account context features
    "sender_txn_count_24h",
    "sender_avg_amount_24h",
    "sender_amount_ratio_24h",
]
