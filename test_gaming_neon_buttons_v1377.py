from pathlib import Path

def test_global_neon_css_is_last_and_scoped():
    base=Path('templates/base.html').read_text()
    assert 'data-ui-scope=' in base
    assert "css/gaming_neon_buttons.css" in base
    assert base.index("{% block page_styles %}{% endblock %}") < base.index("css/gaming_neon_buttons.css")

def test_admin_and_parsec_are_excluded():
    css=Path('static/css/gaming_neon_buttons.css').read_text()
    assert 'body[data-ui-scope="player"]' in css
    assert '.parsec-room-panel *' in css
    assert '#parsec-profile *' in css

def test_demo_visual_language_present():
    css=Path('static/css/gaming_neon_buttons.css').read_text()
    for token in ['--gn-line','--gn-glow','--gn-glow-strong','inset 0 1px 0','translateY(-1px)','translateY(1px)']:
        assert token in css

def test_version():
    assert 'APP_VERSION = "1.3.77"' in Path('app.py').read_text()
