"""Tournament module routes.

V1.4.24 keeps tournament concerns isolated from Rank/Season/Match data.
The module currently provides only the UI structure and an Admin open/close switch.
No tournament records are mocked and no competition database tables are created yet.
"""

TOURNAMENT_AREA_SETTING_KEY = "tournament_area_enabled"


def register_routes(context):
    globals().update(context)

    def tournament_area_enabled(force=False):
        request_key = "_tournament_area_enabled_cached"
        if not force:
            cached = cache_get(request_key)
            if isinstance(cached, bool):
                return cached
            cached = ttl_cache_get("tournament_area_enabled")
            if isinstance(cached, bool):
                return cache_set(request_key, cached)

        # Tạm đóng theo yêu cầu. Admin phải chủ động bật.
        enabled = False
        try:
            result = execute_query(
                db.table("system_settings").select("setting_value")
                .eq("setting_key", TOURNAMENT_AREA_SETTING_KEY).limit(1),
                "get_tournament_area_enabled", attempts=2,
            )
            raw = ((result.data or [{}])[0]).get("setting_value")
            if isinstance(raw, dict):
                raw = raw.get("enabled")
            if isinstance(raw, str):
                raw = raw.strip().lower() in {"1", "true", "yes", "on", "enabled"}
            if isinstance(raw, bool):
                enabled = raw
        except Exception as exc:
            print(f"tournament_area_enabled warning: {exc}")

        ttl_cache_set("tournament_area_enabled", enabled, 45)
        return cache_set(request_key, enabled)

    @app.context_processor
    def inject_tournament_context():
        return {"tournament_area_enabled": tournament_area_enabled()}

    @app.get('/tournaments')
    @login_required
    def tournaments():
        return render_template(
            'tournaments.html',
            tournament_open=tournament_area_enabled(),
        )

    @app.post('/admin/tournaments/access')
    @login_required
    @admin_required
    @admin_permission_required("system_features_manage")
    def admin_tournament_access():
        enabled = request.form.get("enabled") == "1"
        execute_query(
            db.table("system_settings").upsert({
                "setting_key": TOURNAMENT_AREA_SETTING_KEY,
                "setting_value": {"enabled": enabled},
                "updated_at": now_iso(),
            }, on_conflict="setting_key"),
            "admin_update_tournament_area", attempts=2,
        )
        ttl_cache_delete("tournament_area_enabled")
        cache_delete("_tournament_area_enabled_cached")
        log_admin_action(
            "Mở khu vực Giải đấu" if enabled else "Tạm đóng khu vực Giải đấu",
            "system", details={"enabled": enabled},
        )
        flash(
            "Đã mở khu vực Giải đấu." if enabled else "Đã tạm đóng khu vực Giải đấu.",
            "success",
        )
        return redirect_admin("tournaments")
