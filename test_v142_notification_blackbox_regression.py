from pathlib import Path
ROOT = Path(__file__).resolve().parent


def test_v142_version():
    assert 'APP_VERSION = "1.4.2"' in (ROOT / 'app.py').read_text(encoding='utf-8')


def test_confirm_safe_int_is_local_and_used():
    src = (ROOT / 'modules/match_result_service.py').read_text(encoding='utf-8')
    assert 'def _safe_int(value, default=0):' in src
    assert 'phase = "calculate_deltas"' in src
    assert 'delta1, delta2 = _safe_int(delta1), _safe_int(delta2)' in src


def test_invite_primary_action_follows_pink_notice_tone():
    css = (ROOT / 'static/css/invite_center.css').read_text(encoding='utf-8')
    assert '.invite-action-btn.is-accept' in css
    assert 'rgba(224,56,126,.86)' in css
    assert '.invite-modal{' in css and '--invite-accent:#f2498f' in css
    # secondary reject must remain neutral rather than competing with primary action
    assert 'background:rgba(22,30,44,.82)!important' in css


def test_quick_notice_button_follows_tone():
    css = (ROOT / 'static/css/quick_match.css').read_text(encoding='utf-8')
    for tone in ('success', 'danger', 'info'):
        assert f'.game-notice-modal.tone-{tone} .game-notice-button' in css


def test_generic_dialog_owns_tone_and_primary_button():
    css = (ROOT / 'static/css/ui_dialog.css').read_text(encoding='utf-8')
    js = (ROOT / 'static/js/ui_dialog.js').read_text(encoding='utf-8')
    for tone in ('success', 'danger', 'warning', 'info'):
        assert f'.app-ui-dialog.tone-{tone}' in css
    assert "root.classList.add('tone-' + tone)" in js
    assert '[data-ui-dialog-confirm]' in css


def test_blackbox_does_not_mislabel_resource_errors_as_js_errors():
    src = (ROOT / 'static/js/blackbox.js').read_text(encoding='utf-8')
    assert "push('resource_error'" in src
    assert "target.tagName" in src
    assert "stack:e && e.error && e.error.stack" in src


def test_blackbox_navigation_fetch_failures_are_transient():
    src = (ROOT / 'static/js/blackbox.js').read_text(encoding='utf-8')
    assert 'let pageLeaving = false;' in src
    assert "push(transient ? 'network_cancelled' : 'api_error'" in src
    assert "window.addEventListener('beforeunload'" in src
