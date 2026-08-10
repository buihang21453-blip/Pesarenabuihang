from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_ready_flow_present_in_initial_and_live_room_templates():
    for rel in ["templates/room_detail.html", "templates/_room_live_content.html"]:
        text = read(rel)
        assert "room_guest_ready" in text
        assert "room_guest_unready" in text
        assert "room-neon-green" in text
        assert "Sẵn Sàng" in text


def test_ready_flow_fallback_partial_is_not_stale():
    text = read("templates/partials/room_dynamic_state.html")
    assert "room_guest_ready" in text
    assert "room_guest_unready" in text
    assert 'class="btn red room-center-action-btn"' not in text


def test_invite_action_layout_has_single_component_owner():
    base = read("templates/base.html")
    invites = read("templates/invites.html")
    css = read("static/css/components/invites.css")
    assert "css/components/invites.css" in base
    assert "invite-response-actions" in base
    assert "invite-response-actions" in invites
    assert "justify-content:center" in css


def test_room_neon_button_background_is_tinted_not_black_or_gradient():
    css = read("static/css/room/buttons.css")
    assert "background-color:rgba(var(--room-neon-rgb),.16)" in css
    assert "background-image:none" in css
    assert "linear-gradient" not in css
    assert "background-color:rgba(3,7,10" not in css
