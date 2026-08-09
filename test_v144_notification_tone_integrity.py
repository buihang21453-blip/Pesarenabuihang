from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_notification_tone_stylesheet_loaded_after_global_button_skin():
    base = (ROOT / 'templates/base.html').read_text(encoding='utf-8')
    neon = base.index("css/gaming_neon_buttons.css")
    tones = base.index("css/notification_tones.css")
    assert tones > neon


def test_room_modal_confirm_has_no_fixed_success_color_class():
    html = (ROOT / 'templates/room/_action_modal.html').read_text(encoding='utf-8')
    line = next(x for x in html.splitlines() if 'roomActionModalConfirm' in x)
    assert 'is-success' not in line
    assert ' green' not in line
    assert ' red' not in line
    assert ' gold' not in line
    assert 'primary' in line


def test_shared_dialog_confirm_has_no_legacy_color_class_assignment():
    js = (ROOT / 'static/js/ui_dialog.js').read_text(encoding='utf-8')
    assert "confirmButton.className = 'btn app-ui-dialog-confirm'" in js
    assert "tone === 'danger' ? 'red'" not in js


def test_canonical_tone_css_covers_all_popup_systems_and_tones():
    css = (ROOT / 'static/css/notification_tones.css').read_text(encoding='utf-8')
    required = [
        '.app-ui-dialog.tone-success', '.app-ui-dialog.tone-danger',
        '.app-ui-dialog.tone-warning', '.app-ui-dialog.tone-info',
        '.room-action-modal[data-tone="danger"]',
        '.room-action-modal[data-tone="safe"]',
        '.room-action-modal[data-tone="warning"]',
        '.room-action-modal[data-tone="info"]',
        '.invite-modal .invite-action-btn.is-accept',
        '.game-notice-modal.tone-success', '.game-notice-modal.tone-danger',
        '.game-notice-modal.tone-info', '.game-notice-modal.tone-warning',
    ]
    for selector in required:
        assert selector in css, selector


def test_room_modal_primary_tone_override_is_important():
    css = (ROOT / 'static/css/notification_tones.css').read_text(encoding='utf-8')
    block = css.split('.room-action-modal .room-action-modal-button.primary', 1)[1].split('}', 1)[0]
    assert 'border-color:var(--notice-accent)!important' in block
    assert 'background:linear-gradient' in block and '!important' in block
