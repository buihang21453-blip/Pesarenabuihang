from . import service


def register_routes(context):
    globals().update(context)
    service.configure(context)

    @app.route('/profile/parsec-id', methods=['POST'])
    @login_required
    def update_parsec_id():
        user = current_user()
        try:
            parsec_id = service.validate_parsec_id(request.form.get('parsec_id'))
            execute_query(
                db.table('users').update({'parsec_id': parsec_id}).eq('id', user.get('id')),
                'profile_update_parsec_id',
            )
            ttl_cache_delete(f"user:{user.get('id')}")
            cache_delete('_rz_current_user')
            cache_delete('_rz_users_map')
            flash('Đã lưu Parsec ID.' if parsec_id else 'Đã xóa Parsec ID.', 'success')
        except ValueError as exc:
            flash(str(exc), 'danger')
        except Exception as exc:
            app.logger.exception('update_parsec_id error: %s', exc)
            flash('Không thể lưu Parsec ID. Hãy kiểm tra đã chạy SQL V1.14.41.6.', 'danger')
        return redirect(url_for('profile', user_id=user.get('id')) + '#parsec-profile')

    @app.route('/room/<room_id>/parsec-link', methods=['POST'])
    @login_required
    def update_room_parsec_link(room_id):
        user = current_user()
        room = get_room(room_id)
        if not room:
            flash('Không tìm thấy phòng.', 'danger')
            return redirect(url_for('rooms'))
        if str(user.get('id')) != str(room.get('host_user_id')):
            flash('Chỉ chủ phòng được sửa hoặc xóa link Parsec.', 'danger')
            return redirect(url_for('room_detail', room_id=room_id))
        try:
            parsec_link = service.validate_parsec_link(request.form.get('parsec_link'))
            execute_query(
                db.table('match_rooms').update({
                    'parsec_link': parsec_link,
                    'updated_at': now_iso(),
                }).eq('id', room_id).eq('host_user_id', user.get('id')),
                'room_update_parsec_link',
            )
            cache_delete('_rz_rooms_all')
            ttl_cache_delete('rooms_raw')
            flash('Đã cập nhật link Parsec.' if parsec_link else 'Đã xóa link Parsec khỏi phòng.', 'success')
        except ValueError as exc:
            flash(str(exc), 'danger')
        except Exception as exc:
            app.logger.exception('update_room_parsec_link error room=%s: %s', room_id, exc)
            flash('Không thể cập nhật link Parsec. Hãy kiểm tra đã chạy SQL V1.14.41.6.', 'danger')
        return redirect(url_for('room_detail', room_id=room_id))
