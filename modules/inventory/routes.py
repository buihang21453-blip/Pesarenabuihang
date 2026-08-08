"""Route Kho đồ Giai đoạn 3."""

from . import repository
from . import service
from modules.shop.catalog import EQUIPMENT_SLOT_LABELS
from modules.profile import equipment_service


def register_routes(context):
    globals().update(context)
    repository.configure(context)
    service.configure(context)

    @app.route("/inventory", endpoint="inventory")
    @login_required
    def inventory_page():
        user = current_user()
        active_tab = request.args.get("tab") or "all"
        focus_item_code = str(request.args.get("gift_item") or "").strip()
        return render_template(
            "inventory.html",
            **service.build_inventory_context(user, active_tab, focus_item_code),
        )

    @app.route(
        "/inventory/equip/<inventory_id>",
        methods=["POST"],
        endpoint="inventory_equip",
    )
    @login_required
    def inventory_equip_route(inventory_id):
        user = current_user()
        try:
            result = repository.equip_inventory_item(user.get("id"), inventory_id)
        except Exception as exc:
            app.logger.exception("Equip inventory failed user=%s inventory=%s: %s", user.get("id"), inventory_id, exc)
            flash(service.equipment_error_message(exc), "danger")
            return redirect(url_for("inventory"))

        ttl_cache_delete(f"user:{user.get('id')}")
        cache_delete("_rz_current_user")
        equipment_service.invalidate_equipment_cache(user.get("id"))
        flash(f"Đã trang bị {result.get('item_name') or 'vật phẩm'}.", "success")
        return redirect(url_for("inventory", tab="equipped"))

    @app.route(
        "/inventory/unequip/<slot>",
        methods=["POST"],
        endpoint="inventory_unequip",
    )
    @login_required
    def inventory_unequip_route(slot):
        user = current_user()
        if slot not in EQUIPMENT_SLOT_LABELS:
            flash("Vị trí trang bị không hợp lệ.", "danger")
            return redirect(url_for("inventory"))
        try:
            repository.unequip_slot(user.get("id"), slot)
        except Exception as exc:
            app.logger.exception("Unequip failed user=%s slot=%s: %s", user.get("id"), slot, exc)
            flash(service.equipment_error_message(exc), "danger")
            return redirect(url_for("inventory"))

        ttl_cache_delete(f"user:{user.get('id')}")
        cache_delete("_rz_current_user")
        equipment_service.invalidate_equipment_cache(user.get("id"))
        flash(f"Đã gỡ {EQUIPMENT_SLOT_LABELS[slot]}.", "success")
        return redirect(url_for("inventory", tab="equipped"))
