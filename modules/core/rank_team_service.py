"""Module hóa từ V1.2.9.

Giữ nguyên logic gốc; dependency được truyền từ app.py bằng configure() để tránh import vòng.
"""

_CONTEXT = {}

def configure(context):
    _CONTEXT.clear()
    _CONTEXT.update(context)
    globals().update(context)

EXPORTED_NAMES = ['_validate_rank_ranges', 'load_rank_ranges', 'get_rank_ranges', 'get_rank_info', 'is_goat_player', 'get_player_rank_info', 'get_rank_name', 'get_rank_display', 'get_team_power_score', 'get_tier_strength', 'get_match_difficulty', 'get_difficulty_factor', '_match_affects_streak', 'get_current_loss_streak', 'get_loss_recovery_win_step', 'calculate_deltas', 'get_league_logo_url', 'power_score_to_tier', '_normalize_team_row', '_load_teams_from_supabase', 'get_random_team_pools', 'get_db_team_info', 'get_team_info', 'get_team_overall', 'get_team_tier', 'build_friendly_random3_state', 'encode_friendly_random3_state', 'decode_friendly_random3_state', 'get_rank_level', '_validate_rank_tier_weights', 'load_rank_tier_weights', 'get_rank_tier_weights', '_all_random_teams', '_normalize_team_name', '_is_random3_match', '_teams_in_tiers', '_weighted_tier_choice', '_nearest_rank_tier_candidates', '_pick_rank_team', 'get_smart_random_rule', 'smart_random_team_pair', 'get_available_team_tiers', 'friendly_random_team_pair']

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


