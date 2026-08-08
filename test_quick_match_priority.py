from datetime import datetime, timezone

from modules.quick_match.service import build_candidate_sort_key, quick_match_priority_group


def test_quick_match_priority_groups():
    assert quick_match_priority_group(same_rank=True, points_gap=2500) == 0
    assert quick_match_priority_group(same_rank=False, points_gap=300) == 1
    assert quick_match_priority_group(same_rank=False, points_gap=301) == 2
    assert quick_match_priority_group(same_rank=False, points_gap=500) == 2
    assert quick_match_priority_group(same_rank=False, points_gap=501) == 3
    assert quick_match_priority_group(same_rank=False, points_gap=1000) == 3
    assert quick_match_priority_group(same_rank=False, points_gap=1001) == 4
    assert quick_match_priority_group(same_rank=False, points_gap=2000) == 4
    assert quick_match_priority_group(same_rank=False, points_gap=2001) is None


def test_quick_match_sort_order_prefers_group_then_gap_then_activity():
    recent = datetime(2026, 7, 31, 2, 0, tzinfo=timezone.utc)
    older = datetime(2026, 7, 31, 1, 59, tzinfo=timezone.utc)
    group_300 = build_candidate_sort_key(priority_group=1, points_gap=300, last_seen=older, display_name='A')
    group_510 = build_candidate_sort_key(priority_group=3, points_gap=510, last_seen=recent, display_name='B')
    assert group_300 < group_510

    same_group_close = build_candidate_sort_key(priority_group=1, points_gap=100, last_seen=older, display_name='A')
    same_group_far = build_candidate_sort_key(priority_group=1, points_gap=200, last_seen=recent, display_name='B')
    assert same_group_close < same_group_far

    same_gap_recent = build_candidate_sort_key(priority_group=1, points_gap=100, last_seen=recent, display_name='B')
    assert same_gap_recent < same_group_close
