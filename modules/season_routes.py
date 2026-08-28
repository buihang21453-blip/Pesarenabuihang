"""Admin/API routes for Rank seasons."""
from flask import jsonify

def register_routes(context):
    globals().update(context)

    def _players_sorted():
        rows = [dict(p) for p in list_players()]
        matches = list_matches()
        season = get_current_season()
        season_counts = build_season_match_count_map(matches, season)
        latest_map = _latest_ranking_activity_map(matches)
        now = now_dt()
        eligible = []
        for p in rows:
            state = season_ranking_eligibility(
                p, season_counts.get(str(p.get("id")), 0),
                latest_map.get(str(p.get("id"))), now=now, season=season
            )
            if state.get("visible"):
                eligible.append(p)
        eligible.sort(key=_player_ranking_sort_key)
        return eligible

    @app.context_processor
    def inject_season_context():
        try:
            season = get_current_season()
            history = get_season_history(12)
        except Exception:
            season, history = {"season_number":1,"name":"Season 1","placement_matches":5}, []
        return {"current_rank_season": season, "rank_season_history": history, "rank_season_reward_config": get_season_reward_config()}

    @app.get('/api/rank/season')
    def rank_season_api():
        return jsonify({"ok": True, "season": get_current_season(), "history": get_season_history(12)})

    @app.post('/admin/season/snapshot')
    @login_required
    @admin_required
    @admin_permission_required('system_features_manage')
    def admin_season_snapshot():
        season = get_current_season()
        players = _players_sorted()
        matches = list_matches()
        season_stats = _build_season_stats_map(matches, season)
        payload = []
        for pos, p in enumerate(players, 1):
            uid = str(p.get('id'))
            stats = season_stats.get(uid, {})
            payload.append({"user_id": uid, "position": pos,
                            "rank_points": int(p.get('rank_points') or 0),
                            "display_name": p.get('display_name') or p.get('username'),
                            "wins": int(stats.get('wins') or 0),
                            "draws": int(stats.get('draws') or 0),
                            "losses": int(stats.get('losses') or 0),
                            "recent_form": list(stats.get('recent_form') or [])[:5]})
        execute_query(db.table('rank_season_snapshots').upsert({
            'season_number': int(season.get('season_number') or 1),
            'snapshot_data': payload, 'created_at': now_iso()
        }, on_conflict='season_number'), 'season_snapshot', attempts=2)
        log_admin_action('Đóng băng BXH mùa', 'season', details={'season': season.get('season_number'), 'players': len(payload)})
        flash(f"Đã đóng băng BXH {season.get('name') or 'Season' } với {len(payload)} người chơi.", 'success')
        return redirect_admin('season')

    @app.post('/admin/season/reward-config')
    @login_required
    @admin_required
    @admin_permission_required('system_features_manage')
    def admin_season_reward_config():
        config = {}
        try:
            for pos in (1, 2, 3):
                zcoin = max(0, int(request.form.get(f'top{pos}_zcoin') or 0))
                boxes = max(0, int(request.form.get(f'top{pos}_lucky_box') or 0))
                if zcoin > 100000000 or boxes > 100000:
                    raise ValueError('reward too large')
                config[f'top{pos}'] = {'zcoin': zcoin, 'lucky_box': boxes}
        except (TypeError, ValueError):
            flash('Giá trị phần thưởng không hợp lệ.', 'danger')
            return redirect_admin('season')
        execute_query(db.table('system_settings').upsert({
            'setting_key': SEASON_REWARD_SETTING_KEY, 'setting_value': config, 'updated_at': now_iso()
        }, on_conflict='setting_key'), 'save_rank_season_reward_config', attempts=2)
        log_admin_action('Cập nhật thưởng mùa', 'season', details=config)
        flash('Đã lưu phần thưởng Top 1-3.', 'success')
        return redirect_admin('season')

    @app.post('/admin/season/rewards')
    @login_required
    @admin_required
    @admin_permission_required('system_features_manage')
    def admin_season_rewards():
        season = get_current_season()
        sn = int(season.get('season_number') or 1)
        snap = execute_query(db.table('rank_season_snapshots').select('*').eq('season_number', sn).limit(1), 'season_reward_snapshot', attempts=2)
        if not snap.data:
            flash('Chưa có Snapshot BXH. Hãy đóng băng BXH trước.', 'danger')
            return redirect_admin('season')
        rows = list(snap.data[0].get('snapshot_data') or [])[:3]
        actor = current_user()
        reward_config = get_season_reward_config()
        rewarded = 0
        for row in rows:
            pos = int(row.get('position') or 0)
            if pos not in (1, 2, 3): continue
            reward = reward_config.get(f'top{pos}', {})
            zcoin = max(0, int(reward.get('zcoin') or 0))
            boxes = max(0, int(reward.get('lucky_box') or 0))
            uid = str(row.get('user_id'))
            key = f"season:{sn}:rank:{pos}:zcoin"
            try:
                adjust_zcoin_balance(uid, zcoin, f"Thưởng {season.get('name')} Top {pos}", actor.get('id'), key)
            except Exception as exc:
                # Idempotency RPC returns safely on repeats; only re-raise unrelated hard failures.
                if 'idempot' not in str(exc).lower() and 'duplicate' not in str(exc).lower():
                    raise
            execute_query(db.table('rank_season_rewards').upsert({
                'season_number': sn, 'user_id': uid, 'position': pos,
                'zcoin_reward': zcoin, 'lucky_box_reward': boxes,
                'status': 'granted', 'granted_at': now_iso()
            }, on_conflict='season_number,user_id'), 'season_reward_log', attempts=2)
            rewarded += 1
        log_admin_action('Trao thưởng mùa', 'season', details={'season': sn, 'rewarded': rewarded})
        flash(f'Đã ghi nhận thưởng Top 3 của {season.get("name")}: Zcoin + lượt Lucky Box thưởng.', 'success')
        return redirect_admin('season')

    @app.post('/admin/season/reset-open-next')
    @login_required
    @admin_required
    @admin_permission_required('system_features_manage')
    def admin_season_reset_open_next():
        season = get_current_season()
        sn = int(season.get('season_number') or 1)
        # Require snapshot + reward log before destructive RP reset.
        snap = execute_query(db.table('rank_season_snapshots').select('season_number').eq('season_number', sn).limit(1), 'season_reset_snapshot_guard', attempts=2)
        rewards = execute_query(db.table('rank_season_rewards').select('user_id').eq('season_number', sn), 'season_reset_reward_guard', attempts=2)
        if not snap.data or len(rewards.data or []) < 3:
            flash('Chưa đủ Snapshot + log thưởng Top 3. Không cho phép reset.', 'danger')
            return redirect_admin('season')
        next_sn = sn + 1
        started = now_iso()
        try:
            result = execute_query(
                db.rpc('reset_rank_season_open_next', {
                    'p_current_season': sn,
                    'p_current_name': season.get('name') or f'Season {sn}',
                    'p_current_started_at': season.get('started_at'),
                    'p_reset_at': started,
                    'p_next_season': next_sn,
                    'p_next_name': f'Season {next_sn}',
                    'p_placement_matches': 5,
                }),
                'reset_rank_season_open_next_rpc', attempts=2
            )
            payload = result.data
            if isinstance(payload, list):
                payload = payload[0] if payload else {}
            if not isinstance(payload, dict):
                payload = {}
            if payload.get('ok') is False:
                raise RuntimeError(payload.get('message') or 'Database từ chối reset mùa.')
        except Exception as exc:
            print(f'season reset failed: {type(exc).__name__}: {exc}')
            flash('Reset mùa chưa hoàn tất. Database đã tự hoàn tác thay đổi của lần này. Hãy kiểm tra đã chạy SQL V1.4.8 rồi thử lại.', 'danger')
            return redirect_admin('season')
        try:
            ttl_cache_delete('players_raw')
            cache_set('_rz_players_all', None)
        except Exception:
            pass
        log_admin_action('Reset RP và mở mùa mới', 'season', details={'closed': sn, 'opened': next_sn, 'rp': 1000})
        flash(f'Đã mở Season {next_sn}. Tất cả tài khoản bắt đầu 1000 RP và cần đủ 5 trận mùa mới để hiện BXH.', 'success')
        return redirect_admin('season')
