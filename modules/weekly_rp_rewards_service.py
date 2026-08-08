"""Thưởng RP theo hoạt động tuần, mỗi mốc chỉ nhận một lần."""

from datetime import datetime, timedelta, timezone
import time

EXPORTED_NAMES = ["grant_weekly_rp_rewards_for_users", "get_weekly_rp_reward_config"]

WEEKLY_RP_REWARD_SETTING_KEY = "weekly_rp_reward_config"
DEFAULT_WEEKLY_RP_REWARD_CONFIG = {
    "opponents_5_threshold": 5,
    "opponents_5_rp": 20,
    "opponents_10_threshold": 10,
    "opponents_10_rp": 30,
    "opponents_20_threshold": 20,
    "opponents_20_rp": 50,
    "matches_threshold": 10,
    "matches_rp": 20,
}
_config_cache = {"value": None, "expires_at": 0.0}


def get_weekly_rp_reward_config(force_refresh=False):
    """Đọc cấu hình thưởng tuần từ system_settings, cache 30 giây."""
    if not force_refresh and _config_cache["value"] is not None and time.time() < _config_cache["expires_at"]:
        return dict(_config_cache["value"])
    config = dict(DEFAULT_WEEKLY_RP_REWARD_CONFIG)
    try:
        result = execute_query(
            db.table("system_settings").select("setting_value")
            .eq("setting_key", WEEKLY_RP_REWARD_SETTING_KEY).limit(1),
            "get_weekly_rp_reward_config",
            attempts=2,
        )
        rows = list(result.data or [])
        stored = (rows[0].get("setting_value") or {}) if rows else {}
        for key, default in DEFAULT_WEEKLY_RP_REWARD_CONFIG.items():
            config[key] = _safe_int(stored.get(key), default)
    except Exception as exc:
        print(f"weekly reward config warning: {type(exc).__name__}: {exc}")
    _config_cache["value"] = dict(config)
    _config_cache["expires_at"] = time.time() + 30
    return config


def _reward_rules(config):
    return (
        ("opponents_5", f"Gặp {config['opponents_5_threshold']} đối thủ khác nhau trong tuần", config["opponents_5_rp"]),
        ("opponents_10", f"Gặp {config['opponents_10_threshold']} đối thủ khác nhau trong tuần", config["opponents_10_rp"]),
        ("opponents_20", f"Gặp {config['opponents_20_threshold']} đối thủ khác nhau trong tuần", config["opponents_20_rp"]),
        ("matches_10", f"Hoàn thành {config['matches_threshold']} trận trong tuần", config["matches_rp"]),
    )


def configure(context):
    globals().update(context)


def _safe_int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _week_bounds_vn(now=None):
    vn_tz = timezone(timedelta(hours=7))
    current = now.astimezone(vn_tz) if now else datetime.now(vn_tz)
    start = (current - timedelta(days=current.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(days=7)
    return start, end


def _load_week_activity(user_id, week_start, week_end):
    result = execute_query(
        db.table("matches")
        .select("id,player1_id,player2_id,status,created_at")
        .eq("status", "confirmed")
        .gte("created_at", week_start.isoformat())
        .lt("created_at", week_end.isoformat())
        .or_(f"player1_id.eq.{user_id},player2_id.eq.{user_id}"),
        f"weekly_rp_activity:{user_id}",
        attempts=2,
    )
    rows = list(result.data or [])
    opponents = set()
    for row in rows:
        p1 = str(row.get("player1_id") or "")
        p2 = str(row.get("player2_id") or "")
        opponent_id = p2 if p1 == str(user_id) else p1
        if opponent_id and opponent_id != str(user_id):
            opponents.add(opponent_id)
    return len(rows), len(opponents)


def _claim_and_apply_reward(user_id, week_start, reward_code, reward_name, reward_rp):
    """Claim bằng unique key trước, sau đó cộng RP; rollback claim nếu cộng thất bại."""
    claim_payload = {
        "user_id": user_id,
        "week_start": week_start.date().isoformat(),
        "reward_code": reward_code,
        "reward_name": reward_name,
        "reward_rp": int(reward_rp),
        "created_at": now_iso(),
    }
    try:
        claim = execute_query(
            db.table("weekly_rp_rewards").insert(claim_payload),
            f"claim_weekly_rp_reward:{user_id}:{reward_code}",
            attempts=1,
        )
    except Exception as exc:
        # Unique violation nghĩa là mốc đã nhận; không coi là lỗi hệ thống.
        text = str(exc).casefold()
        if "duplicate" in text or "unique" in text or "23505" in text:
            return 0
        raise

    claim_row = (claim.data or [{}])[0]
    claim_id = claim_row.get("id")
    try:
        user = get_user(user_id)
        if not user:
            raise ValueError("Không tìm thấy người chơi để cộng thưởng tuần.")
        new_rp = max(0, _safe_int(user.get("rank_points")) + int(reward_rp))
        execute_query(
            db.table("users").update({
                "rank_points": new_rp,
                "updated_at": now_iso(),
            }).eq("id", user_id),
            f"apply_weekly_rp_reward:{user_id}:{reward_code}",
            attempts=2,
        )
        create_user_notification(
            user_id,
            "🎁 Thưởng hoạt động tuần",
            f"{reward_name}: +{int(reward_rp)} RP.",
            "/notifications",
            "weekly_rp_reward",
        )
        ttl_cache_delete("players_raw", "achievement_map")
        return int(reward_rp)
    except Exception:
        try:
            query = db.table("weekly_rp_rewards").delete()
            query = query.eq("id", claim_id) if claim_id else (
                query.eq("user_id", user_id)
                .eq("week_start", week_start.date().isoformat())
                .eq("reward_code", reward_code)
            )
            execute_query(query, "rollback_weekly_rp_reward_claim", attempts=1)
        except Exception as rollback_exc:
            print(f"weekly reward rollback warning: {rollback_exc}")
        raise


def grant_weekly_rp_rewards_for_users(user_ids):
    """Kiểm tra và cộng tất cả mốc tuần vừa đạt cho danh sách người chơi."""
    week_start, week_end = _week_bounds_vn()
    config = get_weekly_rp_reward_config()
    awarded = {}
    for raw_user_id in dict.fromkeys(user_ids or []):
        user_id = str(raw_user_id or "").strip()
        if not user_id:
            continue
        try:
            match_count, opponent_count = _load_week_activity(user_id, week_start, week_end)
            eligible_codes = set()
            if match_count >= config["matches_threshold"]:
                eligible_codes.add("matches_10")
            if opponent_count >= config["opponents_5_threshold"]:
                eligible_codes.add("opponents_5")
            if opponent_count >= config["opponents_10_threshold"]:
                eligible_codes.add("opponents_10")
            if opponent_count >= config["opponents_20_threshold"]:
                eligible_codes.add("opponents_20")

            total = 0
            for code, name, rp in _reward_rules(config):
                if code in eligible_codes:
                    total += _claim_and_apply_reward(user_id, week_start, code, name, rp)
            if total:
                awarded[user_id] = {
                    "rp": total,
                    "matches": match_count,
                    "different_opponents": opponent_count,
                }
        except Exception as exc:
            print(f"weekly_rp_reward warning user={user_id}: {type(exc).__name__}: {exc}")
    return awarded
