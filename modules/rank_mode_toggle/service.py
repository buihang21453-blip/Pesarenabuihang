"""Logic dùng chung cho hai công tắc chế độ thi đấu Rank.

Module không phụ thuộc Flask hoặc Supabase, vì vậy có thể dùng ở app.py,
route Admin, route phòng đấu và test độc lập.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

FEATURE_RANK_STANDARD = "rank_standard_enabled"
FEATURE_RANDOM3 = "friendly_random3_enabled"


def _flag(features: Mapping[str, Any] | None, key: str, default: bool = True) -> bool:
    if not features:
        return default
    value = features.get(key, default)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def is_rank_standard_enabled(features: Mapping[str, Any] | None) -> bool:
    return _flag(features, FEATURE_RANK_STANDARD, True)


def enforce_valid_rank_features(features: Mapping[str, Any]) -> dict[str, Any]:
    """Trả về bản sao hợp lệ.

    Nếu Rank thường bị tắt, Random 3 chọn 1 bắt buộc bật để người chơi vẫn
    còn một chế độ Rank. Hàm không thay đổi mapping đầu vào.
    """
    normalized = dict(features)
    if not is_rank_standard_enabled(normalized):
        normalized[FEATURE_RANDOM3] = True
    return normalized


def effective_rank_mode(
    requested_mode: str | None,
    features: Mapping[str, Any] | None,
    *,
    smart_random_mode: str = "smart_random",
    random3_mode: str = "random3_pick1",
) -> str:
    """Chuẩn hóa chế độ được yêu cầu theo công tắc hiện tại."""
    if not is_rank_standard_enabled(features):
        return random3_mode
    mode = (requested_mode or smart_random_mode).strip()
    return random3_mode if mode == random3_mode else smart_random_mode


def rank_mode_label(
    mode: str | None,
    features: Mapping[str, Any] | None,
    *,
    random3_mode: str = "random3_pick1",
) -> str:
    effective = effective_rank_mode(
        mode,
        features,
        random3_mode=random3_mode,
    )
    return "Random 3 chọn 1" if effective == random3_mode else "Rank thường"
