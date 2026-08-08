from pathlib import Path

EXPECTED = "{'rank_random':1,'random3_pick1':2,'home_away':3,'bo3':4,'tactical_bo3':5,'ban_pick_bo3':6}"

def test_room_detail_selected_mode_number_map():
    text = Path('templates/room_detail.html').read_text(encoding='utf-8')
    assert EXPECTED in text

def test_room_live_selected_mode_number_map():
    text = Path('templates/_room_live_content.html').read_text(encoding='utf-8')
    assert EXPECTED in text
