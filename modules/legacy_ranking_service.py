"""Legacy service extracted from app.py with behavior preserved.

The application injects its runtime dependencies through configure(context).
"""

EXPORTED_NAMES = ['_validate_rank_ranges', 'load_rank_ranges', 'get_rank_ranges', 'get_rank_info', 'is_goat_player', 'get_player_rank_info', 'get_rank_name', 'get_rank_display', 'get_team_power_score', 'get_tier_strength', 'get_match_difficulty', 'get_difficulty_factor', '_match_affects_streak', '_current_season_mechanics_start_iso', 'get_current_loss_streak', 'get_loss_recovery_win_step', 'calculate_deltas']

def configure(context):
    globals().update(context)

def _validate_rank_ranges(raw_ranges):
    """Validate the 10 rank definitions stored in system_settings."""
    if isinstance(raw_ranges, dict):
        raw_ranges = raw_ranges.get("ranks") or raw_ranges.get("value") or raw_ranges
    if not isinstance(raw_ranges, list) or len(raw_ranges) != 10:
        raise ValueError("Cấu hình khoảng điểm Rank phải có đúng 10 Rank.")

    normalized = []
    previous_max = -1
    required_text_fields = ("name", "short_name", "abbr", "code", "icon", "slug")
    for index, item in enumerate(raw_ranges):
        if not isinstance(item, dict):
            raise ValueError(f"Rank {index + 1} không đúng định dạng.")
        row = dict(item)
        minimum = int(row.get("min"))
        maximum_raw = row.get("max")
        maximum = None if maximum_raw in (None, "", "null") else int(maximum_raw)
        if index == 0 and minimum != 0:
            raise ValueError("Rank đầu tiên phải bắt đầu từ 0 RP.")
        if index > 0 and minimum != previous_max + 1:
            raise ValueError(f"Rank {index + 1} phải bắt đầu từ {previous_max + 1} RP.")
        if index < 9 and maximum is None:
            raise ValueError(f"Rank {index + 1} phải có điểm kết thúc.")
        if maximum is not None and maximum < minimum:
            raise ValueError(f"Khoảng điểm Rank {index + 1} không hợp lệ.")
        if index == 9 and maximum is not None:
            raise ValueError("Rank cuối cùng phải để max = null.")
        for field in required_text_fields:
            row[field] = str(row.get(field) or "").strip()
            if not row[field]:
                raise ValueError(f"Rank {index + 1} thiếu trường {field}.")
        row["min"] = minimum
        row["max"] = maximum
        normalized.append(row)
        previous_max = maximum if maximum is not None else previous_max
    return normalized


def load_rank_ranges(force=False):
    """Always load active Rank ranges from Supabase system_settings."""
    now = time.time()
    if not force and _rank_range_cache["value"] is not None and now < _rank_range_cache["expires_at"]:
        return _rank_range_cache["value"]
    if db is None:
        raise RuntimeError("Chưa cấu hình kết nối Supabase để đọc khoảng điểm Rank.")

    result = execute_query(
        db.table("system_settings").select("setting_value").eq("setting_key", RANK_RANGE_SETTING_KEY).limit(1),
        "load_rank_ranges",
        attempts=3,
    )
    if not result.data:
        # Tự tạo cấu hình lần đầu để không cần chạy hoặc lưu file SQL trên GitHub.
        execute_query(
            db.table("system_settings").upsert({
                "setting_key": RANK_RANGE_SETTING_KEY,
                "setting_value": DEFAULT_RANKS,
                "updated_at": now_iso(),
            }, on_conflict="setting_key"),
            "seed_rank_ranges",
            attempts=3,
        )
        configured = _validate_rank_ranges(DEFAULT_RANKS)
    else:
        stored = result.data[0].get("setting_value")
        if isinstance(stored, str):
            stored = json.loads(stored)
        configured = _validate_rank_ranges(stored)

    _rank_range_cache.update({"value": configured, "expires_at": now + 30})
    return configured


