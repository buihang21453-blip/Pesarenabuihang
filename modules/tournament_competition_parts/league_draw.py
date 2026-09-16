"""Pure GĐ2 draw: 16 active coaches, Tier sizes 5-6-5, four distinct opponents.

A validated four-round, four-regular fixture template ensures every coach faces
all three coach Tiers across four matches. Random independent permutations *within*
each Tier and shuffling rounds/pairs give varied, always-valid draws without a
retry limit or accidentally accepting a merely 'best effort' solution.
"""
import random

# Positions 1..5: Tier 1; 6..11: Tier 2; 12..16: Tier 3.
# Each of the 4 rows is a complete matching (8 games, all 16 positions once).
_TEMPLATE = (
    ((1, 4), (6, 12), (5, 8), (7, 10), (2, 3), (11, 14), (13, 16), (9, 15)),
    ((1, 8), (6, 10), (4, 12), (2, 14), (9, 11), (3, 13), (15, 16), (5, 7)),
    ((1, 11), (12, 14), (4, 10), (6, 8), (9, 13), (2, 15), (5, 16), (3, 7)),
    ((1, 12), (2, 9), (3, 5), (4, 6), (7, 15), (8, 13), (11, 16), (10, 14)),
)


def validate_four_match_draw(rounds, tier_by):
    """Raise ValueError unless the ENTIRE draw meets all hard constraints."""
    players = set(tier_by)
    if len(players) != 16 or [sum(t == n for t in tier_by.values()) for n in (1, 2, 3)] != [5, 6, 5]:
        raise ValueError('GĐ2 cần đúng 16 HLV active, chia Tier 5–6–5.')
    if len(rounds) != 4:
        raise ValueError('Lịch GĐ2 phải có đúng 4 lượt.')
    seen_pairs = set()
    opponents = {uid: set() for uid in players}
    opponent_tiers = {uid: set() for uid in players}
    for round_pairs in rounds:
        if len(round_pairs) != 8:
            raise ValueError('Mỗi lượt GĐ2 phải có đúng 8 trận.')
        seen_round = set()
        for a, b in round_pairs:
            if a == b or a not in players or b not in players or a in seen_round or b in seen_round:
                raise ValueError('Lịch GĐ2 có HLV sai hoặc thi đấu hai lần trong cùng lượt.')
            pair = frozenset((a, b))
            if pair in seen_pairs:
                raise ValueError('Lịch GĐ2 có cặp đối thủ bị trùng.')
            seen_pairs.add(pair)
            seen_round.update((a, b))
            opponents[a].add(b)
            opponents[b].add(a)
            opponent_tiers[a].add(tier_by[b])
            opponent_tiers[b].add(tier_by[a])
        if seen_round != players:
            raise ValueError('Một lượt GĐ2 chưa có đủ 16 HLV.')
    if len(seen_pairs) != 32 or any(len(opponents[uid]) != 4 or opponent_tiers[uid] != {1, 2, 3} for uid in players):
        raise ValueError('Lịch GĐ2 không đạt 32 trận, 4 đối thủ khác nhau và đủ 3 Tier cho từng HLV.')
    return True


def generate_four_match_draw(members, rng=None):
    """Return four shuffled 8-game matchings; no database side effects."""
    rng = rng if rng is not None else random.SystemRandom()
    groups = {tier: [] for tier in (1, 2, 3)}
    for member in members:
        uid = str(member.get('user_id') or '')
        try:
            tier = int(member.get('pot_no') or 0)  # legacy DB column = HLV Tier, NOT club Pot
        except (ValueError, TypeError):
            raise ValueError('Tier HLV không hợp lệ.') from None
        if not uid or tier not in groups:
            raise ValueError('Danh sách HLV hoặc Tier không hợp lệ.')
        groups[tier].append(uid)
    if [len(groups[tier]) for tier in (1, 2, 3)] != [5, 6, 5]:
        raise ValueError('GĐ2 cần đúng 16 HLV active, chia Tier 5–6–5.')
    slots = {}
    for tier, start in ((1, 1), (2, 6), (3, 12)):
        group = groups[tier][:]
        rng.shuffle(group)
        slots.update({start + index: uid for index, uid in enumerate(group)})
    tier_by = {uid: tier for tier, group in groups.items() for uid in group}
    if len(tier_by) != 16:
        raise ValueError('Danh sách GĐ2 có HLV trùng ID.')
    rounds = [[(slots[a], slots[b]) for a, b in template_round] for template_round in _TEMPLATE]
    rng.shuffle(rounds)
    for round_pairs in rounds:
        rng.shuffle(round_pairs)
        # Flip home/away independently without changing opponents.
        for i, (a, b) in enumerate(round_pairs):
            if rng.randrange(2):
                round_pairs[i] = (b, a)
    validate_four_match_draw(rounds, tier_by)
    return rounds
