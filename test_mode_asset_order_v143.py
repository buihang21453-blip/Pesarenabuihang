from pathlib import Path

EXPECTED_LINES = [
    '"rank_random": "1.webp"',
    '"random3_pick1": "2.webp"',
    '"home_away": "3.webp"',
    '"bo3": "4.webp"',
    '"tactical_bo3": "5.webp"',
    '"ban_pick_bo3": "6.webp"',
]

def test_mode_logo_order_matches_left_to_right_ui():
    text = Path('modules/static_asset_service.py').read_text(encoding='utf-8')
    start = text.index('MODE_LOGO_FILE_BY_CODE = {')
    end = text.index('}\n\n\ndef mode_asset_base_url()', start)
    block = text[start:end]
    positions = []
    for line in EXPECTED_LINES:
        assert line in block
        positions.append(block.index(line))
    assert positions == sorted(positions)
