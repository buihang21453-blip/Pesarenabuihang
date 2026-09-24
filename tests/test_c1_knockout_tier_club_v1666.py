from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_knockout_payload_contains_tier_and_club_fields():
    src=(ROOT/'modules/tournament_routes.py').read_text(encoding='utf-8')
    for token in ['"home_tier"','"away_tier"','"home_club"','"away_club"','"champion_tier"','"champion_club"']:
        assert token in src

def test_knockout_dashboard_renders_tier_and_club_chips():
    html=(ROOT/'templates/tournament/components/knockout_dashboard.html').read_text(encoding='utf-8')
    assert 'pair.home_tier' in html and 'pair.away_tier' in html
    assert 'pair.home_club' in html and 'pair.away_club' in html
    assert 'c1-ko-tier-chip' in html and 'c1-ko-club-chip' in html