def get_rank_ranges():
    return load_rank_ranges()


def get_rank_info(points: int):
    ranks = load_rank_ranges()
    safe=max(0,int(points or 0)); selected=ranks[0]
    for rank in ranks:
        if safe>=rank["min"]: selected=rank
    result=dict(selected); nxt=next((r for r in ranks if r["min"]>safe),None)
    result["points"]=safe; result["next_rank"]=nxt
    result["points_to_next"]=max(0,nxt["min"]-safe) if nxt else 0
    if nxt:
        span=max(1,nxt["min"]-selected["min"]); result["progress"]=max(0,min(100,round(((safe-selected["min"])/span)*100)))
    else: result["progress"]=100
    return result


def is_goat_player(player, position=None):
    """GOAT is the official level 10 rank (2700+ RP)."""
    return bool(player) and get_rank_info(player.get("rank_points", 0)).get("code") == "GOAT"


def get_player_rank_info(player, position=None):
    return get_rank_info(player.get("rank_points", 0) if player else 0)


def get_rank_name(points:int)->str: return get_rank_info(points)["name"]


def get_rank_display(points:int)->str:
    r=get_rank_info(points); return f'{r["icon"]} {r["name"]}'


def get_team_power_score(team_name):
    """Đọc power_score của CLB trực tiếp từ bảng teams trên Supabase."""
    info = get_db_team_info(team_name) if team_name else None
    if info and info.get("power_score") is not None:
        try:
            return float(info.get("power_score"))
        except (TypeError, ValueError):
            pass
    return 73.33


def get_tier_strength(tier):
    """Return numeric club strength: D=1 ... S+=7."""
    values = {"D": 1, "C": 2, "B": 3, "A": 4, "A+": 5, "S": 6, "S+": 7}
    return values.get(str(tier or "").strip().upper(), 1)


def get_match_difficulty(player, opponent, player_tier, opponent_tier):
    """Combined rank gap and club compensation.

    Positive values mean the player's real matchup is harder; negative values
    mean the player has the easier matchup.
    """
    rank_gap = get_rank_level(opponent.get("rank_points", 0)) - get_rank_level(player.get("rank_points", 0))
    club_compensation = get_tier_strength(player_tier) - get_tier_strength(opponent_tier)
    return rank_gap - club_compensation


def get_difficulty_factor(difficulty, won):
    """Return the requested win/loss coefficient for one player."""
    difficulty = int(difficulty or 0)
    if difficulty >= 3:
        return 1.20 if won else 0.80
    if difficulty >= 1:
        return 1.10 if won else 0.90
    if difficulty <= -3:
        return 0.80 if won else 1.20
    if difficulty <= -1:
        return 0.90 if won else 1.10
    return 1.00


def _match_affects_streak(match):
    details = (match or {}).get("rp_details") or {}
    if not isinstance(details, dict):
        return True
    repeat = details.get("repeat_opponent") or {}
    return not (isinstance(repeat, dict) and repeat.get("streak_eligible") is False)


def _current_season_mechanics_start_iso():
    """Mốc bắt đầu Season hiện tại cho các cơ chế streak/recovery legacy."""
    if db is None:
        return None
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", "rank_season_current").limit(1),
            "current_season_mechanics_start", attempts=2,
        )
        value = ((result.data or [{}])[0].get("setting_value") or {}) if result.data else {}
        return value.get("started_at") or None
    except Exception as exc:
        print(f"current season mechanics warning: {type(exc).__name__}: {exc}")
        return None


