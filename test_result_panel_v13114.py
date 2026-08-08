from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = (ROOT / 'static/css/room/17-center-match-stability.css').read_text(encoding='utf-8')
CENTER = (ROOT / 'templates/room/_center_stage.html').read_text(encoding='utf-8')
APP = (ROOT / 'app.py').read_text(encoding='utf-8')


def test_version_bumped():
    assert 'APP_VERSION = "1.3.114"' in APP


def test_result_form_markup_still_complete():
    assert 'class="room-score-form room-center-score-form"' in CENTER
    assert 'name="host_score"' in CENTER
    assert 'name="guest_score"' in CENTER
    assert 'room-submit-result-btn' in CENTER


def test_desktop_result_panel_is_reserved_and_visible():
    assert 'padding-bottom:190px !important;' in CSS
    assert 'max-height:none !important;' in CSS
    assert 'overflow:visible !important;' in CSS
    assert '.room-center-score-panel .room-center-score-form' in CSS
    assert 'width:100% !important;' in CSS
