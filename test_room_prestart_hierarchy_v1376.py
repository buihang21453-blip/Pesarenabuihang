from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_waiting_status_not_duplicated_in_current_room_templates():
    for path in ["templates/room/_center_stage.html", "templates/_room_live_content.html"]:
        text = read(path)
        assert "ĐỢI QUAY RANDOM ĐỘI" not in text
        assert "ĐỢI KHÁCH SẴN SÀNG" not in text
        assert "Đang chờ chủ phòng quay đội" not in text
        assert "Chờ đối thủ sẵn sàng" not in text
        assert "Đã đủ người" in text
        assert "room-prestart-flow-status" not in text


def test_legacy_dynamic_partial_does_not_restore_fake_waiting_button():
    text = read("templates/partials/room_dynamic_state.html")
    assert "ĐỢI QUAY RANDOM ĐỘI" not in text
    assert "ĐỢI KHÁCH SẴN SÀNG" not in text
    assert "room-prestart-flow-status" not in text


def test_all_series_modes_keep_orchestrator_path():
    text = read("templates/room/_center_stage.html") + read("templates/_room_live_content.html")
    for code in ["home_away", "bo3", "tactical_bo3", "ban_pick_bo3"]:
        assert code in text
    assert "room_series_start_next_game" in text
    assert "data-bare-action=\"series-start\"" in text


def test_invite_actions_use_synced_centered_style_everywhere():
    base = read("templates/base.html")
    page = read("templates/invites.html")
    js = read("static/js/invite_center.js")
    css = read("static/css/invite_center.css")
    for text in [base, page, js]:
        assert "invite-action-btn is-accept" in text
        assert "invite-action-btn is-reject" in text
    assert "justify-content:center" in css
    assert ".invite-action-btn.is-accept" in css
    assert ".invite-action-btn.is-reject" in css


def test_prestart_start_lane_and_action_dock_are_separate():
    css = read("static/css/room/10-prestart-flow.css")
    assert "V1.3.76 — pre-start hierarchy cleanup" in css
    room_detail = read("templates/room_detail.html")
    assert room_detail.index("09-series-orchestrator.css") < room_detail.index("10-prestart-flow.css")
    assert "bottom:calc(var(--room-prestart-dock-h) + 22px)" in css
    assert "padding-bottom:184px" in css
    assert "background:linear-gradient(180deg,rgba(5,13,25,.88),rgba(3,8,17,.94))" in css
