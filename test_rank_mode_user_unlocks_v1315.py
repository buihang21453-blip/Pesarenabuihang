from modules.rank_modes import service

class Result:
    def __init__(self, data=None): self.data=data or []

class Query:
    def __init__(self, rows): self.rows=rows
    def select(self,*a,**k): return self
    def eq(self,key,value):
        self.rows=[r for r in self.rows if r.get(key)==value]
        return self
    def limit(self,*a,**k): return self

class DB:
    def __init__(self, rows): self.rows=rows
    def table(self,name): return Query(list(self.rows.get(name,[])))

def execute_query(query,*a,**k): return Result(query.rows)

service.configure({
    'db': DB({'rank_mode_user_unlocks':[{'user_id':'u1','mode_code':'bo3','is_unlocked':True}]}),
    'execute_query': execute_query,
    'is_admin_user': lambda u: bool(u and u.get('role')=='admin'),
})
service.get_rank_mode=lambda code: {'code':code,'enabled':True,'min_rp':1500,'min_matches':20,'max_rp_gap':500}

admin={'id':'a1','role':'admin','rank_points':0,'wins':0,'draws':0,'losses':0}
player={'id':'u1','role':'player','rank_points':100,'wins':0,'draws':0,'losses':0}
locked={'id':'u2','role':'player','rank_points':100,'wins':0,'draws':0,'losses':0}
assert service.check_rank_mode_eligibility('bo3',admin)['eligible']
assert service.check_rank_mode_eligibility('bo3',player)['eligible']
assert not service.check_rank_mode_eligibility('bo3',locked)['eligible']
assert service.check_rank_mode_eligibility('bo3',player).get('manual_unlocked') is True
print('rank mode user unlock tests: OK')
