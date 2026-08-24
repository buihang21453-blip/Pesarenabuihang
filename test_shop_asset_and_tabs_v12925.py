from pathlib import Path


def test_shop_clean_build_has_public_asset_fallback():
    source = Path('modules/static_asset_service.py').read_text(encoding='utf-8')
    assert 'v1.14.41/shop' in source
    assert 'DEFAULT_SHOP_ASSET_BASE_URL' in source


def test_shop_primary_tabs_luckybox_first_and_topup_separate():
    source = Path('templates/shop.html').read_text(encoding='utf-8')
    nav = source[source.index('<nav class="shop3-main-tabs"'):]
    assert nav.index('Lucky Box') < nav.index('Vật phẩm') < nav.index('Nạp Zcoin')
    assert "shop_page_tab == 'topup'" in source
    assert 'partials/shop_zcoin_topup.html' in source


def test_topup_latest_bonus_markers():
    source = Path('templates/partials/shop_zcoin_topup.html').read_text(encoding='utf-8')
    assert '+1.800 <span aria-hidden="true">⭐</span>' in source
    assert '+3.500 <span aria-hidden="true">⭐</span>' in source
    assert '+8.000 <span aria-hidden="true">⭐</span>' in source
    assert '🔥' not in source
