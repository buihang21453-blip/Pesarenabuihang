"""Áp dụng kết quả, xử lý tranh chấp, cập nhật và hoàn tác thống kê/RP.

Module không khai báo route; dependency được liên kết khi app khởi động.
"""

import random

from modules.rp_engine import get_win_streak_bonus


def _safe_int(value, default=0):
    """Convert database/form values to int without depending on app.py globals.

    This helper intentionally lives in this module because match confirmation is a
    critical write path.  It must keep working even if service configure/import
    order changes while app.py is being modularized.
    """
    try:
        if value is None or value == "":
            return int(default)
        return int(value)
    except (TypeError, ValueError, OverflowError):
        try:
            return int(default)
        except (TypeError, ValueError, OverflowError):
            return 0

EXPORTED_NAMES = ['sync_room_after_admin_match_change', 'apply_match_result', 'resolve_match_dispute_with_result', 'cancel_match_dispute', 'update_player_after_match', 'reverse_player_match_stats', 'reverse_confirmed_match_result']

def configure(context):
    """Liên kết module với dependency hiện tại của ứng dụng."""
    globals().update(context)


def sync_room_after_admin_match_change(match, target, actor_id=None):
    """Đồng bộ đúng cột host_score/guest_score mà không sửa created_at."""
    if not match or not match.get("id"):
        return
    result = execute_query(
        db.table("match_rooms").select(
            "id,match_id,host_user_id,guest_user_id,status,host_score,guest_score,note,confirmed_by_id,state_expires_at"
        ).eq("match_id", match.get("id")).limit(1),
        "load_room_for_admin_match_sync",
        attempts=2,
    )
    room = (result.data or [None])[0]
    if not room:
        return

    status = str(target.get("status", match.get("status")) or "")
    score1 = target.get("score1", match.get("score1"))
    score2 = target.get("score2", match.get("score2"))
    p1_id = str(match.get("player1_id") or "")
    p2_id = str(match.get("player2_id") or "")
    host_id = str(room.get("host_user_id") or "")
    if host_id == p2_id:
        host_score, guest_score = score2, score1
    else:
        # Mặc định cấu trúc hiện hành: player1 là chủ phòng.
        host_score, guest_score = score1, score2

    room_payload = {
        "host_score": host_score,
        "guest_score": guest_score,
        "status": _room_status_from_match_status(status),
        "note": target.get("note", match.get("note")),
        "updated_at": now_iso(),
    }
    if status == "confirmed":
        room_payload["confirmed_by_id"] = target.get("confirmed_by_id") or actor_id
        room_payload["state_expires_at"] = None
    elif status == "waiting_confirm":
        room_payload["confirmed_by_id"] = None
        room_payload["state_expires_at"] = future_iso(RESULT_CONFIRM_TIMEOUT_SECONDS)
    elif status == "playing":
        room_payload["confirmed_by_id"] = None
        room_payload["state_expires_at"] = future_iso(ROOM_MATCH_INACTIVITY_TIMEOUT_SECONDS)
    else:
        room_payload["confirmed_by_id"] = None
        room_payload["state_expires_at"] = None

    execute_query(
        db.table("match_rooms").update(room_payload).eq("id", room.get("id")),
        "sync_room_after_admin_match_change",
        attempts=2,
    )


def _restore_player_snapshot(player):
    """Restore exactly the mutable ranked-stat fields from a pre-confirm snapshot."""
    if not player or not player.get("id"):
        return
    payload = {
        "rank_points": _safe_int(player.get("rank_points")),
        "wins": _safe_int(player.get("wins")),
        "draws": _safe_int(player.get("draws")),
        "losses": _safe_int(player.get("losses")),
        "total_matches": _safe_int(player.get("total_matches")),
        "goals_for": _safe_int(player.get("goals_for")),
        "goals_against": _safe_int(player.get("goals_against")),
        "streak": _safe_int(player.get("streak")),
    }
    execute_query(
        db.table("users").update(payload).eq("id", player["id"]),
        f"restore_player_snapshot:{player.get('id')}",
        attempts=2,
    )
    try:
        ttl_cache_delete("players_raw", "achievement_map", f"user:{player.get('id')}")
    except Exception:
        pass


