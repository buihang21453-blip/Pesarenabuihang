import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ROUTES = (ROOT / "modules/luckybox/routes.py").read_text(encoding="utf-8")
SERVICE = (ROOT / "modules/luckybox/service.py").read_text(encoding="utf-8")
REPOSITORY = (ROOT / "modules/luckybox/repository.py").read_text(encoding="utf-8")
TEMPLATE = (ROOT / "templates/luckybox/index.html").read_text(encoding="utf-8")
HISTORY = (ROOT / "templates/luckybox/history.html").read_text(encoding="utf-8")
DETAIL = (ROOT / "templates/luckybox/opening_detail.html").read_text(encoding="utf-8")
JS = (ROOT / "static/js/luckybox_user.js").read_text(encoding="utf-8")
CSS = (ROOT / "static/css/luckybox_user.css").read_text(encoding="utf-8")
BASE = (ROOT / "templates/base.html").read_text(encoding="utf-8")
SHOP = (ROOT / "templates/shop.html").read_text(encoding="utf-8")
ADMIN = (ROOT / "templates/admin_luckybox/index.html").read_text(encoding="utf-8")


def test_phase3_version_and_python_parse():
    assert 'APP_VERSION = "V1.4.28"' in APP
    for relative in (
        "modules/luckybox/repository.py",
        "modules/luckybox/service.py",
        "modules/luckybox/routes.py",
    ):
        ast.parse((ROOT / relative).read_text(encoding="utf-8"), filename=relative)


def test_player_page_and_history_routes_are_login_protected():
    assert '@app.route("/lucky-box", endpoint="luckybox_home")' in ROUTES
    assert '@app.route("/lucky-box/history", endpoint="luckybox_history")' in ROUTES
    assert '@app.route("/lucky-box/openings/<opening_id>"' in ROUTES
    assert ROUTES.count("@login_required") >= 11


def test_admin_player_ui_preview_is_non_mutating():
    assert 'endpoint="luckybox_admin_preview_open"' in ROUTES
    assert "@admin_required" in ROUTES
    assert "preview_open_for_admin" in ROUTES
    preview = SERVICE.split("def preview_open_for_admin", 1)[1].split("def build_opening_detail", 1)[0]
    assert "preview_rate_version" in preview
    assert "open_box" not in preview
    assert 'sample["balance_after"] = sample["balance_before"]' in preview
    assert 'sample["zcoin_cost"] = 0' in preview


def test_live_open_still_uses_atomic_rpc_and_request_id():
    assert '"open_lucky_box"' in REPOSITORY
    assert "validate_request_id" in SERVICE
    assert "repository.open_box" in SERVICE
    assert "request_id:requestId()" in JS


def test_player_ui_has_price_rewards_and_history_without_rate_panel():
    for text in (
        "Giá mỗi lượt",
        "POOL PHẦN THƯỞNG",
        "Lịch sử Lucky Box",
        "Ba phần thưởng của bạn",
    ):
        assert text in TEMPLATE
    assert "reward_groups" in TEMPLATE
    assert "data-lb3-open" in TEMPLATE
    assert "Tỷ lệ số vật phẩm trong mỗi lượt" not in TEMPLATE
    assert "Tỷ lệ trong nhóm" not in TEMPLATE


def test_phase4_has_opening_animation_without_sound():
    for marker in (
        "data-lb4-overlay",
        "data-lb4-stage",
        "data-lb4-rewards",
        "data-lb4-skip",
        "data-lb4-continue",
    ):
        assert marker in TEMPLATE
    for marker in (
        "playOpeningAnimation",
        "strongestRarity",
        "is-charging",
        "is-bursting",
        "is-revealing",
    ):
        assert marker in JS
    assert "@keyframes lb4BoxCharge" in CSS
    assert "@keyframes lb4BoxBurst" in CSS
    assert "@keyframes lb4Spark" in CSS
    assert "Audio(" not in JS
    assert "new Audio" not in JS


def test_player_style_ui_never_exposes_rate_percentages_even_in_admin_preview():
    assert "show_rates = False" in SERVICE
    assert 'reward.pop("group_percent", None)' in SERVICE
    assert 'reward.pop("weight", None)' in SERVICE
    assert '"item_count_odds": _item_count_percentages(selected_rate) if show_rates else []' in SERVICE
    assert '"show_rates": False' in ROUTES
    for forbidden in (
        "Tỷ lệ số vật phẩm trong mỗi lượt",
        "Tỷ lệ trong nhóm",
        "odd.percent",
        "CHỈ ADMIN PREVIEW",
        "TỶ LỆ CÔNG KHAI",
    ):
        assert forbidden not in TEMPLATE
    assert "Trọng số 0 vật phẩm" in ADMIN
    assert "Trọng số 1 vật phẩm" in ADMIN


def test_shop_and_account_navigation_link_to_luckybox():
    assert "url_for('luckybox_home')" in SHOP
    assert "url_for('luckybox_home')" in BASE
    assert "url_for('luckybox_history')" in TEMPLATE
    assert "Xem UI người chơi" in ADMIN


def test_history_and_detail_are_styled_and_user_scoped():
    assert "lb3-history-page" in HISTORY
    assert "lb3-detail-page" in DETAIL
    assert "build_opening_detail" in ROUTES
    assert "PermissionError" in ROUTES


def test_shop_home_has_prominent_luckybox_spotlight():
    shop_css = (ROOT / "static/css/shop_phase3.css").read_text(encoding="utf-8")
    for marker in (
        "shop3-luckybox-spotlight",
        "luckybox/luckybox-pes-arena.webp",
        "Mở hộp, săn phần thưởng bí ẩn",
        "14 vật phẩm độc quyền",
        "Khám phá Lucky Box",
    ):
        assert marker in SHOP
    assert "@keyframes shopLuckyFloat" in shop_css
    assert "@keyframes shopLuckySweep" in shop_css
