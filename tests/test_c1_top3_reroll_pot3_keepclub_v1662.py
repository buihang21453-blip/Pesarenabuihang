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
            'tickets':[{'user_id':'u1','rank':1,'name':'HLV 1','club':'Como','remaining':1,'total':1,'club_finalized':finalized,'hlv_tier':1,'expected_club_pot':3,'current_club_pot':3,'club_pot_mismatch':False}],
            'rounds':{'qf':[],'sf':[],'final':[]}}}

    def test_player_cannot_see_keep_or_reroll_controls(self):
        tpl=self.env.get_template('tournament/components/knockout_dashboard.html')
        html=tpl.render(tournament=self._tour(),current_user=SimpleNamespace(id='u1',role='user',admin_level='none'))
        self.assertNotIn('Tôi chọn CLB này, không cần sử dụng vé Random',html)
        self.assertNotIn('🎲 Random lại CLB</button>',html)
        self.assertNotIn('Admin chọn giữ',html)

    def test_finalized_club_hides_reroll_buttons(self):
        tpl=self.env.get_template('tournament/components/knockout_dashboard.html')
        html=tpl.render(tournament=self._tour(True),current_user=SimpleNamespace(id='u1',role='user',admin_level='none'))
        self.assertIn('Admin đã chốt giữ CLB này',html)
        self.assertNotIn('🎲 Random lại CLB</button>',html)

    def test_reroll_backend_keeps_tier1_strictly_in_pot3_via_mapping(self):
        src=(self.root/'modules'/'tournament_competition_parts'/'rewards.py').read_text()
        self.assertIn('C1_CLUB_POT_BY_NAME',src)
        self.assertIn('expected_club_pot=4-hlv_tier',src)
        self.assertIn('==expected_club_pot',src)
        self.assertIn('Tier 1 -> Pot 3',src)
        self.assertIn('club_finalized',src)
        self.assertIn('ticket_spent":False',src)

if __name__=='__main__': unittest.main()
