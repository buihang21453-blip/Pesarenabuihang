"""Pure ranking helpers for the Quick Match flow.

The HTTP route remains in app.py because it currently depends on the app's
session, room, invitation and Supabase helpers. Selection policy is isolated
here so it can be tested and changed without touching the route.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple


def quick_match_priority_group(*, same_rank: bool, points_gap: int) -> Optional[int]:
    """Return the configured priority bucket or ``None`` when ineligible.

    Priority order:
      0. Same rank tier
      1. Different tier, gap <= 300
      2. Different tier, gap <= 500
      3. Different tier, gap <= 1000
      4. Different tier, gap <= 2000
    """
    gap = max(0, int(points_gap or 0))
    if same_rank:
        return 0
    if gap <= 300:
        return 1
    if gap <= 500:
        return 2
    if gap <= 1000:
        return 3
    if gap <= 2000:
        return 4
    return None


def build_candidate_sort_key(
    *,
    priority_group: int,
    points_gap: int,
    last_seen: datetime,
    display_name: str,
) -> Tuple[int, int, float, str]:
    """Sort by group, RP distance, recent activity, then stable name."""
    return (
        int(priority_group),
        max(0, int(points_gap or 0)),
        -float(last_seen.timestamp()),
        str(display_name or "").casefold(),
    )
