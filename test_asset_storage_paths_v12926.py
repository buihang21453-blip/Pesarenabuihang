import importlib
import os
import sys
import types
from unittest.mock import patch

fake_flask = types.ModuleType('flask')
fake_flask.url_for = lambda endpoint, filename='': f'/static/{filename}'
sys.modules.setdefault('flask', fake_flask)

service = importlib.import_module('modules.static_asset_service')
ROOT = 'https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1.14.41'


def test_default_shop_base_is_real_supabase_folder():
    with patch.dict(os.environ, {'SHOP_ASSET_BASE_URL':'', 'STATIC_ASSET_BASE_URL':''}, clear=False):
        assert service.shop_asset_base_url() == ROOT + '/shop'


def test_default_luckybox_base_is_real_supabase_folder():
    with patch.dict(os.environ, {'LUCKYBOX_ASSET_BASE_URL':'', 'STATIC_ASSET_BASE_URL':''}, clear=False):
        assert service.luckybox_asset_base_url() == ROOT + '/luckybox'


def test_shop_item_exact_url():
    with patch.dict(os.environ, {'SHOP_ASSET_BASE_URL':'', 'STATIC_ASSET_BASE_URL':''}, clear=False):
        assert service.asset_url('shop/items/avatar_frame_common.webp') == ROOT + '/shop/items/avatar_frame_common.webp'


def test_luckybox_exclusive_exact_url():
    with patch.dict(os.environ, {'LUCKYBOX_ASSET_BASE_URL':'', 'STATIC_ASSET_BASE_URL':''}, clear=False):
        assert service.asset_url('luckybox/exclusive/avatar-frame-royal-dominator.webp') == ROOT + '/luckybox/exclusive/avatar-frame-royal-dominator.webp'


def test_luckybox_reward_exact_url():
    with patch.dict(os.environ, {'LUCKYBOX_ASSET_BASE_URL':'', 'STATIC_ASSET_BASE_URL':''}, clear=False):
        assert service.asset_url('luckybox/rewards/discount-coupon-05.webp') == ROOT + '/luckybox/rewards/discount-coupon-05.webp'


def test_absolute_supabase_url_passthrough():
    url = ROOT + '/shop/items/avatar_frame_common.webp'
    assert service.asset_url(url) == url
