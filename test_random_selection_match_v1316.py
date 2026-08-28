from pathlib import Path
ROOT=Path(__file__).parent
APP=(ROOT/"app.py").read_text(encoding="utf-8")
ROUTES=(ROOT/"modules/room_team_routes.py").read_text(encoding="utf-8")
MODE=(ROOT/"templates/partials/room_mode_selector_strip.html").read_text(encoding="utf-8")
CENTER=(ROOT/"templates/partials/room_mode_center_display.html").read_text(encoding="utf-8")
ROOMS=[(ROOT/p).read_text(encoding="utf-8") for p in ["templates/room_detail.html","templates/_room_live_content.html","templates/partials/room_dynamic_state.html"]]
RESULT=(ROOT/"modules/match_result_service.py").read_text(encoding="utf-8")
REMATCH=(ROOT/"modules/room_rematch_routes.py").read_text(encoding="utf-8")

def test_mode_core_and_version():
 assert 'APP_VERSION = "V1.4.7"' in APP
 assert 'RANDOM_SELECTION_MATCH_MODE = "random_selection_match"' in APP
 assert 'build_random_selection_match_state' in APP
 assert 'decode_random_selection_match_state' in APP

def test_mode_three_unlocked():
 assert 'name="rank_mode" value="random_selection_match"' in MODE
 segment=MODE.split('name="rank_mode" value="random_selection_match"',1)[1].split('room-mode-dock-number">4',1)[0]
 assert 'room-mode-lock-badge' not in segment
 assert 'Mỗi bên nhận 3 CLB' in segment

def test_start_immediately_and_no_choose_button_for_random_selection():
 assert 'def room_start_random_selection_match' in ROUTES
 assert 'create_random_selection_ranked_match' in ROUTES
 assert '"status": "playing"' in ROUTES
 for room in ROOMS:
  assert 'room.random_selection_match.host_options' in room
  assert 'room.random_selection_match.guest_options' in room
  host=room.split('room-random-selection-display',1)[1].split('{% elif room.status',1)[0]
  assert 'CHỌN CLB' not in host

def test_center_and_result_keep_identity():
 assert 'Random Selection Match' in CENTER
 assert "room_mode_logo_index = '3'" in CENTER
 assert 'is_random_selection_match' in RESULT
 assert '[MODE:random_selection_match]' in RESULT


def test_rematch_preserves_random_selection_mode_label():
 assert 'RANDOM_SELECTION_MATCH_MODE' in REMATCH
 assert 'Random Selection Match' in REMATCH
