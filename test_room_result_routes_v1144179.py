from types import SimpleNamespace
import importlib


class FakeQuery:
    def __init__(self, table_name):
        self.table_name = table_name
        self.action = None
        self.payload = None
        self.filters = []

    def update(self, payload):
        self.action = "update"
        self.payload = dict(payload)
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self


class FakeDB:
    def table(self, table_name):
        return FakeQuery(table_name)


class FakeApp:
    def __init__(self):
        self.routes = {}

    def route(self, path, methods=None):
        def decorator(func):
            self.routes[(path, tuple(methods or ("GET",)))] = func
            return func
        return decorator


class FakeRequest:
    def __init__(self, form=None, files=None):
        self.form = form or {}
        self.files = files or {}


def make_common_context(*, current_user, room, match, form=None, files=None):
    app = FakeApp()
    flashes = []
    labels = []

    def execute_query(query, label, attempts=4, delay=0.25):
        del attempts, delay
        labels.append((label, query.table_name, query.action, query.payload, tuple(query.filters)))
        successful_labels = {
            "submit_room_match_result",
            "submit_room_result_state",
            "confirm_result_reset_room_waiting_ready",
            "match_dispute_update",
            "room_dispute_release_room",
        }
        return SimpleNamespace(data=[{"id": "row"}] if label in successful_labels else [])

    context = {
        "app": app,
        "login_required": lambda func: func,
        "current_user": lambda: dict(current_user),
        "get_room": lambda _room_id: dict(room),
        "get_match": lambda _match_id: dict(match),
        "is_admin_user": lambda user: user.get("role") == "admin",
        "flash": lambda message, category="message": flashes.append((category, message)),
        "redirect": lambda target: f"redirect:{target}",
        "url_for": lambda endpoint, **values: endpoint + (":" + str(values.get("room_id")) if values.get("room_id") else ""),
        "request": FakeRequest(form=form, files=files),
        "db": FakeDB(),
        "execute_query": execute_query,
        "assert_ranking_rebuild_not_running": lambda: None,
        "now_iso": lambda: "2026-08-03T09:00:00+00:00",
        "future_iso": lambda seconds: f"future:{seconds}",
        "RESULT_CONFIRM_TIMEOUT_SECONDS": 60,
        "ttl_cache_delete": lambda *_keys: None,
        "users_map": lambda: {},
        "apply_match_result": lambda _match: (25, -15),
        "build_win_streak_event": lambda *_args: None,
        "publish_global_streak_event": lambda *_args: False,
        "system_feature_enabled": lambda _key: True,
        "SMART_RANDOM_MODE": "Smart Tier Random",
        "FRIENDLY_RANDOM3_MODE": "random3_pick1",
        "MATCH_MODE_RANKED": "ranked",
        "_same_user_id": lambda a, b: str(a) == str(b),
        "dispute_reason_label": lambda code: {"wrong_score": "Sai tỷ số"}.get(code, code),
        "prepare_dispute_evidence_bytes": lambda _file: b"",
        "upload_dispute_evidence": lambda *_args: None,
        "remove_dispute_evidence_object": lambda *_args: None,
        "create_or_update_match_dispute": lambda *_args, **_kwargs: {"id": "d1"},
        "notify_admins": lambda *_args, **_kwargs: None,
        "create_user_notification": lambda *_args, **_kwargs: None,
        "get_match_dispute_by_match": lambda *_args, **_kwargs: None,
        "resolve_match_dispute_with_result": lambda *_args, **_kwargs: (25, -15),
        "DISPUTE_PENDING_STATUSES": {"open", "pending"},
    }
    return context, app, flashes, labels


def register(context):
    import modules.room_result_routes as routes
    routes = importlib.reload(routes)
    routes.register_routes(context)
    return routes


