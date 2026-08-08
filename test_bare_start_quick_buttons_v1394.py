from pathlib import Path

ROOT = Path(__file__).resolve().parent
CENTER = (ROOT / "templates/room/_center_stage.html").read_text(encoding="utf-8")
LIVE = (ROOT / "templates/_room_live_content.html").read_text(encoding="utf-8")
JS = (ROOT / "static/js/quick_match.js").read_text(encoding="utf-8")
CSS_TEXT = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in (ROOT / "static/css").rglob("*.css"))
CSS_TEXT += "\n" + (ROOT / "static/style.css").read_text(encoding="utf-8")


def _series_button_slice(text):
    pos = text.index('data-bare-action="series-start"')
    return text[max(0, pos - 180):pos + 900]


def _quick_button_slice(text):
    pos = text.index('data-bare-action="quick-match"')
    return text[max(0, pos - 180):pos + 900]


def test_series_start_button_has_no_visual_classes_and_only_inline_bare_skin():
    for text in (CENTER, LIVE):
        chunk = _series_button_slice(text)
        assert 'class="btn' not in chunk
        assert 'arena-btn' not in chunk
        assert 'room-center-action-btn' not in chunk
        assert 'room-center-random-trigger' not in chunk
        assert 'all:unset!important' in chunk
        assert 'background:linear-gradient(180deg,#0d542f' in chunk
        assert 'box-shadow:inset 0 1px 0' in chunk
        assert 'border:1px solid #20d889!important' in chunk


def test_series_form_no_longer_uses_series_primary_form_wrapper():
    for text in (CENTER, LIVE):
        pos = text.index('data-bare-action="series-start"')
        before = text[max(0, pos - 1000):pos]
        assert 'series-primary-form room-prestart-mainform' not in before


def test_quick_match_button_has_no_visual_classes_and_only_inline_bare_skin():
    for text in (CENTER, LIVE):
        chunk = _quick_button_slice(text)
        assert 'class="btn' not in chunk
        assert 'arena-btn' not in chunk
        assert 'room-center-action-btn' not in chunk
        assert 'gaming-quick-action' not in chunk
        assert 'arena-action-quick' not in chunk
        assert 'all:unset!important' in chunk
        assert 'background:linear-gradient(180deg,#0d542f' in chunk
        assert 'box-shadow:inset 0 1px 0' in chunk
        assert 'border:1px solid #20d889!important' in chunk


def test_no_stylesheet_targets_bare_buttons_or_quick_match_hooks():
    for token in (
        'data-bare-action',
        'data-quick-match-url',
        'data-quick-match-icon',
        'data-quick-match-label',
        'gaming-quick-action',
        'arena-action-quick',
        'room-quick-match-btn',
        'quick-match-icon',
        'quick-match-label',
    ):
        assert token not in CSS_TEXT


def test_quick_match_js_uses_data_hooks_and_keeps_flow_hooks():
    assert "document.querySelector('[data-quick-match-url]')" in JS
    assert "button.querySelector('[data-quick-match-label]')" in JS
    assert "button.querySelector('[data-quick-match-icon]')" in JS
    assert "fetch(button.dataset.quickMatchUrl" in JS