def apply_match_result(match):
    """Luồng xác nhận RP cơ bản, dễ kiểm soát và idempotent theo trạng thái match.

    Chỉ làm 4 việc: đọc dữ liệu -> tính delta -> cập nhật 2 user -> chốt match.
    Không retry nhiều tầng, không sinh mã CONFIRM và không chạy các rule phụ trong
    đường ghi điểm chính. Các tác vụ phụ (thưởng tuần/badge) chỉ chạy sau khi chốt.
    """
    if not match or not match.get("id"):
        raise ValueError("Thiếu dữ liệu trận đấu.")

    fresh = get_match(match.get("id")) or match
    if fresh.get("status") == "confirmed" and fresh.get("delta1") is not None and fresh.get("delta2") is not None:
        return _safe_int(fresh.get("delta1")), _safe_int(fresh.get("delta2"))
    if fresh.get("status") == "processing_result":
        raise ValueError("Kết quả đang được xử lý. Hãy tải lại phòng sau vài giây.")
    if fresh.get("score1") is None or fresh.get("score2") is None:
        raise ValueError("Trận chưa có tỉ số.")

    assert_ranking_rebuild_not_running()

    player1_id = fresh.get("player1_id")
    player2_id = fresh.get("player2_id")
    if not player1_id or not player2_id:
        raise ValueError("Trận đấu thiếu người chơi.")

    player1 = get_user(player1_id)
    player2 = get_user(player2_id)
    if not player1 or not player2:
        raise ValueError("Không tìm thấy đủ dữ liệu hai người chơi.")

    score1 = _safe_int(fresh.get("score1"), -1)
    score2 = _safe_int(fresh.get("score2"), -1)
    if score1 < 0 or score2 < 0:
        raise ValueError("Tỉ số không hợp lệ.")

    original_status = str(fresh.get("status") or "waiting_confirm")
    claim = execute_query(
        db.table("matches").update({
            "status": "processing_result",
            "updated_at": now_iso(),
        }).eq("id", fresh["id"]).eq("status", original_status),
        "basic_claim_match_result",
        attempts=1,
    )
    if not (claim.data or []):
        latest = get_match(fresh["id"])
        if latest and latest.get("status") == "confirmed" and latest.get("delta1") is not None and latest.get("delta2") is not None:
            return _safe_int(latest.get("delta1")), _safe_int(latest.get("delta2"))
        raise ValueError("Trạng thái trận vừa thay đổi. Hãy tải lại phòng.")

    try:
        rng = random.Random(f"{RP_RANDOM_SEED_NAMESPACE}|{fresh.get('id')}")
        delta1, delta2 = calculate_deltas(
            player1, player2, score1, score2,
            fresh.get("team1"), fresh.get("team2"),
            fresh.get("team1_overall"), fresh.get("team2_overall"),
            fresh.get("team1_tier"), fresh.get("team2_tier"),
            rng=rng,
        )
        delta1, delta2 = validate_ranked_deltas(score1, score2, _safe_int(delta1), _safe_int(delta2))

        # Ghi thống kê/RP trực tiếp từ snapshot trước trận.
        update_player_after_match(player1, delta1, score1, score2, affect_streak=True)
        update_player_after_match(player2, delta2, score2, score1, affect_streak=True)

        original_note = str(fresh.get("note") or "")
        is_random3_pick1 = (
            "random 3 chọn 1" in original_note.casefold()
            or "random3_pick1" in original_note.casefold()
        )
        confirmed_note = "Đã xác nhận."
        if is_random3_pick1:
            confirmed_note += " [MODE:random3_pick1]"

        finalized = execute_query(
            db.table("matches").update({
                "delta1": int(delta1),
                "delta2": int(delta2),
                "rp_formula_version": RP_FORMULA_VERSION,
                "rp_details": {
                    "source": "basic_confirm_flow",
                    "seed": f"{RP_RANDOM_SEED_NAMESPACE}|{fresh.get('id')}",
                    "delta1": int(delta1),
                    "delta2": int(delta2),
                },
                "status": "confirmed",
                "note": confirmed_note,
                "updated_at": now_iso(),
            }).eq("id", fresh["id"]).eq("status", "processing_result"),
            "basic_finalize_match_result",
            attempts=1,
        )
        if not (finalized.data or []):
            raise RuntimeError("Không thể chốt kết quả trận đấu.")

    except Exception:
        # Rollback cơ bản chỉ dùng snapshot trước trận; không retry lồng nhau.
        for snapshot in (player1, player2):
            try:
                _restore_player_snapshot(snapshot)
            except Exception as rollback_exc:
                print(f"basic_result rollback user warning: {type(rollback_exc).__name__}: {rollback_exc}")
        try:
            execute_query(
                db.table("matches").update({
                    "status": original_status,
                    "updated_at": now_iso(),
                }).eq("id", fresh["id"]).eq("status", "processing_result"),
                "basic_restore_match_status",
                attempts=1,
            )
        except Exception as restore_exc:
            print(f"basic_result restore match warning: {type(restore_exc).__name__}: {restore_exc}")
        raise

    # Các tác vụ phụ không được phép làm hỏng xác nhận chính.
    try:
        grant_weekly_rp_rewards_for_users([player1_id, player2_id])
    except Exception as exc:
        print(f"weekly_rp_reward warning match={fresh.get('id')}: {type(exc).__name__}: {exc}")
    try:
        sync_achievements_for_users([player1_id, player2_id])
    except Exception as exc:
        print(f"achievement_sync warning match={fresh.get('id')}: {type(exc).__name__}: {exc}")

    return int(delta1), int(delta2)


