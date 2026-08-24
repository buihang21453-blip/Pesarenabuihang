import os
from unittest.mock import patch


from modules import static_asset_service as service

ROOT_11441 = "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1.14.41"
ROOT_V1 = "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/v1"


def test_shop_does_not_inherit_general_v1_asset_base():
    with patch.dict(os.environ, {
        "STATIC_ASSET_BASE_URL": ROOT_V1,
        "SHOP_ASSET_BASE_URL": "",
        "LUCKYBOX_ASSET_BASE_URL": "",
    }, clear=False):
        assert service.asset_url("shop/items/avatar_frame_common.webp") == ROOT_11441 + "/shop/items/avatar_frame_common.webp"
        assert service.asset_url("luckybox/rewards/discount-coupon-05.webp") == ROOT_11441 + "/luckybox/rewards/discount-coupon-05.webp"


def test_non_shop_assets_keep_general_v1_base():
    with patch.dict(os.environ, {
        "STATIC_ASSET_BASE_URL": ROOT_V1,
        "SHOP_ASSET_BASE_URL": "",
        "LUCKYBOX_ASSET_BASE_URL": "",
    }, clear=False):
        assert service.asset_url("zcoin-logo.webp") == ROOT_V1 + "/zcoin-logo.webp"
        assert service.asset_url("ranks/ga.webp") == ROOT_V1 + "/ranks/ga.webp"


def test_explicit_shop_base_still_can_override():
    custom = "https://example.com/custom-shop"
    with patch.dict(os.environ, {"SHOP_ASSET_BASE_URL": custom}, clear=False):
        assert service.asset_url("shop/items/avatar_frame_common.webp") == custom + "/items/avatar_frame_common.webp"
