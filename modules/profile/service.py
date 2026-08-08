"""Nghiệp vụ Hồ sơ cá nhân: ảnh đại diện và dữ liệu trang hồ sơ."""

import io
import uuid
from collections import Counter

from PIL import Image, ImageOps, UnidentifiedImageError

from . import equipment_service
from . import repository
from .equipment_service import build_equipment_state

AVATAR_BUCKET = "avatars"
AVATAR_MAX_BYTES = 2 * 1024 * 1024
AVATAR_OUTPUT_SIZE = 512
AVATAR_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def configure(context):
    globals().update(context)
    equipment_service.configure(context)


def _normalize_storage_public_url(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return (
            value.get("publicUrl")
            or value.get("public_url")
            or value.get("signedURL")
            or value.get("signed_url")
        )
    return str(value or "")


def prepare_avatar_bytes(file_storage):
    if not file_storage or not getattr(file_storage, "filename", ""):
        raise ValueError("Bạn chưa chọn ảnh đại diện.")

    raw = file_storage.read(AVATAR_MAX_BYTES + 1)
    if len(raw) > AVATAR_MAX_BYTES:
        raise ValueError("Ảnh đại diện không được vượt quá 2 MB.")
    if not raw:
        raise ValueError("File ảnh đang trống.")

    try:
        with Image.open(io.BytesIO(raw)) as probe:
            image_format = (probe.format or "").upper()
            width, height = probe.size
            probe.verify()
        if image_format not in AVATAR_ALLOWED_FORMATS:
            raise ValueError("Chỉ chấp nhận ảnh JPG, PNG hoặc WEBP.")
        if width < 80 or height < 80:
            raise ValueError("Ảnh quá nhỏ. Vui lòng chọn ảnh từ 80×80 pixel trở lên.")
        if width * height > 25_000_000:
            raise ValueError("Ảnh có độ phân giải quá lớn.")

        with Image.open(io.BytesIO(raw)) as source:
            source = ImageOps.exif_transpose(source).convert("RGB")
            avatar = ImageOps.fit(
                source,
                (AVATAR_OUTPUT_SIZE, AVATAR_OUTPUT_SIZE),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            output = io.BytesIO()
            avatar.save(output, format="WEBP", quality=86, method=6)
            return output.getvalue()
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise ValueError("File đã chọn không phải ảnh hợp lệ hoặc đã bị lỗi.")


def upload_avatar_to_storage(user_id, avatar_bytes):
    require_db()
    object_path = f"{user_id}/{uuid.uuid4().hex}.webp"
    bucket = db.storage.from_(AVATAR_BUCKET)
    bucket.upload(
        object_path,
        avatar_bytes,
        {
            "content-type": "image/webp",
            "cache-control": "31536000",
            "upsert": "false",
        },
    )
    public_url = _normalize_storage_public_url(bucket.get_public_url(object_path))
    if not public_url:
        try:
            bucket.remove([object_path])
        except Exception:
            pass
        raise RuntimeError("Không lấy được đường dẫn ảnh sau khi tải lên.")
    return object_path, public_url


def remove_avatar_object(object_path):
    if not object_path or db is None:
        return
    try:
        db.storage.from_(AVATAR_BUCKET).remove([object_path])
    except Exception as exc:
        print(f"profile remove_avatar_object warning: {exc}")


def build_profile_context(user_id, viewer):
    """Tổng hợp dữ liệu hiển thị hồ sơ mà không thay đổi hành vi cũ."""
    user = get_user(user_id)
    if not user:
        return None

    user = dict(user)
    # V1.3.34: chỉ SELECT trận của đúng người chơi, không tải toàn bộ bảng matches.
    player_matches_raw = load_user_matches(user_id, limit=50)
    matches = [decorate_match_for_view(match, user_id) for match in player_matches_raw[:10]]

    form = []
    for match in matches:
        is_ranked_result = match.get("status") == "confirmed"
        is_forfeit_loss = bool(match.get("is_forfeit") and match.get("result_code") == "loss")
        if not (is_ranked_result or is_forfeit_loss):
            continue
        form.append(match.get("result_code", "neutral"))
        if len(form) >= 5:
            break

    total = sum(int(user.get(key, 0) or 0) for key in ("wins", "draws", "losses"))
    user["total_matches"] = total
    wins = int(user.get("wins", 0) or 0)
    user["winrate"] = round((wins / total) * 100, 1) if total else 0
    user["goal_diff"] = int(user.get("goals_for", 0) or 0) - int(user.get("goals_against", 0) or 0)

    ranking_players = list_players()
    position = next((i for i, player in enumerate(ranking_players, 1) if player.get("id") == user_id), None)
    user["rank_info"] = get_player_rank_info(user, position)
    user["position"] = position
    decorate_player_achievements(user, position)
    user["is_online"] = is_user_online_now(user)

    # Favorite team / đối thủ thường gặp đã được Supabase cập nhật sau mỗi trận xác nhận.
    profile_summary = load_player_profile_summary(user_id) or {}
    user["favorite_team"] = profile_summary.get("favorite_team") or "Chưa có"
    frequent_opponent_id = profile_summary.get("frequent_opponent_id")
    frequent_opponent = get_user(frequent_opponent_id) if frequent_opponent_id else None
    user["frequent_opponent"] = (frequent_opponent or {}).get("display_name") or (frequent_opponent or {}).get("username") or "Chưa có"

    h2h = None
    if viewer.get("id") != user_id:
        viewer_id = viewer.get("id")
        pair = load_pair_stats(viewer_id, user_id) or {}
        recent_raw = load_h2h_matches(viewer_id, user_id, limit=5)
        h2h_matches = [decorate_match_for_view(match, viewer_id) for match in recent_raw]
        low_id = str(pair.get("user_low_id") or "")
        viewer_wins = int(pair.get("user_low_wins") or 0) if str(viewer_id) == low_id else int(pair.get("user_high_wins") or 0)
        target_wins = int(pair.get("user_high_wins") or 0) if str(viewer_id) == low_id else int(pair.get("user_low_wins") or 0)
        h2h = {
            "total": int(pair.get("total") or len(h2h_matches)),
            "wins": viewer_wins,
            "draws": int(pair.get("draws") or 0),
            "losses": target_wins,
            "recent": h2h_matches,
        }

    room_rows = list_rooms()
    activity = build_player_activity_map(rooms=room_rows).get(user_id)
    target_room = next((room for room in room_rows if str(user_id) in {str(room.get("host_user_id")), str(room.get("guest_user_id"))} and room_is_active(room)), None)
    viewer_room = next((room for room in room_rows if str(viewer.get("id")) in {str(room.get("host_user_id")), str(room.get("guest_user_id"))} and room_is_active(room)), None)
    target_available = bool(not activity or is_solo_waiting_room(target_room, user_id))
    viewer_available = bool(not viewer_room or is_solo_waiting_room(viewer_room, viewer.get("id")))
    can_invite = bool(
        viewer.get("id") != user_id
        and user.get("is_online")
        and target_available
        and viewer_available
        and not active_match_for_user(viewer.get("id"))
    )

    profile_active_room = active_room_for_user(viewer.get("id")) if viewer.get("id") == user_id else None
    display_name_ticket_count = repository.get_display_name_ticket_count(user_id) if viewer.get("id") == user_id else 0
    return {
        "player": user,
        "matches": matches,
        "form": form,
        "h2h": h2h,
        "can_invite": can_invite,
        "activity": activity,
        "profile_active_room": profile_active_room,
        "profile_equipment": build_equipment_state(user),
        "display_name_ticket_count": display_name_ticket_count,
    }