def resolve_match_dispute_with_result(
    dispute,
    score1,
    score2,
    resolved_by_id,
    resolution_type,
    resolution_note="",
    final_dispute_status="resolved",
):
    if not dispute or dispute.get("status") not in DISPUTE_PENDING_STATUSES:
        raise ValueError("Tranh chấp này đã được xử lý hoặc không còn hiệu lực.")

    score1 = parse_score(score1)
    score2 = parse_score(score2)
    if score1 is None or score2 is None:
        raise ValueError("Trận được công nhận phải có đủ hai tỷ số.")

    match_id = dispute.get("match_id")
    lock_token = acquire_ranking_rebuild_lock(resolved_by_id, match_id)
    try:
        match = get_match(match_id)
        if not match or match.get("status") != "disputed":
            raise ValueError("Trận đấu không còn ở trạng thái tranh chấp.")

        final_note = (
            resolution_note or "Tranh chấp đã được xử lý và kết quả được công nhận."
        ).strip()[:500]
        override = {
            "score1": score1,
            "score2": score2,
            "status": "confirmed",
            "confirmed_by_id": resolved_by_id,
            "note": final_note,
        }
        rebuild_rankings_after_admin_change(
            match_id, override, lock_token=lock_token, actor_id=resolved_by_id
        )

        execute_query(
            db.table("match_disputes").update({
                "status": final_dispute_status,
                "resolution_type": resolution_type,
                "resolution_score1": score1,
                "resolution_score2": score2,
                "resolution_note": final_note,
                "resolved_by_id": resolved_by_id,
                "resolved_at": now_iso(),
                "updated_at": now_iso(),
            }).eq("id", dispute.get("id")).in_("status", list(DISPUTE_PENDING_STATUSES)),
            "finish_match_dispute_chronologically",
        )

        try:
            grant_weekly_rp_rewards_for_users([match.get("player1_id"), match.get("player2_id")])
        except Exception as exc:
            print(f"weekly_rp_reward dispute warning match={match_id}: {type(exc).__name__}: {exc}")

        resolved_match = get_match(match_id) or {}
        delta1 = _safe_int(resolved_match.get("delta1"))
        delta2 = _safe_int(resolved_match.get("delta2"))
        users = users_map()
        p1_name = users.get(match.get("player1_id"), {}).get("display_name", "Player 1")
        p2_name = users.get(match.get("player2_id"), {}).get("display_name", "Player 2")
        create_notifications_for_users(
            [match.get("player1_id"), match.get("player2_id")],
            "✅ Tranh chấp đã được xử lý",
            f"Trận {p1_name} {score1} - {score2} {p2_name}: {final_note}",
            f"/room/{dispute.get('room_id')}",
            "dispute_resolved",
        )
        return delta1, delta2
    finally:
        release_ranking_rebuild_lock(lock_token)


def cancel_match_dispute(dispute, resolved_by_id, resolution_note=""):
    if not dispute or dispute.get("status") not in DISPUTE_PENDING_STATUSES:
        raise ValueError("Tranh chấp này đã được xử lý hoặc không còn hiệu lực.")

    match = get_match(dispute.get("match_id"))
    if not match or match.get("status") != "disputed":
        raise ValueError("Trận đấu không còn ở trạng thái tranh chấp.")

    final_note = (resolution_note or "Admin đã hủy trận tranh chấp; không cộng hoặc trừ điểm.").strip()[:500]
    execute_query(
        db.table("matches").update({
            "status": "cancelled",
            "note": final_note,
            "updated_at": now_iso(),
        }).eq("id", match.get("id")),
        "cancel_disputed_match",
    )
    execute_query(
        db.table("match_rooms").update({
            "status": "cancelled",
            "note": final_note,
            "state_expires_at": None,
            "updated_at": now_iso(),
        }).eq("id", dispute.get("room_id")),
        "cancel_disputed_room",
    )
    execute_query(
        db.table("match_disputes").update({
            "status": "resolved",
            "resolution_type": "cancelled",
            "resolution_note": final_note,
            "resolved_by_id": resolved_by_id,
            "resolved_at": now_iso(),
            "updated_at": now_iso(),
        }).eq("id", dispute.get("id")),
        "cancel_match_dispute",
    )

    users = users_map()
    p1_name = users.get(match.get("player1_id"), {}).get("display_name", "Player 1")
    p2_name = users.get(match.get("player2_id"), {}).get("display_name", "Player 2")
    create_notifications_for_users(
        [match.get("player1_id"), match.get("player2_id")],
        "🚫 Trận tranh chấp đã bị hủy",
        f"Trận giữa {p1_name} và {p2_name} đã được Admin hủy. Không ai bị cộng hoặc trừ điểm.",
        "/matches",
        "dispute_cancelled",
    )


