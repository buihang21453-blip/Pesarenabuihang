from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = (ROOT / 'static/css/room/08-action-layout-guard.css').read_text(encoding='utf-8')
CENTER = (ROOT / 'templates/room/_center_stage.html').read_text(encoding='utf-8')
LIVE = (ROOT / 'templates/_room_live_content.html').read_text(encoding='utf-8')


def test_all_player_action_labels_are_still_rendered():
    labels = ('Sẵn Sàng', 'Hủy Sẵn Sàng', 'Thoát Phòng', 'Gửi Kết Quả', 'Đá Tiếp', 'Về sảnh')
    for label in labels:
        assert label in CENTER
        assert label in LIVE
    assert 'Đưa khỏi phòng' in LIVE


def test_glass_neon_style_covers_action_zones_and_kick():
    marker = CSS.split('/* V1.3.75', 1)[1]
    for selector in (
        '.room-center-primary-actions .arena-btn',
        '.room-action-zone .arena-btn',
        '.room-center-score-panel .room-submit-result-btn',
        '.room-result-actions .room-result-btn',
        '.room-guest-card-kick-btn',
    ):
        assert selector in marker
    assert 'backdrop-filter:blur(7px)' in marker


def test_semantic_glass_variants_are_translucent():
    marker = CSS.split('/* V1.3.75', 1)[1]
    for token in (
        'rgba(8,104,65,.32)',
        'rgba(40,61,126,.30)',
        'rgba(121,84,16,.34)',
        'rgba(116,23,43,.33)',
    ):
        assert token in marker
    # protect against falling back to the old nearly opaque .96-.99 action backgrounds
    assert '--room-btn-top:rgba(' not in marker
    assert '--room-btn-bottom:rgba(' not in marker


def test_parsec_selectors_are_not_styled_by_v1375_block():
    marker = CSS.split('/* V1.3.75', 1)[1]
    assert '.parsec' not in marker.lower()
