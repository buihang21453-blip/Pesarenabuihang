"""Công tắc chế độ Rank thường / Random 3 chọn 1 cho PES Arena."""

from .service import (
    FEATURE_RANDOM3,
    FEATURE_RANK_STANDARD,
    enforce_valid_rank_features,
    effective_rank_mode,
    is_rank_standard_enabled,
    rank_mode_label,
)

__all__ = [
    "FEATURE_RANDOM3",
    "FEATURE_RANK_STANDARD",
    "enforce_valid_rank_features",
    "effective_rank_mode",
    "is_rank_standard_enabled",
    "rank_mode_label",
]
