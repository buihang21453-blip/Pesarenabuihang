from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_champion_cup_has_no_glow_layer():
    html = (ROOT / "templates/tournament/components/knockout_dashboard.html").read_text(encoding="utf-8")
    assert "c1-ko-cup-icon" in html
    assert "c1-ko-cup-glow" not in html

def test_champion_card_is_transparent_panel_free():
    css = (ROOT / "templates/tournament/styles.html").read_text(encoding="utf-8")
    assert ".c1-ko-champion-card{display:flex" in css
    assert "background:transparent;border:0;box-shadow:none" in css
