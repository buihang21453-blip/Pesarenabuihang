import importlib
import os
import sys
import types
from unittest.mock import patch

fake_flask = types.ModuleType("flask")
fake_flask.url_for = lambda endpoint, filename="": f"/static/{filename}"
sys.modules.setdefault("flask", fake_flask)

service = importlib.import_module("modules.static_asset_service")
ROOT = "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1.14.41"

def _env():
    return patch.dict(os.environ, {
        "LUCKYBOX_ASSET_BASE_URL": "",
        "SHOP_ASSET_BASE_URL": "",
        "STATIC_ASSET_BASE_URL": "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1",
    }, clear=False)

def test_luckybox_root_box_image_uses_v11441():
    with _env():
        assert service.asset_url("luckybox/luckybox-pes-arena.webp") == ROOT + "/luckybox/luckybox-pes-arena.webp"

def test_luckybox_root_no_reward_uses_v11441():
    with _env():
        assert service.asset_url("luckybox/no-reward.webp") == ROOT + "/luckybox/no-reward.webp"

def test_luckybox_exclusive_uses_v11441():
    with _env():
        assert service.asset_url("luckybox/exclusive/avatar-frame-royal-dominator.webp") == ROOT + "/luckybox/exclusive/avatar-frame-royal-dominator.webp"

def test_luckybox_rewards_uses_v11441():
    with _env():
        assert service.asset_url("luckybox/rewards/discount-coupon-05.webp") == ROOT + "/luckybox/rewards/discount-coupon-05.webp"

def test_shop_items_uses_v11441_even_when_static_base_is_v1():
    with _env():
        assert service.asset_url("shop/items/avatar_frame_common.webp") == ROOT + "/shop/items/avatar_frame_common.webp"
