"""
Feature Engineering Pipeline for Module 2.
Transforms ValidatedTransaction objects into numeric feature vectors ready for model scoring.
"""

from datetime import timedelta
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd

from sentinal.ingestion.models import ValidatedTransaction
from .config import CATEGORICAL_CATEGORIES, FEATURE_COLUMNS


class FeaturePipeline:
    """
    Transforms validated transaction data into feature vectors.
    Ensures identical transformation logic between single-transaction online scoring
    and batch dataset offline feature computation.
    """

    def __init__(self, feature_columns: Optional[List[str]] = None):
        self.feature_columns = feature_columns or FEATURE_COLUMNS

    def transform_single(
        self,
        txn: ValidatedTransaction,
        history: Optional[List[ValidatedTransaction]] = None,
    ) -> pd.DataFrame:
        """
        Transform a single ValidatedTransaction into a 1-row DataFrame containing feature vector.
        """
        row = self._compute_features_dict(txn, history=history)
        df = pd.DataFrame([row])
        return df[self.feature_columns]

    def transform_batch(
        self,
        txns: List[ValidatedTransaction],
        compute_rolling_history: bool = True,
    ) -> pd.DataFrame:
        """
        Transform a list of ValidatedTransaction objects into a Multi-row DataFrame feature vector.
        If compute_rolling_history is True, rolling 24h history per sender account is computed
        across the ordered batch of transactions.
        """
        if not txns:
            return pd.DataFrame(columns=self.feature_columns)

        # Sort transactions by occurred_at for sequential history calculations
        sorted_txns = sorted(txns, key=lambda t: t.occurred_at)

        rows = []
        for idx, txn in enumerate(sorted_txns):
            history_slice = sorted_txns[:idx] if compute_rolling_history else None
            row = self._compute_features_dict(txn, history=history_slice)
            rows.append(row)

        df = pd.DataFrame(rows)
        return df[self.feature_columns]

    def _compute_features_dict(
        self,
        txn: ValidatedTransaction,
        history: Optional[List[ValidatedTransaction]] = None,
    ) -> Dict[str, Union[int, float]]:
        """
        Compute underlying numeric feature values for a single transaction.
        """
        # 1. Base numeric features
        amount = float(txn.amount)
        amount_log = float(np.log1p(amount))

        # 2. Temporal features
        dt = txn.occurred_at
        hour_of_day = int(dt.hour)
        day_of_week = int(dt.weekday())  # 0=Mon, 6=Sun
        is_weekend = 1 if day_of_week >= 5 else 0
        is_night = 1 if (hour_of_day >= 22 or hour_of_day <= 5) else 0

        feature_dict: Dict[str, Union[int, float]] = {
            "amount": amount,
            "amount_log": amount_log,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "is_night": is_night,
        }

        # 3. Categorical one-hot encoding for transaction_type
        for t_type in CATEGORICAL_CATEGORIES["transaction_type"]:
            feature_dict[f"type_{t_type}"] = 1 if txn.transaction_type == t_type else 0

        # 4. Categorical one-hot encoding for channel
        for ch in CATEGORICAL_CATEGORIES["channel"]:
            feature_dict[f"channel_{ch}"] = 1 if txn.channel == ch else 0

        # 5. Account history context (past 24h aggregated features)
        if history:
            window_start = dt - timedelta(hours=24)
            sender_past_txns = [
                h for h in history
                if h.sender_account_id == txn.sender_account_id
                and window_start <= h.occurred_at < dt
            ]
            sender_txn_count_24h = len(sender_past_txns)
            if sender_past_txns:
                sender_avg_amount_24h = float(np.mean([h.amount for h in sender_past_txns]))
                sender_amount_ratio_24h = float(amount / max(sender_avg_amount_24h, 1e-4))
            else:
                sender_avg_amount_24h = amount
                sender_amount_ratio_24h = 1.0
        else:
            sender_txn_count_24h = 0
            sender_avg_amount_24h = amount
            sender_amount_ratio_24h = 1.0

        feature_dict["sender_txn_count_24h"] = sender_txn_count_24h
        feature_dict["sender_avg_amount_24h"] = sender_avg_amount_24h
        feature_dict["sender_amount_ratio_24h"] = sender_amount_ratio_24h

        return feature_dict
