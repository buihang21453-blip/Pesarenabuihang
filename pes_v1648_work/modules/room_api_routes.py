"""Route extracted from app.py without changing endpoint behavior.

Dependencies are injected from the application context at registration time to
avoid circular imports and preserve the existing business logic.
"""

def register_routes(context):
    globals().update(context)

    @app.route("/api/active-room")
    @login_required

    def api_active_room():
        user = current_user()

        if not user or user.get("role") == "admin":
            return jsonify({"ok": True, "has_room": False})

        try:
            room = active_room_for_user(user["id"])
        except Exception:
            return jsonify({"ok": False, "has_room": False, "error": "temporary_db_error"}), 503

        if not room:
            return jsonify({"ok": True, "has_room": False})

        is_host = room.get("host_user_id") == user["id"]
        is_guest = room.get("guest_user_id") == user["id"]
        has_opponent = bool(room.get("guest_user_id"))

        # Chỉ ép quay lại khi trận đã bắt đầu hoặc đang chờ xác nhận.
        # Phòng trống/chờ sẵn sàng vẫn cho phép người dùng xem các trang khác.
        must_finish_statuses = {"playing", "friendly_playing", "waiting_result_confirm"}
        auto_redirect = bool(room.get("status") in must_finish_statuses and has_opponent)

        return jsonify({
            "ok": True,
            "has_room": True,
            "room_id": room["id"],
            "room_url": url_for("room_detail", room_id=room["id"]),
            "status": room.get("status"),
            "is_host": is_host,
            "is_guest": is_guest,
            "has_opponent": has_opponent,
            "auto_redirect": auto_redirect,
        })

    @app.route("/api/room/<room_id>/state")
    @login_required

    def api_room_state(room_id):
        user = current_user()

        try:
            room = get_room(room_id)
        except Exception:
            return jsonify({"ok": False, "error": "temporary_db_error"}), 503

        if not room:
            return polling_stop_response("room_not_found")

        if close_room_if_host_browser_offline(room):
            return polling_stop_response("host_browser_offline")

        if user["id"] not in [room["host_user_id"], room["guest_user_id"]] and not is_admin_user(user):
            return polling_stop_response("room_access_ended")

        # V1.6.24: while a scheduled GĐ2/KO match is waiting, ticket rerolls
        # must invalidate the room state key so both HLV see the new club.
        # Match already playing keeps the clubs captured when it started.
        note=str(room.get("note") or "")
        if note.startswith("TOURNAMENT_ROOM|") and str(room.get("status") or "")=="waiting_ready":
            try:
                import json
                meta=json.loads(note[len("TOURNAMENT_ROOM|"):])
                if (str(meta.get("stage_code") or "") in {"league","knockout"}
                        and not meta.get("test_sandbox_room")):
                    host=str(room.get("host_user_id") or "")
                    guest=str(room.get("guest_user_id") or "")
                    ids=[x for x in (host,guest) if x]
                    if ids:
                        result=execute_query(
                            db.table("tournament_members").select("user_id,fixed_club_name")
                            .eq("tournament_id",meta.get("tournament_id")).in_("user_id",ids),
                            "c1_fixed_polling_clubs",attempts=1,
                        )
                        clubs={str(r.get("user_id") or ""):r.get("fixed_club_name") for r in (getattr(result,"data",None) or [])}
                        room["host_team"]=clubs.get(host)
                        room["guest_team"]=clubs.get(guest)
            except Exception:
                app.logger.exception("C1 fixed-club polling failed room=%s",room_id)

        state_key = build_room_state_key(room)

        # V4.1: nếu trạng thái chưa đổi, trả response rỗng để giảm dữ liệu truyền.
        # Client vẫn giữ polling nhưng không phải nhận/phân tích JSON lặp lại.
        since_state_key = (request.args.get("since") or "").strip()
        if since_state_key and since_state_key == state_key:
            response = app.response_class(status=204)
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["X-Room-State-Unchanged"] = "1"
            return response

        rematch_declined_by_me = (
            (user["id"] == room.get("host_user_id") and room.get("rematch_host_declined"))
            or (user["id"] == room.get("guest_user_id") and room.get("rematch_guest_declined"))
        )

        return jsonify({
            "ok": True,
            "state_key": state_key,
            "status": room.get("status"),
            "guest_user_id": str(room.get("guest_user_id") or ""),
            "has_guest": bool(room.get("guest_user_id")),
            "updated_at": str(room.get("updated_at") or ""),
            "rematch_declined": bool(room.get("rematch_declined")),
            "rematch_declined_by_me": bool(rematch_declined_by_me),
            "rematch_expired": bool(room.get("rematch_expired")),
            "timeout_seconds": int(room.get("timeout_seconds") or 0),
            "timeout_label": room.get("timeout_label") or "",
        })