def test_host_can_submit_score_and_room_moves_to_waiting_confirmation():
    room = {
        "id": "r1", "host_user_id": "host", "guest_user_id": "guest",
        "status": "playing", "match_id": "m1",
    }
    match = {"id": "m1", "status": "playing"}
    context, app, flashes, labels = make_common_context(
        current_user={"id": "host", "role": "player"},
        room=room,
        match=match,
        form={"host_score": "3", "guest_score": "1"},
    )
    register(context)

    result = app.routes[("/room/<room_id>/submit-result", ("POST",))]("r1")

    assert result == "redirect:room_detail:r1"
    assert any(label == "submit_room_match_result" for label, *_ in labels)
    room_write = next(row for row in labels if row[0] == "submit_room_result_state")
    assert room_write[3]["status"] == "waiting_result_confirm"
    assert room_write[3]["host_score"] == 3
    assert room_write[3]["guest_score"] == 1
    assert any(category == "success" for category, _ in flashes)


def test_guest_can_confirm_and_room_returns_to_waiting_ready():
    room = {
        "id": "r1", "host_user_id": "host", "guest_user_id": "guest",
        "status": "waiting_result_confirm", "match_id": "m1",
        "team_tier": "Smart Tier Random",
    }
    match = {
        "id": "m1", "status": "waiting_confirm", "score1": 3, "score2": 1,
        "player1_id": "host", "player2_id": "guest",
    }
    context, app, flashes, labels = make_common_context(
        current_user={"id": "guest", "role": "player"}, room=room, match=match,
    )
    applied = []
    context["apply_match_result"] = lambda value: applied.append(value["id"]) or (25, -15)
    register(context)

    result = app.routes[("/room/<room_id>/confirm-result", ("POST",))]("r1")

    assert result == "redirect:room_detail:r1"
    assert applied == ["m1"]
    room_write = next(row for row in labels if row[0] == "confirm_result_reset_room_waiting_ready")
    assert room_write[3]["status"] == "waiting_ready"
    assert room_write[3]["match_id"] is None
    assert room_write[3]["confirmed_by_id"] == "guest"
    assert any(category == "success" for category, _ in flashes)


def test_host_cannot_confirm_guest_result_and_rp_is_not_called():
    room = {
        "id": "r1", "host_user_id": "host", "guest_user_id": "guest",
        "status": "waiting_result_confirm", "match_id": "m1",
    }
    match = {"id": "m1", "status": "waiting_confirm"}
    context, app, flashes, labels = make_common_context(
        current_user={"id": "host", "role": "player"}, room=room, match=match,
    )
    applied = []
    context["apply_match_result"] = lambda value: applied.append(value) or (25, -15)
    register(context)

    result = app.routes[("/room/<room_id>/confirm-result", ("POST",))]("r1")

    assert result == "redirect:room_detail:r1"
    assert applied == []
    assert labels == []
    assert any(category == "danger" for category, _ in flashes)


def test_guest_wrong_score_opens_dispute_without_applying_rp():
    room = {
        "id": "r1", "host_user_id": "host", "guest_user_id": "guest",
        "host_name": "Chủ", "guest_name": "Khách",
        "host_score": 3, "guest_score": 2, "submitted_by_id": "host",
        "status": "waiting_result_confirm", "match_id": "m1",
        "team_tier": "Smart Tier Random",
    }
    match = {"id": "m1", "status": "waiting_confirm"}
    context, app, flashes, labels = make_common_context(
        current_user={"id": "guest", "display_name": "Khách", "role": "player"},
        room=room,
        match=match,
        form={"reason_code": "wrong_score", "details": "Tỷ số đúng là 2-2"},
    )
    applied = []
    context["apply_match_result"] = lambda value: applied.append(value) or (25, -15)
    register(context)

    result = app.routes[("/room/<room_id>/dispute-result", ("POST",))]("r1")

    assert result == "redirect:room_detail:r1"
    assert applied == []
    assert any(label == "match_dispute_update" for label, *_ in labels)
    room_write = next(row for row in labels if row[0] == "room_dispute_release_room")
    assert room_write[3]["status"] == "waiting_ready"
    assert any(category == "warning" for category, _ in flashes)
