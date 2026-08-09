from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_global_gaming_skin_excludes_notification_owned_overlays():
    css = (ROOT / 'static/css/gaming_neon_buttons.css').read_text(encoding='utf-8')
    required = [
        ':not(.room-action-modal *)',
        ':not(.app-ui-dialog *)',
        ':not(.invite-modal *)',
        ':not(.invite-banner *)',
        ':not(.game-notice-modal *)',
    ]
    # Every selector branch that used the high-specificity Parsec exclusion must now
    # also exclude notification-owned overlays. This prevents default blue !important
    # rules from winning over modal tone rules.
    parsec_count = css.count(':not(#parsec-profile *)')
    assert parsec_count > 0
    for token in required:
        assert css.count(token) == parsec_count, (token, css.count(token), parsec_count)


def test_room_danger_modal_primary_cta_is_red_not_blue():
    css = (ROOT / 'static/css/notification_tones.css').read_text(encoding='utf-8')
    block_start = css.rfind('.room-action-modal[data-tone="danger"] .room-action-modal-button.primary{')
    assert block_start >= 0
    block = css[block_start:block_start + 500]
    assert '#ff6870' in block
    assert '#ff7880' in block
    assert '#c83d4b' in block
    assert '#29a8ff' not in block
    assert '#0d4f7a' not in block


def test_room_modal_tones_define_primary_cta_for_all_semantic_tones():
    css = (ROOT / 'static/css/notification_tones.css').read_text(encoding='utf-8')
    for tone in ('danger', 'warning', 'info'):
        assert f'.room-action-modal[data-tone="{tone}"] .room-action-modal-button.primary' in css
    assert '.room-action-modal[data-tone="success"] .room-action-modal-button.primary' in css
    assert '.room-action-modal[data-tone="safe"] .room-action-modal-button.primary' in css


def test_version_is_145():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'APP_VERSION = "1.4.5"' in app