def update_player_after_match(player, delta, goals_for, goals_against, affect_streak=True):
    win = 1 if goals_for > goals_against else 0
    draw = 1 if goals_for == goals_against else 0
    loss = 1 if goals_for < goals_against else 0

    delta = _safe_int(delta)
    goals_for = _safe_int(goals_for)
    goals_against = _safe_int(goals_against)
    new_points = max(0, _safe_int(player.get("rank_points")) + delta)
    current_streak = int(player.get("streak", 0) or 0)
    if affect_streak:
        new_streak = current_streak + 1 if win else 0
    else:
        new_streak = current_streak

    new_wins = _safe_int(player.get("wins")) + win
    new_draws = _safe_int(player.get("draws")) + draw
    new_losses = _safe_int(player.get("losses")) + loss

    execute_query(
        db.table("users").update({
            "rank_points": new_points,
            "wins": new_wins,
            "draws": new_draws,
            "losses": new_losses,
            "total_matches": new_wins + new_draws + new_losses,
            "goals_for": _safe_int(player.get("goals_for")) + goals_for,
            "goals_against": _safe_int(player.get("goals_against")) + goals_against,
            "streak": new_streak,
        }).eq("id", player["id"]),
        f"update_player_after_match:{player.get('id')}",
    )
    try:
        ttl_cache_delete("players_raw", "achievement_map", f"user:{player.get('id')}")
    except Exception as exc:
        print(f"update_player_after_match cache warning user={player.get('id')}: {type(exc).__name__}: {exc}")




def reverse_player_match_stats(player, delta, goals_for, goals_against):
    """Hoàn tác đúng một trận đã áp dụng, không đụng tới dữ liệu người chơi khác."""
    if not player:
        return

    win = 1 if goals_for > goals_against else 0
    draw = 1 if goals_for == goals_against else 0
    loss = 1 if goals_for < goals_against else 0

    new_wins = max(0, int(player.get("wins", 0) or 0) - win)
    new_draws = max(0, int(player.get("draws", 0) or 0) - draw)
    new_losses = max(0, int(player.get("losses", 0) or 0) - loss)

    db.table("users").update({
        "rank_points": max(0, int(player.get("rank_points", 0) or 0) - int(delta or 0)),
        "wins": new_wins,
        "draws": new_draws,
        "losses": new_losses,
        "total_matches": new_wins + new_draws + new_losses,
        "goals_for": max(0, int(player.get("goals_for", 0) or 0) - int(goals_for or 0)),
        "goals_against": max(0, int(player.get("goals_against", 0) or 0) - int(goals_against or 0)),
        # Không thể suy ngược chính xác chuỗi thắng lịch sử nếu có trận mới hơn.
        # Đặt về 0 để tránh giữ chuỗi thắng sai sau khi Admin sửa/xóa trận.
        "streak": 0,
    }).eq("id", player["id"]).execute()


def reverse_confirmed_match_result(match):
    """Hoàn tác một trận confirmed bằng delta đã lưu, không reset toàn bộ BXH."""
    if not match or match.get("status") != "confirmed":
        return False
    if match.get("score1") is None or match.get("score2") is None:
        return False

    player1 = get_user(match.get("player1_id"))
    player2 = get_user(match.get("player2_id"))
    if not player1 or not player2:
        return False

    score1 = int(match.get("score1") or 0)
    score2 = int(match.get("score2") or 0)
    reverse_player_match_stats(player1, int(match.get("delta1", 0) or 0), score1, score2)
    reverse_player_match_stats(player2, int(match.get("delta2", 0) or 0), score2, score1)
    return True
