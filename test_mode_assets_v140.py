from pathlib import Path
ROOT = Path(__file__).resolve().parent

def read(rel): return (ROOT/rel).read_text(encoding='utf-8')

def test_version():
    assert 'APP_VERSION = "1.3.43"' in read('app.py')

def test_mode_base_and_mapping():
    s=read('modules/static_asset_service.py')
    assert 'pes-assets/room-assets/v1.3.40/modes' in s
    expected={
        'rank_random':'1.webp','random3_pick1':'2.webp','home_away':'3.webp',
        'bo3':'4.webp','tactical_bo3':'5.webp','ban_pick_bo3':'6.webp'}
    for code,name in expected.items():
        assert f'"{code}": "{name}"' in s

def test_templates_use_single_mode_asset_helper():
    for rel in ['templates/room_detail.html','templates/_room_live_content.html']:
        s=read(rel)
        assert 'mode_asset(selected_rank_mode)' in s
        assert 'mode_asset(mode.code)' in s
        assert "room_asset('emblems/' ~ selected_rank_mode" not in s
        assert "room_asset('modes/' ~ mode.code" not in s

def test_upload_tree_exists_and_is_clean():
    p=ROOT/'pes-assets'/'room-assets'/'v1.3.40'/'modes'
    assert p.is_dir()
    assert list(p.iterdir()) == []
