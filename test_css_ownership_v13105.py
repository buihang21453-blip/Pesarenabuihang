from pathlib import Path
import re
ROOT = Path(__file__).resolve().parent
ROOM = ROOT / 'static/css/room'
OWNER = ROOM / '16-side-rail-history-stability.css'
TEMPLATE = ROOT / 'templates/room_detail.html'
TOKENS = (
    'room-arena-right-rail','room-side-rail','room-side-info-panel','room-side-info-list',
    'room-chat-side','parsec-room-panel','parsec-room-','room-bottom-shell',
    'room-bottom-side','room-history-full','room-session-h2h','room-score-history-',
    'room-session-empty','room-score-value','room-score-separator',
)

def selector_text(path: Path) -> str:
    text = path.read_text(encoding='utf-8')
    return '\n'.join(m.group(1) for m in re.finditer(r'([^{}]+)\{', text) if not m.group(1).lstrip().startswith('@'))

def test_owner_loaded_last_in_room_chain():
    html = TEMPLATE.read_text(encoding='utf-8')
    assert '16-side-rail-history-stability.css' in html
    assert html.index('15-room-actions-stability.css') < html.index('16-side-rail-history-stability.css')

def test_side_rail_history_has_single_room_owner():
    assert OWNER.exists()
    for css in ROOM.glob('*.css'):
        if css.name == OWNER.name:
            continue
        selectors = selector_text(css)
        for token in TOKENS:
            assert token not in selectors, f'{token} still owned by {css.name}'

def test_generic_parsec_skin_remains_separate():
    parsec = (ROOT / 'static/css/parsec_room.css').read_text(encoding='utf-8')
    assert '.parsec-room-panel' in parsec
    assert '.parsec-action-btn' in parsec
