from modules.parsec_room.service import validate_parsec_id, validate_parsec_link

def test_parsec_id_valid(): assert validate_parsec_id('Player_01') == 'Player_01'
def test_parsec_id_with_hash_valid(): assert validate_parsec_id('Salem6556#18473949') == 'Salem6556#18473949'
def test_parsec_id_empty_allowed(): assert validate_parsec_id('') is None
def test_parsec_id_rejects_spaces():
    try: validate_parsec_id('bad id')
    except ValueError: return
    assert False

def test_parsec_link_valid(): assert validate_parsec_link('https://parsec.gg/g/abc/def')
def test_parsec_link_optional(): assert validate_parsec_link('') is None
def test_parsec_link_rejects_fake_domain():
    for link in ('https://parsec.gg.evil.com/g/a/b','https://evilparsec.gg/g/a/b','http://parsec.gg/g/a/b'):
        try: validate_parsec_link(link)
        except ValueError: continue
        assert False, link

def test_no_new_polling_source():
    src=open('modules/parsec_room/routes.py',encoding='utf-8').read()+open('templates/_room_live_content.html',encoding='utf-8').read()
    assert 'setInterval' not in src and 'setTimeout' not in src

def test_rp_files_untouched_by_module():
    src=open('modules/parsec_room/routes.py',encoding='utf-8').read()
    assert 'rp_' not in src.lower() and 'matches' not in src.lower()


def test_parsec_visible_on_initial_room_template():
    initial=open('templates/room_detail.html',encoding='utf-8').read()
    fragment=open('templates/_room_live_content.html',encoding='utf-8').read()
    for src in (initial, fragment):
        assert 'partials/parsec_room_panel.html' in src
    panel=open('templates/partials/parsec_room_panel.html',encoding='utf-8').read()
    assert "asset_url('parsec-logo.webp')" in panel
    assert '<span>Copy Link</span>' in panel

def test_parsec_panel_is_in_right_rail():
    for name in ('templates/room_detail.html','templates/_room_live_content.html'):
        src=open(name,encoding='utf-8').read()
        assert src.index('room-arena-right-rail') < src.index('partials/parsec_room_panel.html')

def test_parsec_logo_is_webp_and_no_polling_added():
    from pathlib import Path
    
    # Logo đã được đưa lên Supabase và không còn đóng gói cục bộ.
    manifest = Path('SUPABASE_ASSET_MANIFEST.csv').read_text(encoding='utf-8-sig')
    assert 'parsec-logo.webp' in manifest
    assert not Path('static/parsec-logo.png').exists()
    src=open('static/css/parsec_room.css',encoding='utf-8').read()
    assert 'width:18px!important' in src
    assert 'height:18px!important' in src
    assert 'setInterval' not in src
