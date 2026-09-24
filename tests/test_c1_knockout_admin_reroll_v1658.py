import unittest
from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader


class KnockoutAdminRerollV1658Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.env = Environment(loader=FileSystemLoader(str(cls.root / 'templates')))
        cls.env.globals['url_for'] = lambda endpoint, **kw: f"/{endpoint}/" + "/".join(str(v) for v in kw.values())

    def _tournament(self):
        return {
            'id': 'tour', 'my_member': None,
            'public_knockout': {
                'generated': True, 'current_round': 'qf', 'my_next': None,
                'tickets': [{'user_id':'u1','rank':1,'name':'HLV 1','club':'Como','remaining':1,'total':1}],
                'rounds': {'qf': [], 'sf': [], 'final': []},
            }
        }

    def test_admin_sees_proxy_reroll_button(self):
        tpl = self.env.get_template('tournament/components/knockout_dashboard.html')
        html = tpl.render(tournament=self._tournament(), current_user=SimpleNamespace(id='admin', role='admin'))
        self.assertIn('Admin Random hộ', html)
        self.assertIn('admin_tournament_league_top3_reroll_club_for', html)
        self.assertIn('name="user_id" value="u1"', html)

    def test_normal_viewer_does_not_see_admin_proxy_button(self):
        tpl = self.env.get_template('tournament/components/knockout_dashboard.html')
        html = tpl.render(tournament=self._tournament(), current_user=SimpleNamespace(id='u9', role='user'))
        self.assertNotIn('Admin Random hộ', html)

    def test_backend_uses_same_guard_for_player_and_admin(self):
        source = (self.root/'modules'/'tournament_competition_parts'/'rewards.py').read_text(encoding='utf-8')
        self.assertIn('def _league_top3_reroll_for', source)
        self.assertIn("@app.post('/admin/tournaments/<tournament_id>/league-top3/reroll-club-for')", source)
        self.assertIn('return _league_top3_reroll_for(tournament_id,uid,admin_actor=admin_uid)', source)
        self.assertIn('{"pending","scheduled","cancelled"}', source)
        self.assertIn('actor_role', source)


if __name__ == '__main__':
    unittest.main()
