from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROOM = ROOT / 'static/css/room'
OWNER = ROOM / '15-room-actions-stability.css'
TEMPLATE = ROOT / 'templates/room_detail.html'

TOKENS = (
    'arena-btn', 'room-center-primary-actions', 'room-action-zone',
    'room-prestart', 'room-submit-result-btn', 'room-result-btn',
    'room-guest-card-kick-btn', 'arena-action-invite', 'arena-action-exit',
    'room-center-random-trigger', 'room-action-modal',
)


def test_action_owner_is_loaded_after_other_room_modules():
    html = TEMPLATE.read_text(encoding='utf-8')
    assert '15-room-actions-stability.css' in html
    assert html.index('14-shell-player-stability.css') < html.index('15-room-actions-stability.css')


def test_room_action_rules_have_one_room_owner():
    assert OWNER.exists()
    for css in ROOM.glob('*.css'):
        if css.name == OWNER.name:
            continue
        text = css.read_text(encoding='utf-8')
        # Check selector text only; custom-property names such as --room-prestart-*
        # on a non-action container are allowed.
        import re
        selectors = '\n'.join(m.group(1) for m in re.finditer(r'([^{}]+)\{', text) if not m.group(1).lstrip().startswith('@'))
        for token in TOKENS:
            assert token not in selectors, f'{token} still owned by {css.name}'


def test_shared_button_skin_stays_global():
    global_css = (ROOT / 'static/css/gaming_neon_buttons.css').read_text(encoding='utf-8')
    assert '--gn-role-success' in global_css
    assert '--gn-role-danger' in global_css
    assert '--gn-role-primary' in global_css
    assert '--gn-role-secondary' in global_css
