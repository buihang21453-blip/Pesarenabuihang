"""Route Cửa hàng Giai đoạn 3."""

from . import service


def register_routes(context):
    globals().update(context)
    service.configure(context)

    @app.route("/shop", endpoint="shop")
    @login_required
    def shop_page():
        user = current_user()
        requested_tab = str(request.args.get("tab") or "store").strip().lower()
        page_tab = "topup" if requested_tab in {"topup", "zcoin", "nap-zcoin"} else "store"
        active_category = request.args.get("category") or "featured"
        context = service.build_shop_context(user, active_category)
        context["shop_page_tab"] = page_tab
        return render_template("shop.html", **context)

    @app.route("/shop/purchase/<item_code>", methods=["POST"], endpoint="shop_purchase")
    @login_required
    def shop_purchase_route(item_code):
        user = current_user()
        category = str(request.form.get("category") or "featured").strip()
        coupon_inventory_id = str(request.form.get("coupon_inventory_id") or "").strip() or None
        request_key = str(request.form.get("request_key") or "").strip()
        try:
            result = service.purchase_for_user(
                user,
                item_code,
                coupon_inventory_id,
                request_key,
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("shop", category=category))
        except Exception as exc:
            app.logger.exception("Shop purchase failed user=%s item=%s: %s", user.get("id"), item_code, exc)
            flash(service.purchase_error_message(exc), "danger")
            return redirect(url_for("shop", category=category))

        new_balance = int(result.get("balance_after") or 0)
        session["zcoin_balance"] = new_balance
        ttl_cache_delete(f"user:{user.get('id')}")
        cache_delete("_rz_current_user")
        cache_delete("_rz_players_all")
        cache_delete("_rz_users_map")

        item_name = result.get("item_name") or item_code
        paid = format_zcoin(result.get("final_price") or 0)
        discount = int(result.get("discount_amount") or 0)
        discount_text = f" (đã giảm {format_zcoin(discount)} Zcoin)" if discount > 0 else ""
        flash(f"Đã mua {item_name} với {paid} Zcoin{discount_text}.", "success")
        return redirect(url_for("inventory"))
