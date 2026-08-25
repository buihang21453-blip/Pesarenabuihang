from pathlib import Path

ROOT=Path(__file__).parent
ROOMS=[(ROOT/"templates/room_detail.html").read_text(encoding="utf-8"),(ROOT/"templates/_room_live_content.html").read_text(encoding="utf-8"),(ROOT/"templates/partials/room_dynamic_state.html").read_text(encoding="utf-8")]
CSS=(ROOT/"static/style.css").read_text(encoding="utf-8")
BASE=(ROOT/"templates/base.html").read_text(encoding="utf-8")

def test_room_center_timer_display_removed():
    for source in ROOMS:
        assert 'id="roomStartCountdown"' not in source
        assert 'Thời gian còn lại để bắt đầu' not in source
        assert 'Thời gian thi đấu' not in source

def test_invite_actions_are_centered():
    assert '.invite-modal-actions {' in CSS
    block=CSS.split('.invite-modal-actions {',1)[1].split('}',1)[0]
    assert 'justify-content: center' in block
    assert 'align-items: center' in block
    assert 'width: 100%' in block
    assert '<div class="invite-modal-actions">' in BASE
