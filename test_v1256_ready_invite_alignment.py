from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(p): return (ROOT/p).read_text(encoding="utf-8")

def test_live_fragment_receives_viewer_aliases():
    live=read("templates/_room_live_content.html")
    dynamic=read("templates/partials/room_dynamic_state.html")
    for text in (live,dynamic):
        assert "{% set room_viewer_is_guest = viewer_is_guest|default(false) %}" in text
        assert "{% set room_room_viewer_is_host = viewer_is_host|default(false) %}" in text
    assert "url_for('room_guest_ready', room_id=room.id)" in live
    assert "url_for('room_guest_unready', room_id=room.id)" in live

def test_invite_actions_are_centered_by_component_owner():
    css=read("static/css/components/invites.css")
    assert ".invite-modal-actions{" in css
    assert "display:flex;" in css
    assert "justify-content:center;" in css
    assert "width:100%;" in css
    assert ".invite-modal-actions form{" in css
    assert "flex:0 0 auto;" in css