def get_current_loss_streak(user_id):
    """Đếm số trận thua liên tiếp gần nhất từ lịch sử đã xác nhận."""
    if not user_id or db is None:
        return 0
    try:
        query = (db.table("matches")
            .select("player1_id,player2_id,score1,score2,status,created_at,rp_details")
            .or_(f"player1_id.eq.{user_id},player2_id.eq.{user_id}")
            .eq("status", "confirmed"))
        season_start = _current_season_mechanics_start_iso()
        if season_start:
            query = query.gte("created_at", season_start)
        result = execute_query(
            query.order("created_at", desc=True).limit(30),
            f"get_loss_streak:{user_id}", attempts=2,
        )
    except Exception as exc:
        print(f"get_current_loss_streak warning user={user_id}: {type(exc).__name__}: {exc}")
        return 0

    streak = 0
    for match in result.data or []:
        if not _match_affects_streak(match):
            continue
        score1 = _safe_int(match.get("score1"), -1)
        score2 = _safe_int(match.get("score2"), -1)
        if score1 < 0 or score2 < 0 or score1 == score2:
            break
        is_player1 = str(match.get("player1_id")) == str(user_id)
        lost = (is_player1 and score1 < score2) or ((not is_player1) and score2 < score1)
        if not lost:
            break
        streak += 1
    return streak


def get_loss_recovery_win_step(user_id):
    """Trả 1/2 nếu người chơi đang ở trận thắng phục hồi sau >=5 trận thua."""
    if not user_id or db is None:
        return 0
    try:
        query = (db.table("matches")
            .select("player1_id,player2_id,score1,score2,status,created_at,rp_details")
            .or_(f"player1_id.eq.{user_id},player2_id.eq.{user_id}")
            .eq("status", "confirmed"))
        season_start = _current_season_mechanics_start_iso()
        if season_start:
            query = query.gte("created_at", season_start)
        result = execute_query(
            query.order("created_at", desc=True).limit(30),
            f"get_loss_recovery:{user_id}", attempts=2,
        )
    except Exception as exc:
        print(f"get_loss_recovery warning user={user_id}: {type(exc).__name__}: {exc}")
        return 0
    outcomes = []
    for match in result.data or []:
        if not _match_affects_streak(match):
            continue
        s1, s2 = _safe_int(match.get("score1"), -1), _safe_int(match.get("score2"), -1)
        if s1 < 0 or s2 < 0 or s1 == s2:
            break
        is_p1 = str(match.get("player1_id")) == str(user_id)
        won = (is_p1 and s1 > s2) or ((not is_p1) and s2 > s1)
        outcomes.append("win" if won else "loss")
    recent_wins = 0
    for outcome in outcomes:
        if outcome != "win": break
        recent_wins += 1
    if recent_wins not in (0, 1):
        return 0
    prior_losses = 0
    for outcome in outcomes[recent_wins:]:
        if outcome != "loss": break
        prior_losses += 1
    return recent_wins + 1 if prior_losses >= 5 else 0


def calculate_deltas(player_a, player_b, score_a: int, score_b: int, team_a=None, team_b=None,
                     team_overall_a=None, team_overall_b=None, team_tier_a=None, team_tier_b=None,
                     rng=None):
    """Lớp tương thích: route cũ gọi như trước, công thức nằm trong rp_engine."""
    player_a_for_rp = dict(player_a or {})
    player_b_for_rp = dict(player_b or {})
    player_a_for_rp["loss_streak"] = get_current_loss_streak(player_a_for_rp.get("id"))
    player_b_for_rp["loss_streak"] = get_current_loss_streak(player_b_for_rp.get("id"))
    player_a_for_rp["loss_recovery_win_step"] = get_loss_recovery_win_step(player_a_for_rp.get("id"))
    player_b_for_rp["loss_recovery_win_step"] = get_loss_recovery_win_step(player_b_for_rp.get("id"))
    return calculate_ranked_deltas(
        player_a_for_rp, player_b_for_rp, score_a, score_b, get_rank_level=get_rank_level,
        team_a=team_a, team_b=team_b, team_overall_a=team_overall_a,
        team_overall_b=team_overall_b, team_tier_a=team_tier_a, team_tier_b=team_tier_b,
        rng=rng,
    )

