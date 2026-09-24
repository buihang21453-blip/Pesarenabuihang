import unittest
from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader

class Top3RerollPot3KeepClubV1662Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).resolve().parents[1]
        cls.env=Environment(loader=FileSystemLoader(str(cls.root/'templates')))
        cls.env.globals['url_for']=lambda endpoint, **kw: f"/{endpoint}/" + "/".join(str(v) for v in kw.values())

    def _tour(self, finalized=False):
        return {'id':'tour','my_member':{'user_id':'u1'},'public_knockout':{
            'generated':True,'current_round':'qf','my_next':None,
            'tickets':[{'user_id':'u1','rank':1,'name':'HLV 1','club':'Como','remaining':1,'total':1,'club_finalized':finalized}],
            'rounds':{'qf':[],'sf':[],'final':[]}}}

    def test_player_sees_keep_current_club_button(self):
        tpl=self.env.get_template('tournament/components/knockout_dashboard.html')
        html=tpl.render(tournament=self._tour(),current_user=SimpleNamespace(id='u1',role='user',admin_level='none'))
        self.assertIn('Tôi chọn CLB này, không cần sử dụng vé Random',html)
        self.assertIn('tournament_league_top3_keep_club',html)

    def test_finalized_club_hides_reroll_buttons(self):
        tpl=self.env.get_template('tournament/components/knockout_dashboard.html')
        html=tpl.render(tournament=self._tour(True),current_user=SimpleNamespace(id='u1',role='user',admin_level='none'))
        self.assertIn('Đã chọn giữ CLB này',html)
        self.assertNotIn('🎲 Random lại CLB</button>',html)

    def test_reroll_backend_filters_strictly_to_pot3(self):
        src=(self.root/'modules'/'tournament_competition_parts'/'rewards.py').read_text()
        self.assertIn('C1_CLUB_POT_BY_NAME',src)
        self.assertIn('==3',src)
        self.assertIn('Không còn CLB Pot 3 trống',src)
        self.assertIn('club_finalized',src)
        self.assertIn('ticket_spent":False',src)

if __name__=='__main__': unittest.main()