def get_current_loss_streak(user_id):
    """Đếm số trận thua liên tiếp gần nhất từ lịch sử đã xác nhận."""
    if not user_id or db is None:
        return 0
    try:
        result = execute_query(
            db.table("matches")
            .select("player1_id,player2_id,score1,score2,status,created_at,rp_details")
            .or_(f"player1_id.eq.{user_id},player2_id.eq.{user_id}")
            .eq("status", "confirmed")
            .order("created_at", desc=True)
            .limit(30),
            f"get_loss_streak:{user_id}",
            attempts=2,
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
        result = execute_query(
            db.table("matches")
            .select("player1_id,player2_id,score1,score2,status,created_at,rp_details")
            .or_(f"player1_id.eq.{user_id},player2_id.eq.{user_id}")
            .eq("status", "confirmed")
            .order("created_at", desc=True)
            .limit(30),
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


def get_league_logo_url(league_name):
    """Tạo URL public tới team-logos/league-logos trên Supabase Storage."""
    import unicodedata
    raw = str(league_name or "").strip()
    if not raw or not supabase_url:
        return ""
    key = " ".join(raw.lower().replace("-", " ").replace("_", " ").split())
    key_ascii = "".join(ch for ch in unicodedata.normalize("NFKD", key) if not unicodedata.combining(ch))
    filename = LEAGUE_LOGO_FILES.get(key) or LEAGUE_LOGO_FILES.get(key_ascii)
    if not filename:
        for alias, candidate in LEAGUE_LOGO_FILES.items():
            if alias in key or alias in key_ascii:
                filename = candidate
                break
    if not filename:
        return ""
    from urllib.parse import quote
    object_path = f"{LEAGUE_LOGO_FOLDER}/{filename}"
    return f"{supabase_url}/storage/v1/object/public/{TEAM_LOGO_BUCKET}/{quote(object_path, safe='/')}"


def power_score_to_tier(power_score):
    """Classify one club into S+..D using power_score only."""
    try:
        score = float(power_score)
    except (TypeError, ValueError):
        return "D"
    for tier in CLUB_TIER_ORDER:
        minimum, maximum = CLUB_TIER_RANGES[tier]
        if minimum <= score <= maximum:
            return tier
    if score > CLUB_TIER_RANGES["S+"][1]:
        return "S+"
    return "D"


def _normalize_team_row(row):
    """Chuẩn hóa một dòng CLB lấy trực tiếp từ bảng teams trên Supabase."""
    if not row:
        return None
    name = row.get("team") or row.get("display")
    if not name:
        return None
    try:
        overall = int(row.get("overall") or 0)
    except (TypeError, ValueError):
        return None
    if overall <= 0:
        return None
    return {
        "id": row.get("id"),
        "display": str(name),
        "team": str(name),
        "league": row.get("league") or "",
        "overall": overall,
        "tier": str(row.get("tier") or power_score_to_tier(row.get("power_score"))).strip().upper(),
        "logo_file": row.get("logo_file") or "",
        "logo_url": row.get("logo_url") or "",
        "defence": row.get("defence"),
        "midfield": row.get("midfield"),
        "attack": row.get("attack"),
        "speed": row.get("speed"),
        "strength": row.get("strength"),
        "total_stats": row.get("total_stats"),
        "power_score": row.get("power_score"),
    }


def _load_teams_from_supabase(force=False):
    """Chỉ đọc CLB từ Supabase; không còn CSV hoặc teams_data.py dự phòng."""
    global TEAM_COUNT
    now = time.monotonic()
    if not force and _TEAM_CACHE["rows"] and now - _TEAM_CACHE["loaded_at"] < _TEAM_CACHE_TTL_SECONDS:
        return _TEAM_CACHE["rows"]
    if db is None:
        raise RuntimeError("Chưa cấu hình kết nối Supabase để đọc bảng teams.")
    result = execute_query(
        db.table("teams")
        .select("id,league,team,overall,defence,midfield,attack,speed,strength,total_stats,power_score,tier,logo_file,logo_url,is_active")
        .eq("is_active", True),
        "load_teams_from_supabase",
        attempts=3,
    )
    rows = []
    by_name = {}
    pools = {}
    for raw in result.data or []:
        team = _normalize_team_row(raw)
        if not team:
            continue
        rows.append(team)
        by_name[team["team"].casefold()] = team
        pools.setdefault(team["overall"], []).append(team)
    if not rows:
        raise RuntimeError("Bảng teams trên Supabase không có CLB hoạt động.")
    _TEAM_CACHE.update({"loaded_at": now, "rows": rows, "by_name": by_name, "pools": pools})
    TEAM_COUNT = len(rows)
    return rows


def get_random_team_pools():
    """Trả nhóm CLB theo overall, chỉ từ Supabase."""
    _load_teams_from_supabase()
    return _TEAM_CACHE["pools"]


def get_db_team_info(team_name):
    """Tìm CLB theo tên trong dữ liệu Supabase đã cache ngắn hạn."""
    if not team_name:
        return None
    try:
        _load_teams_from_supabase()
        return _TEAM_CACHE["by_name"].get(str(team_name).casefold())
    except Exception as exc:
        print(f"get_db_team_info error: {exc}")
        return None


def get_team_info(team_name):
    return get_db_team_info(team_name)


def get_team_overall(team_name):
    info = get_db_team_info(team_name)
    try:
        return int(info.get("overall")) if info else 0
    except (TypeError, ValueError):
        return 0


def get_team_tier(team_name):
    info = get_db_team_info(team_name)
    return str(info.get("tier") or "") if info else ""


def build_friendly_random3_state(host_player, guest_player):
    """Chia 3 CLB mỗi bên; tránh đội trong 5 trận gần nhất với đúng đối thủ."""
    if not host_player or not guest_player:
        raise ValueError("Không tải được thông tin Rank của hai người chơi.")

    all_teams = _all_random_teams()
    if len(all_teams) < 6:
        raise ValueError("Cần ít nhất 6 CLB để dùng Random 3 chọn 1.")

    picked_names = []
    selected_history = {
        "host": _recent_pair_team_names(host_player.get("id"), guest_player.get("id")),
        "guest": _recent_pair_team_names(guest_player.get("id"), host_player.get("id")),
    }

    def pack(team):
        return {
            "name": team.get("display"),
            "overall": int(team.get("overall") or 0),
            "total_stats": int(team.get("total_stats") or 0),
            "tier": str(team.get("tier") or "").strip().upper(),
            "logo": team.get("logo_url") or "",
            "league": team.get("league") or "",
        }

    def pick_three(player, side):
        options = []
        opponent_id = guest_player.get("id") if side == "host" else host_player.get("id")
        for _ in range(3):
            # picked_names là danh sách cấm cứng để 6 lựa chọn của hai bên
            # không bao giờ trùng nhau. Lịch sử đối đầu là danh sách cấm mềm:
            # hệ thống ưu tiên tránh, nhưng có thể nới khi pool Tier đã cạn.
            team, _, _, _ = _pick_rank_team(
                player,
                all_teams,
                extra_excluded=picked_names,
                opponent_id=opponent_id,
                include_pair_history=True,
            )
            name = team.get("display")
            picked_names.append(name)
            options.append(pack(team))
        return options

    host_level = get_rank_level(host_player.get("rank_points", 0))
    guest_level = get_rank_level(guest_player.get("rank_points", 0))
    rank_ranges = load_rank_ranges()

    host_options = pick_three(host_player, "host")
    guest_options = pick_three(guest_player, "guest")
    all_options = host_options + guest_options
    normalized_names = [_normalize_team_name(item.get("name")) for item in all_options]
    if len(all_options) != 6 or len(set(normalized_names)) != 6:
        raise ValueError("Không thể tạo 6 CLB khác nhau cho Random 3 chọn 1. Vui lòng thử lại.")

    return {
        "mode": FRIENDLY_RANDOM3_MODE,
        "distribution": "rank_weighted",
        "host_rank": rank_ranges[host_level]["name"],
        "guest_rank": rank_ranges[guest_level]["name"],
        "host_rank_points": int(host_player.get("rank_points") or 0),
        "guest_rank_points": int(guest_player.get("rank_points") or 0),
        "host_tier_weights": get_rank_tier_weights(host_level),
        "guest_tier_weights": get_rank_tier_weights(guest_level),
        "host_options": host_options,
        "guest_options": guest_options,
        "host_choice": None,
        "guest_choice": None,
    }


def encode_friendly_random3_state(state):
    return FRIENDLY_RANDOM3_NOTE_PREFIX + json.dumps(state, ensure_ascii=False, separators=(",", ":"))


def decode_friendly_random3_state(note):
    text = str(note or "")
    if not text.startswith(FRIENDLY_RANDOM3_NOTE_PREFIX):
        return None
    try:
        data = json.loads(text[len(FRIENDLY_RANDOM3_NOTE_PREFIX):])
        return data if data.get("mode") == FRIENDLY_RANDOM3_MODE else None
    except Exception:
        return None


def get_rank_level(points: int) -> int:
    """Return rank level from 0 (lowest) to 9 (highest)."""
    safe_points = max(0, int(points or 0))
    level = 0
    for index, rank in enumerate(load_rank_ranges()):
        if safe_points >= rank["min"]:
            level = index
    return level


def _validate_rank_tier_weights(raw_weights):
    """Validate imported 1..10 Rank mapping and convert it to internal 0..9 levels."""
    if not isinstance(raw_weights, dict):
        raise ValueError("RANK_CLUB_TIER_WEIGHTS phải là một dictionary.")

    normalized = {}
    for rank_number in range(1, len(load_rank_ranges()) + 1):
        row = raw_weights.get(rank_number)
        if row is None:
            row = raw_weights.get(str(rank_number))
        if not isinstance(row, dict) or not row:
            raise ValueError(f"Rank {rank_number} chưa có tỷ lệ Tier CLB.")

        clean_row = {}
        total = 0
        for tier, percent in row.items():
            tier = str(tier).strip().upper()
            if tier not in CLUB_TIER_ORDER:
                raise ValueError(f"Rank {rank_number} có Tier không hợp lệ: {tier}.")
            if isinstance(percent, bool) or not isinstance(percent, (int, float)):
                raise ValueError(f"Tỷ lệ {tier} của Rank {rank_number} phải là số.")
            percent = int(percent)
            if percent < 0 or percent > 100:
                raise ValueError(f"Tỷ lệ {tier} của Rank {rank_number} phải từ 0 đến 100.")
            if percent:
                clean_row[tier] = percent
                total += percent

        if total != 100:
            raise ValueError(f"Tổng tỷ lệ Rank {rank_number} đang là {total}%, bắt buộc phải bằng 100%.")
        normalized[rank_number - 1] = clean_row
    return normalized


def load_rank_tier_weights(force=False):
    now = time.time()
    if not force and _rank_tier_config_cache["value"] is not None and now < _rank_tier_config_cache["expires_at"]:
        return _rank_tier_config_cache["value"]

    configured = RANK_CLUB_TIER_WEIGHTS
    if db is not None:
        try:
            result = execute_query(
                db.table("system_settings").select("setting_value").eq("setting_key", RANK_TIER_SETTING_KEY).limit(1),
                "load_rank_tier_weights",
                attempts=2,
            )
            if result.data:
                stored = result.data[0].get("setting_value")
                if isinstance(stored, str):
                    stored = json.loads(stored)
                configured = _validate_rank_tier_weights(stored)
        except Exception as exc:
            print(f"load_rank_tier_weights fallback warning: {exc}")

    _rank_tier_config_cache.update({"value": configured, "expires_at": now + 30})
    return configured


def get_rank_tier_weights(level: int):
    """Return the active Admin-configured Tier percentages for one rank level."""
    safe_level = max(0, min(len(load_rank_ranges()) - 1, int(level or 0)))
    return load_rank_tier_weights().get(safe_level, RANK_CLUB_TIER_WEIGHTS[safe_level])


def _all_random_teams():
    pools = get_random_team_pools()
    teams = []
    for pool in pools.values():
        for team in pool:
            team = dict(team)
            try:
                team["power_score"] = float(team.get("power_score"))
            except (TypeError, ValueError):
                team["power_score"] = round(73.33 + (int(team.get("overall", 73)) - 73) * 0.75, 2)
            # Tier is always calculated from power_score, never trusted from stale CSV data.
            team["tier"] = power_score_to_tier(team["power_score"])
            teams.append(team)
    return teams


def _normalize_team_name(name):
    return " ".join(str(name or "").strip().casefold().split())


def _is_random3_match(match):
    note = str(match.get("note") or "").casefold()
    return "random 3 chọn 1" in note or FRIENDLY_RANDOM3_MODE in note


def _teams_in_tiers(teams, tiers, excluded_names=None):
    allowed = {str(tier).upper() for tier in (tiers or [])}
    excluded = {_normalize_team_name(name) for name in (excluded_names or []) if name}
    return [
        team for team in teams
        if str(team.get("tier") or "").upper() in allowed
        and _normalize_team_name(team.get("display")) not in excluded
    ]


def _weighted_tier_choice(tier_weights, teams, excluded_names):
    """Pick a Tier by configured percentage, then return clubs in that Tier.

    If a configured Tier has no available club after anti-repeat filtering,
    the remaining available percentages are automatically re-normalized.
    """
    available = []
    for tier, weight in (tier_weights or {}).items():
        candidates = _teams_in_tiers(teams, [tier], excluded_names)
        if candidates and float(weight or 0) > 0:
            available.append((tier, float(weight), candidates))
    if not available:
        return None, []

    roll = random.random() * sum(weight for _, weight, _ in available)
    cumulative = 0.0
    for tier, weight, candidates in available:
        cumulative += weight
        if roll <= cumulative:
            return tier, candidates
    tier, _, candidates = available[-1]
    return tier, candidates


def _nearest_rank_tier_candidates(tier_weights, teams, excluded_names):
    """Tìm CLB ở Tier gần nhất khi các Tier có tỷ lệ đã hết lựa chọn.

    Danh sách cấm vẫn được tôn trọng. Cơ chế này chỉ mở rộng sang Tier liền kề,
    tránh làm Random 3 chọn 1 thất bại khi một Rank chỉ được cấu hình 1 Tier
    nhưng Tier đó không đủ 6 CLB khác nhau cho cả hai người.
    """
    excluded = {_normalize_team_name(name) for name in (excluded_names or []) if name}
    available_by_tier = {}
    for team in teams:
        if _normalize_team_name(team.get("display")) in excluded:
            continue
        tier = str(team.get("tier") or "").upper()
        if tier in CLUB_TIER_ORDER:
            available_by_tier.setdefault(tier, []).append(team)

    preferred_indexes = [
        CLUB_TIER_ORDER.index(str(tier).upper())
        for tier, weight in (tier_weights or {}).items()
        if str(tier).upper() in CLUB_TIER_ORDER and float(weight or 0) > 0
    ]
    if not preferred_indexes:
        preferred_indexes = list(range(len(CLUB_TIER_ORDER)))

    ranked_tiers = []
    for tier, candidates in available_by_tier.items():
        tier_index = CLUB_TIER_ORDER.index(tier)
        distance = min(abs(tier_index - preferred) for preferred in preferred_indexes)
        ranked_tiers.append((distance, tier_index, tier, candidates))
    if not ranked_tiers:
        return None, []

    ranked_tiers.sort(key=lambda item: (item[0], item[1]))
    nearest_distance = ranked_tiers[0][0]
    nearest = [item for item in ranked_tiers if item[0] == nearest_distance]
    _, _, selected_tier, candidates = random.choice(nearest)
    return selected_tier, candidates


def _pick_rank_team(player, all_teams, extra_excluded=None, opponent_id=None, include_pair_history=True):
    level = get_rank_level(player.get("rank_points", 0))
    tier_weights = get_rank_tier_weights(level)
    recent = (
        _recent_pair_team_names(player.get("id"), opponent_id)
        if include_pair_history and opponent_id
        else []
    )
    # extra là danh sách cấm cứng (đội đã xuất hiện trong lượt hiện tại).
    # recent là danh sách cấm mềm (đội đã dùng trong lịch sử đối đầu gần đây).
    extra = list(extra_excluded or [])
    strict_excluded = list(dict.fromkeys(recent + extra))

    selected_tier, candidates = _weighted_tier_choice(tier_weights, all_teams, strict_excluded)
    if not candidates:
        selected_tier, candidates = _nearest_rank_tier_candidates(
            tier_weights, all_teams, strict_excluded
        )

    # Nếu lịch sử 5 trận làm cạn toàn bộ pool, nới riêng lịch sử nhưng vẫn
    # tuyệt đối không cho trùng đội trong 6 lựa chọn của lượt hiện tại.
    if not candidates and recent:
        selected_tier, candidates = _weighted_tier_choice(tier_weights, all_teams, extra)
        if not candidates:
            selected_tier, candidates = _nearest_rank_tier_candidates(
                tier_weights, all_teams, extra
            )

    if not candidates:
        raise ValueError(
            f"Không đủ CLB hoạt động để tạo lựa chọn cho rank {load_rank_ranges()[level]['name']}."
        )
    return random.choice(candidates), selected_tier, tier_weights, recent


def get_smart_random_rule(player_a, player_b):
    level_a = get_rank_level(player_a.get("rank_points", 0))
    level_b = get_rank_level(player_b.get("rank_points", 0))
    return {
        "level_a": level_a,
        "level_b": level_b,
        "rank_gap": abs(level_a - level_b),
        "advantage": "Mỗi Rank có tỷ lệ xuất hiện Tier CLB riêng.",
        "summary": "Random theo tỷ lệ Tier riêng; tránh CLB đã dùng trong 5 trận confirmed gần nhất với đúng đối thủ, dùng chung cả Rank thường và Random 3 chọn 1; hai bên không trùng CLB.",
        "rule_a": get_rank_tier_weights(level_a),
        "rule_b": get_rank_tier_weights(level_b),
    }


def smart_random_team_pair(player_a, player_b):
    """Random clubs from rank-linked S+..D tiers with anti-repeat protection."""
    all_teams = _all_random_teams()
    if len(all_teams) < 2:
        raise ValueError("Không đủ dữ liệu CLB để Smart Random.")

    team_a, tier_a_selected, weights_a, recent_a = _pick_rank_team(
        player_a, all_teams, opponent_id=player_b.get("id")
    )
    team_b, tier_b_selected, weights_b, recent_b = _pick_rank_team(
        player_b,
        all_teams,
        extra_excluded=[team_a.get("display")],
        opponent_id=player_a.get("id"),
    )

    if str(team_a.get("display")).casefold() == str(team_b.get("display")).casefold():
        allowed_b = set(weights_b.keys())
        excluded_b = {
            _normalize_team_name(name)
            for name in list(recent_b) + [team_a.get("display")]
            if name
        }
        alternatives = [
            team for team in all_teams
            if _normalize_team_name(team.get("display")) not in excluded_b
            and str(team.get("tier") or "").upper() in allowed_b
        ]
        if not alternatives:
            raise ValueError("Không tìm được hai CLB khác nhau trong các Tier phù hợp.")
        team_b = random.choice(alternatives)

    return {
        "mode": SMART_RANDOM_MODE,
        "team_a": team_a["display"],
        "team_b": team_b["display"],
        "overall_a": int(team_a["overall"]),
        "overall_b": int(team_b["overall"]),
        "total_stats_a": int(team_a.get("total_stats") or 0),
        "total_stats_b": int(team_b.get("total_stats") or 0),
        "power_score_a": float(team_a.get("power_score", 0)),
        "power_score_b": float(team_b.get("power_score", 0)),
        "tier_a": team_a["tier"],
        "tier_b": team_b["tier"],
        "logo_a": team_a.get("logo_url") or "",
        "logo_b": team_b.get("logo_url") or "",
        "league_a": team_a.get("league") or "",
        "league_b": team_b.get("league") or "",
        "team_id_a": team_a.get("id"),
        "team_id_b": team_b.get("id"),
        "band_a": tier_a_selected,
        "band_b": tier_b_selected,
        "recent_excluded_a": recent_a,
        "recent_excluded_b": recent_b,
        "rank_gap": abs(get_rank_level(player_a.get("rank_points", 0)) - get_rank_level(player_b.get("rank_points", 0))),
        "summary": get_smart_random_rule(player_a, player_b)["summary"],
    }


def get_available_team_tiers():
    """Return active club tiers for the friendly-mode selector."""
    tiers = []
    for team in _all_random_teams():
        tier = str(team.get("tier") or "").strip().upper()
        if tier and tier not in tiers:
            tiers.append(tier)
    preferred = CLUB_TIER_ORDER
    return sorted(tiers, key=lambda value: (preferred.index(value) if value in preferred else 99, value))


def friendly_random_team_pair(tier, excluded_names=None):
    """Pick two different active clubs from the selected tier; no history is created."""
    selected_tier = str(tier or "").strip().upper()
    if not selected_tier:
        raise ValueError("Hãy chọn Tier CLB cho trận giao hữu.")
    excluded = {str(name or "").casefold() for name in (excluded_names or []) if name}
    candidates = [
        team for team in _all_random_teams()
        if str(team.get("tier") or "").strip().upper() == selected_tier
        and _normalize_team_name(team.get("display")) not in excluded
    ]
    if len(candidates) < 2 and excluded:
        candidates = [
            team for team in _all_random_teams()
            if str(team.get("tier") or "").strip().upper() == selected_tier
        ]
    if len(candidates) < 2:
        raise ValueError(f"Tier {selected_tier} cần ít nhất 2 CLB khác nhau để đá giao hữu.")
    team_a, team_b = random.sample(candidates, 2)
    return {
        "mode": MATCH_MODE_FRIENDLY,
        "selected_tier": selected_tier,
        "team_a": team_a["display"],
        "team_b": team_b["display"],
        "overall_a": int(team_a["overall"]),
        "overall_b": int(team_b["overall"]),
        "total_stats_a": int(team_a.get("total_stats") or 0),
        "total_stats_b": int(team_b.get("total_stats") or 0),
        "power_score_a": float(team_a.get("power_score", 0)),
        "power_score_b": float(team_b.get("power_score", 0)),
        "tier_a": team_a.get("tier") or selected_tier,
        "tier_b": team_b.get("tier") or selected_tier,
        "logo_a": team_a.get("logo_url") or "",
        "logo_b": team_b.get("logo_url") or "",
        "league_a": team_a.get("league") or "",
        "league_b": team_b.get("league") or "",
    }

