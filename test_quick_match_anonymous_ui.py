from pathlib import Path


def test_quick_match_sender_response_hides_opponent_identity():
    source = Path('app.py').read_text(encoding='utf-8')
    block = source[source.index('def quick_match_invite():'):source.index('@app.route("/api/invites/quick-match/<invite_id>/status")')]
    assert '"opponent_name"' not in block
    assert '"points_gap"' not in block
    assert '"message": "Đã tìm thấy đối thủ. Đang chờ phản hồi..."' in block
    assert '"note": "Đã tìm thấy đối thủ phù hợp. Đang chờ phản hồi."' in block


def test_quick_match_button_does_not_reveal_name():
    source = Path('static/js/quick_match.js').read_text(encoding='utf-8')
    assert 'ĐANG CHỜ PHẢN HỒI' in source
    assert 'data.opponent_name' not in source
