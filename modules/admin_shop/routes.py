"""Route quản trị Cửa hàng độc lập."""

from . import repository
from . import service


def register_routes(context):
    globals().update(context)
    repository.configure(context)
    service.configure(context)

    def _redirect(anchor=""):
        target = url_for("admin_shop")
        return redirect(target + (f"#{anchor}" if anchor else ""))

    @app.route("/admin/shop", endpoint="admin_shop")
    @login_required
    @admin_required
    def admin_shop_page():
        return render_template("admin_shop/index.html", **service.build_page_context())

    @app.route(
        "/admin/shop/items/<item_id>/update",
        methods=["POST"],
        endpoint="admin_shop_update_item",
    )
    @login_required
    @admin_required
    def admin_shop_update_item_route(item_id):
        try:
            payload = service.parse_item_update(request.form)
            item = repository.update_item(item_id, payload)
        except ValueError as exc:
            flash(str(exc), "danger")
            return _redirect("catalog")
        except Exception as exc:
            app.logger.exception("Admin Shop update failed item=%s: %s", item_id, exc)
            flash(service.admin_error_message(exc), "danger")
            return _redirect("catalog")

        log_admin_action(
            "Cập nhật vật phẩm Shop",
            "shop_item",
            item_id,
            (item or {}).get("name") or item_id,
            str(payload),
        )
        flash("Đã cập nhật vật phẩm.", "success")
        return _redirect("catalog")

    @app.route(
        "/admin/shop/grant",
        methods=["POST"],
        endpoint="admin_shop_grant",
    )
    @login_required
    @admin_required
    def admin_shop_grant_route():
        actor = current_user()
        try:
            payload = service.parse_grant(request.form)
            result = repository.grant_item(
                actor.get("id"),
                payload["item_code"],
                payload["quantity"],
                payload["target_user_id"],
                payload["grant_all"],
                payload["note"],
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return _redirect("grant-items")
        except Exception as exc:
            app.logger.exception("Admin Shop grant failed: %s", exc)
            flash(service.admin_error_message(exc), "danger")
            return _redirect("grant-items")

        recipient_count = int(result.get("recipient_count") or 0)
        item_code = str(result.get("item_code") or payload["item_code"])
        item_name = str(result.get("item_name") or item_code)
        granted_quantity = int(result.get("quantity") or payload["quantity"] or 1)
        gift_message = f"Admin đã tặng bạn {granted_quantity} × {item_name}."
        if payload["note"]:
            gift_message += f" Ghi chú: {payload['note']}"
        gift_link = url_for("inventory", gift_item=item_code)
        if payload["grant_all"]:
            recipient_ids = [row.get("id") for row in repository.list_players() if row.get("id")]
            create_notifications_for_users(
                recipient_ids, "Bạn nhận được vật phẩm từ Admin", gift_message,
                gift_link, "admin_gift_item",
            )
        elif payload["target_user_id"]:
            create_user_notification(
                payload["target_user_id"], "Bạn nhận được vật phẩm từ Admin",
                gift_message, gift_link, "admin_gift_item",
            )
        log_admin_action(
            "Tặng vật phẩm Shop",
            "shop_item_grant",
            result.get("item_id") or payload["item_code"],
            payload["item_code"],
            f"quantity={payload['quantity']} recipients={recipient_count} note={payload['note']}",
        )
        cache_delete("_rz_current_user")
        cache_delete("_rz_players_all")
        cache_delete("_rz_users_map")
        flash(f"Đã tặng vật phẩm cho {recipient_count} người chơi.", "success")
        return _redirect("grant-items")
