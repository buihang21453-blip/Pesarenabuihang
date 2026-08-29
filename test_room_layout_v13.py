from pathlib import Path

ROOT = Path(__file__).parent
ROOM = (ROOT / "templates/room_detail.html").read_text(encoding="utf-8")
MODE = (ROOT / "templates/partials/room_mode_selector_strip.html").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/rank_mode_toggle.css").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_release_bundle_is_v13_without_breaking_legacy_app_version_contract():
    assert '# UI release bundle: V1.3' in APP
    assert 'APP_VERSION = "V1.4.20"' in APP


def test_user_reported_dom_classes_are_covered():
    assert 'room-center-stage-plain' in ROOM
    assert 'room-side-card room-team-card home' in ROOM
    assert 'btn gold room-center-action-btn' in ROOM
    assert 'btn red room-center-action-btn' in ROOM


def test_three_main_panels_have_exact_same_desktop_heights():
    for selector in (
        '.room-layout-v137 .room-team-card.home',
        '.room-layout-v137 .room-center-stage-plain',
        '.room-layout-v137 .room-team-card.away',
    ):
        assert selector in CSS
    assert 'height: 100% !important;' in CSS
    assert 'align-self: stretch !important;' in CSS
    assert 'align-items: stretch !important;' in CSS
    assert 'grid-template-columns: repeat(3, minmax(0, 1fr))' in CSS


def test_primary_actions_are_centered_and_balanced():
    assert '.room-layout-v137 .room-center-primary-actions {' in CSS
    assert 'width: min(100%, 330px) !important;' in CSS
    assert 'grid-template-columns: repeat(2, minmax(0, 1fr)) !important;' in CSS
    assert 'margin-left: auto !important;' in CSS
    assert 'margin-right: auto !important;' in CSS


def test_mode_area_is_transparent_but_logo_background_is_adjustable():
    assert 'background: transparent !important;' in CSS
    assert '.room-layout-v137 .room-mode-dock-logo-shell' in CSS
    assert 'var(--room-mode-logo-bg-opacity, 0)' in CSS
    assert MODE.count('room-mode-dock-logo-shell') >= 7
    for index in range(1, 8):
        assert f'{index}.webp' in MODE

if __name__ == '__main__':
    test_release_bundle_is_v13_without_breaking_legacy_app_version_contract()
    test_user_reported_dom_classes_are_covered()
    test_three_main_panels_have_exact_same_desktop_heights()
    test_primary_actions_are_centered_and_balanced()
    test_mode_area_is_transparent_but_logo_background_is_adjustable()
