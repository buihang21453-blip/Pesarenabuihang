"""Dữ liệu quản trị Gift Code cho tab Zcoin."""


def configure(context):
    globals().update(context)


def build_admin_context(actor):
    can_manage = has_admin_permission(actor, "zcoin_manage")
    can_view = can_manage or has_admin_permission(actor, "zcoin_view")
    codes = []
    if can_view:
        try:
            codes = list_gift_codes(limit=150)
        except Exception as exc:
            app.logger.exception("Không thể tải danh sách Gift Code: %s", exc)
    return {
        "can_view_gift_codes": can_view,
        "can_manage_gift_codes": can_manage,
        "gift_codes": codes,
    }
