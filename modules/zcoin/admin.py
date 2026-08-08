"""Chuẩn bị dữ liệu quản trị Zcoin, tách khỏi dashboard Admin chính."""

import uuid


def configure(context):
    globals().update(context)


def build_admin_context(players, actor):
    """Trả về toàn bộ dữ liệu cần cho tab Zcoin trong Admin."""
    can_manage = has_admin_permission(actor, "zcoin_manage")
    can_view = can_manage or has_admin_permission(actor, "zcoin_view")
    transactions = (
        admin_safe_load(
            "zcoin_transactions",
            lambda: list_zcoin_transactions(limit=100),
            [],
        )
        if can_view
        else []
    )
    stats = (
        build_zcoin_stats(players, transactions)
        if can_view
        else {
            "circulating": 0,
            "wallet_count": 0,
            "highest_balance": 0,
            "recent_issued": 0,
            "recent_withdrawn": 0,
        }
    )
    return {
        "can_view_zcoin": can_view,
        "can_manage_zcoin": can_manage,
        "zcoin_transactions": transactions,
        "zcoin_stats": stats,
        "zcoin_adjustment_token": uuid.uuid4().hex if can_manage else "",
    }
