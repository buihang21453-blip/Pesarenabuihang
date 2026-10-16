"""Public, account-free friendly team randomizer.

V1.6.102: 5★/4★ pools are read from the owner's clubs_import catalog.
The public endpoint is read-only and cached in-process; random pairing stays client-side.
"""

import time

_CACHE = {"at": 0.0, "payload": None}
_CACHE_TTL = 300

def _name(row):
    for key in ("club_name", "team_name", "team", "name", "club", "display"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""

def _tier(row):
    for key in ("tier", "team_tier", "club_tier", "rank_tier"):
        value = str(row.get(key) or "").strip().upper().replace("Ｓ", "S")
        if value:
            return value
    return ""

def register_routes(context):
    globals().update(context)

    @app.route('/friendly')
    def friendly_public():
        return render_template('friendly_public.html')

    @app.route('/api/friendly/club-pools')
    def friendly_club_pools():
        now = time.monotonic()
        if _CACHE["payload"] is not None and now - _CACHE["at"] < _CACHE_TTL:
            return jsonify(_CACHE["payload"])
        try:
            result = execute_query(
                db.table('clubs_import').select('*').limit(1000),
                'friendly_public_clubs_import', attempts=2
            )
            five, four, seen5, seen4 = [], [], set(), set()
            for row in result.data or []:
                name, tier = _name(row), _tier(row)
                if not name:
                    continue
                key = name.casefold()
                if tier in {"S", "S+"} and key not in seen5:
                    five.append(name); seen5.add(key)
                elif tier in {"A", "A+"} and key not in seen4:
                    four.append(name); seen4.add(key)
            payload = {"ok": True, "five_star": five, "four_star": four, "source": "clubs_import"}
            _CACHE.update({"at": now, "payload": payload})
            return jsonify(payload)
        except Exception as exc:
            app.logger.warning('friendly clubs_import pool unavailable: %s', exc)
            return jsonify({"ok": False, "five_star": [], "four_star": [], "source": "clubs_import"}), 503
