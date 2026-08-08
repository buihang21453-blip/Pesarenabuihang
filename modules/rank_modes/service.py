import json
import random
import time
from copy import deepcopy
from .catalog import DEFAULT_MODE_CONFIGS, MODE_ORDER, RANK_RANDOM, RANDOM3_PICK1
_CONTEXT={}; SETTING_KEY='rank_mode_configs_v1'
_CONFIG_CACHE={'value':None,'expires_at':0.0}; CONFIG_CACHE_TTL_SECONDS=8.0
EXPORTED_NAMES=('save_rank_mode_configs','get_rank_mode_configs','get_rank_mode','rank_mode_catalog_for_players','check_rank_mode_eligibility','rank_mode_eligibility_for_room','get_user_rank_mode_unlocks','list_rank_mode_user_unlocks','save_user_rank_mode_unlocks','resolve_series_result','calculate_mode_rp','mode_rp_audit_payload','mode_series_rp_audit_payload','is_series_mode','legacy_team_tier_for_mode','normalize_rank_mode_code','resolve_enabled_rank_mode','default_rank_mode_code','default_rank_room_team_tier','required_daily_games_for_mode','rank_mode_daily_quota_status','assert_rank_mode_daily_quota','MODE_ORDER','RANK_RANDOM','RANDOM3_PICK1')
def configure(context):
 global _CONTEXT; _CONTEXT=context
def _deep_merge(base, override):
 r=deepcopy(base)
 for k,v in (override or {}).items(): r[k]=_deep_merge(r[k],v) if isinstance(v,dict) and isinstance(r.get(k),dict) else v
 return r
def normalize_rank_mode_code(value):
 value=str(value or '').strip().lower(); return {'smart_random':RANK_RANDOM,'random':RANK_RANDOM}.get(value,value if value in DEFAULT_MODE_CONFIGS else RANK_RANDOM)

def _request_cache():
 has_request_context=_CONTEXT.get('has_request_context'); g=_CONTEXT.get('g')
 if callable(has_request_context) and has_request_context() and g is not None:
  return g
 return None

def save_rank_mode_configs(configs):
 clean={}
 for code in MODE_ORDER:
  incoming=(configs or {}).get(code) or {}
  clean[code]=_deep_merge(DEFAULT_MODE_CONFIGS[code],incoming)
 execute_query=_CONTEXT.get('execute_query'); db=_CONTEXT.get('db')
 if not execute_query or db is None: raise RuntimeError('Database chưa sẵn sàng')
 payload={'setting_key':SETTING_KEY,'setting_value':json.dumps(clean,ensure_ascii=False)}
 execute_query(db.table('system_settings').upsert(payload,on_conflict='setting_key'),'save_rank_mode_configs',attempts=2)
 _CONFIG_CACHE['value']=deepcopy(clean); _CONFIG_CACHE['expires_at']=time.monotonic()+CONFIG_CACHE_TTL_SECONDS
 req=_request_cache()
 if req is not None: setattr(req,'_rank_mode_configs_cache',deepcopy(clean))
 return clean

def get_rank_mode_configs():
 req=_request_cache()
 if req is not None:
  cached=getattr(req,'_rank_mode_configs_cache',None)
  if isinstance(cached,dict): return deepcopy(cached)
 now=time.monotonic()
 if isinstance(_CONFIG_CACHE.get('value'),dict) and now < float(_CONFIG_CACHE.get('expires_at') or 0):
  configs=deepcopy(_CONFIG_CACHE['value'])
  if req is not None: setattr(req,'_rank_mode_configs_cache',deepcopy(configs))
  return configs
 configs=deepcopy(DEFAULT_MODE_CONFIGS); execute_query=_CONTEXT.get('execute_query'); db=_CONTEXT.get('db')
 if execute_query and db is not None:
  try:
   result=execute_query(db.table('system_settings').select('setting_value').eq('setting_key',SETTING_KEY).limit(1),'get_rank_mode_configs',attempts=1)
   raw=((result.data or [{}])[0]).get('setting_value'); raw=json.loads(raw) if isinstance(raw,str) else raw
   if isinstance(raw,dict):
    for code in MODE_ORDER:
     if isinstance(raw.get(code),dict):
      configs[code]=_deep_merge(configs[code],raw[code])
      canonical_rp=(DEFAULT_MODE_CONFIGS.get(code) or {}).get('rp') or {}
      if canonical_rp.get('formula_version') and ((raw.get(code) or {}).get('rp') or {}).get('formula_version')!=canonical_rp.get('formula_version'):
       configs[code]['rp']=deepcopy(canonical_rp)
  except Exception: pass
 _CONFIG_CACHE['value']=deepcopy(configs); _CONFIG_CACHE['expires_at']=now+CONFIG_CACHE_TTL_SECONDS
 if req is not None: setattr(req,'_rank_mode_configs_cache',deepcopy(configs))
 return configs
def get_rank_mode(code): return get_rank_mode_configs()[normalize_rank_mode_code(code)]

def default_rank_mode_code():
 configs=get_rank_mode_configs()
 for code in MODE_ORDER:
  if bool((configs.get(code) or {}).get('enabled',True)):
   return code
 return RANK_RANDOM

def resolve_enabled_rank_mode(value):
 code=normalize_rank_mode_code(value)
 configs=get_rank_mode_configs()
 if bool((configs.get(code) or {}).get('enabled',False)):
  return code
 return default_rank_mode_code()

def default_rank_room_team_tier():
 return legacy_team_tier_for_mode(default_rank_mode_code())


def _is_admin_account(user):
 is_admin_user=_CONTEXT.get('is_admin_user')
 if callable(is_admin_user):
  try: return bool(is_admin_user(user))
  except Exception: pass
 return bool(user and (user.get('role')=='admin' or user.get('admin_level')))

def get_user_rank_mode_unlocks(user_id):
 """Trả về tập mã chế độ được Admin mở riêng cho một tài khoản."""
 if not user_id: return set()
 execute_query=_CONTEXT.get('execute_query'); db=_CONTEXT.get('db')
 if not execute_query or db is None: return set()
 cache_key=f'rank_mode_unlocks:{user_id}'
 has_request_context=_CONTEXT.get('has_request_context'); g=_CONTEXT.get('g')
 if callable(has_request_context) and has_request_context() and g is not None:
  cache=getattr(g,'_rank_mode_unlock_cache',None)
  if cache is None:
   cache={}; setattr(g,'_rank_mode_unlock_cache',cache)
  if cache_key in cache: return set(cache[cache_key])
 try:
  result=execute_query(db.table('rank_mode_user_unlocks').select('mode_code').eq('user_id',user_id).eq('is_unlocked',True),'get_user_rank_mode_unlocks',attempts=1)
  modes={normalize_rank_mode_code(row.get('mode_code')) for row in (result.data or []) if row.get('mode_code') in DEFAULT_MODE_CONFIGS}
 except Exception:
  modes=set()
 if callable(has_request_context) and has_request_context() and g is not None:
  getattr(g,'_rank_mode_unlock_cache',{})[cache_key]=set(modes)
 return modes

def list_rank_mode_user_unlocks():
 execute_query=_CONTEXT.get('execute_query'); db=_CONTEXT.get('db')
 if not execute_query or db is None: return {}
 try:
  result=execute_query(db.table('rank_mode_user_unlocks').select('user_id,mode_code,is_unlocked').eq('is_unlocked',True),'list_rank_mode_user_unlocks',attempts=1)
 except Exception:
  return {}
 output={}
 for row in (result.data or []):
  user_id=str(row.get('user_id') or '')
  code=str(row.get('mode_code') or '')
  if user_id and code in DEFAULT_MODE_CONFIGS: output.setdefault(user_id,set()).add(code)
 return output

def save_user_rank_mode_unlocks(user_id, mode_codes, updated_by=None):
 execute_query=_CONTEXT.get('execute_query'); db=_CONTEXT.get('db')
 if not execute_query or db is None: raise RuntimeError('Database chưa sẵn sàng')
 valid=[code for code in MODE_ORDER if code in set(mode_codes or [])]
 execute_query(db.table('rank_mode_user_unlocks').delete().eq('user_id',user_id),'delete_user_rank_mode_unlocks',attempts=2)
 if valid:
  rows=[{'user_id':user_id,'mode_code':code,'is_unlocked':True,'updated_by':updated_by} for code in valid]
  execute_query(db.table('rank_mode_user_unlocks').insert(rows),'save_user_rank_mode_unlocks',attempts=2)
 return set(valid)

def _completed_rank_matches(user):
 user=user or {}
 # Dữ liệu chuẩn của PES Arena là tổng W/H/B. Ưu tiên nguồn này để tránh
 # total_matches cũ/chưa đồng bộ làm khóa sai chế độ.
 if any(key in user for key in ('wins','draws','losses')):
  try:
   return max(0,int(user.get('wins') or 0)+int(user.get('draws') or 0)+int(user.get('losses') or 0))
  except (TypeError,ValueError):
   pass
 for key in ('total_matches','matches_played','rank_matches','completed_matches'):
  try:
   value=int(user.get(key) or 0)
   if value: return value
  except (TypeError,ValueError): pass
 return 0
def check_rank_mode_eligibility(mode_code,user,opponent=None):
 mode_code=normalize_rank_mode_code(mode_code); mode=get_rank_mode(mode_code); reasons=[]
 if not mode.get('enabled',True): reasons.append('Chế độ đang tạm tắt')
 user=user or {}
 admin_unlocked=_is_admin_account(user)
 manual_unlocked=mode_code in get_user_rank_mode_unlocks(user.get('id'))
 bypass_requirements=admin_unlocked or manual_unlocked
 user_rp=int(user.get('rank_points') or user.get('rating') or user.get('rp') or 0); min_rp=int(mode.get('min_rp') or 0)
 if not bypass_requirements and user_rp<min_rp: reasons.append(f'Cần tối thiểu {min_rp:,} RP'.replace(',','.'))
 played=_completed_rank_matches(user); min_matches=int(mode.get('min_matches') or 0)
 if not bypass_requirements and played<min_matches: reasons.append(f'Cần hoàn thành {min_matches} trận Rank')
 max_gap=int(mode.get('max_rp_gap') or 0)
 if opponent and max_gap>0:
  opponent_rp=int((opponent or {}).get('rank_points') or (opponent or {}).get('rating') or (opponent or {}).get('rp') or 0)
  if abs(user_rp-opponent_rp)>max_gap: reasons.append(f'Hai người không được chênh quá {max_gap} RP')
 return {'eligible':not reasons,'reasons':reasons,'mode':mode,'admin_unlocked':admin_unlocked,'manual_unlocked':manual_unlocked}
def rank_mode_eligibility_for_room(mode_code,host,guest=None):
 h=check_rank_mode_eligibility(mode_code,host,guest); g=check_rank_mode_eligibility(mode_code,guest,host) if guest else {'eligible':True,'reasons':[]}; reasons=list(h['reasons'])
 for x in g['reasons']:
  if x not in reasons: reasons.append(x)
 return {'eligible':h['eligible'] and g['eligible'],'reasons':reasons}
def required_daily_games_for_mode(mode_code):
 mode=get_rank_mode(normalize_rank_mode_code(mode_code))
 try: return max(1,int(mode.get('max_games') or 1))
 except (TypeError,ValueError): return 1

def rank_mode_daily_quota_status(mode_code,*user_ids,continuation=False):
 required=1 if continuation else required_daily_games_for_mode(mode_code)
 status_fn=_CONTEXT.get('rank_daily_status')
 if not callable(status_fn):
  return {'eligible':True,'required_games':required,'continuation':bool(continuation),'players':{},'reasons':[]}
 players={}; reasons=[]
 for user_id in user_ids:
  if not user_id: continue
  status=status_fn(user_id) or {}
  if not status.get('enabled',True):
   players[str(user_id)]={**status,'required_games':required,'enough':True}
   continue
  remaining=int(status.get('games_remaining') or 0)
  enough=remaining>=required
  players[str(user_id)]={**status,'required_games':required,'enough':enough}
  if not enough:
   reasons.append(f'Cần còn ít nhất {required} lượt trận trong ngày để bắt đầu chế độ này (hiện còn {remaining})')
 return {'eligible':not reasons,'required_games':required,'continuation':bool(continuation),'players':players,'reasons':reasons}

def assert_rank_mode_daily_quota(mode_code,*user_ids,continuation=False):
 result=rank_mode_daily_quota_status(mode_code,*user_ids,continuation=continuation)
 if not result.get('eligible'):
  raise ValueError('; '.join(result.get('reasons') or ['Không đủ lượt trận Rank trong ngày.']))
 return result

def rank_mode_catalog_for_players(host,guest=None):
 # Daily status does not depend on the mode; only required_games does. Load it
 # once per player instead of 6 modes x 2 players. This removes the largest
 # Supabase N+1 chain from room rendering.
 status_fn=_CONTEXT.get('rank_daily_status')
 host_status=status_fn((host or {}).get('id')) if callable(status_fn) and (host or {}).get('id') else None
 guest_status=status_fn((guest or {}).get('id')) if callable(status_fn) and (guest or {}).get('id') else None
 output=[]
 for c in MODE_ORDER:
  base=rank_mode_eligibility_for_room(c,host,guest)
  required=required_daily_games_for_mode(c)
  reasons=list(base.get('reasons') or [])
  for status in (host_status,guest_status):
   if not status or not status.get('enabled',True): continue
   remaining=int(status.get('games_remaining') or 0)
   if remaining < required:
    reason=f'Cần còn ít nhất {required} lượt trận trong ngày để bắt đầu chế độ này (hiện còn {remaining})'
    if reason not in reasons: reasons.append(reason)
  output.append({**get_rank_mode(c),**{'eligible':not reasons,'lock_reasons':reasons,'required_daily_games':required}})
 return output
def is_series_mode(mode_code): return get_rank_mode(mode_code).get('series_type')!='single'
def legacy_team_tier_for_mode(mode_code): return 'smart_random' if normalize_rank_mode_code(mode_code)==RANK_RANDOM else normalize_rank_mode_code(mode_code)
def resolve_series_result(mode_code,games,forfeiting_user_id=None):
 mode=get_rank_mode(mode_code); clean=[g for g in (games or []) if g.get('status','completed')=='completed']; p1=sum(g.get('winner_side')=='player1' for g in clean); p2=sum(g.get('winner_side')=='player2' for g in clean); draws=sum(g.get('winner_side')=='draw' for g in clean)
 if forfeiting_user_id: return {'status':'completed','reason':'forfeit','forfeiting_user_id':forfeiting_user_id,'score':'0-2','p1_wins':p1,'p2_wins':p2,'draws':draws}
 if mode.get('series_type')=='aggregate_two_legs':
  if len(clean)<2:return {'status':'playing','p1_wins':p1,'p2_wins':p2,'draws':draws}
  a=sum(int(g.get('player1_score') or 0) for g in clean[:2]); b=sum(int(g.get('player2_score') or 0) for g in clean[:2]); w='player1' if a>b else 'player2' if b>a else 'draw'; return {'status':'completed','reason':'aggregate','winner_side':w,'aggregate_score':f'{a}-{b}','p1_wins':p1,'p2_wins':p2,'draws':draws}
 req=int(mode.get('wins_required') or 2)
 if p1>=req or p2>=req:
  w='player1' if p1>p2 else 'player2'; return {'status':'completed','reason':'wins_required','winner_side':w,'score':f'{max(p1,p2)}-{min(p1,p2)}','p1_wins':p1,'p2_wins':p2,'draws':draws}
 if len(clean)>=int(mode.get('max_games') or 3):
  w='player1' if p1>p2 else 'player2' if p2>p1 else 'draw'; return {'status':'completed','reason':'max_games','winner_side':w,'score':f'{p1}-{p2}','p1_wins':p1,'p2_wins':p2,'draws':draws}
 return {'status':'playing','p1_wins':p1,'p2_wins':p2,'draws':draws}
def _mode_randint(rng, minimum, maximum):
 return int((rng or random).randint(int(minimum), int(maximum)))

def _mode_draw_points(player1_rp, player2_rp, rng):
 """Luật hòa dùng chung: <500 RP thì cả hai random +1..+6; >=500 chỉ người thấp RP được random."""
 p1=int(player1_rp or 0); p2=int(player2_rp or 0)
 if abs(p1-p2)>=500:
  if p1<p2: return _mode_randint(rng,1,6),0
  if p2<p1: return 0,_mode_randint(rng,1,6)
 return _mode_randint(rng,1,6),_mode_randint(rng,1,6)

def _with_variance(base, rng):
 variance=_mode_randint(rng,-2,3)
 return int(base),int(variance),int(base)+int(variance)

def calculate_mode_rp(mode_code,series_result,winner_side=None,forfeit=False,player1_rp=0,player2_rp=0,rng=None):
 """Tính RP cho Series.

 Random/3 chọn 1 vẫn dùng ``rank_current``. Các mode Series dùng RP cơ sở +
 random(-2,+3) đúng một lần cho mỗi người. Hòa dùng luật +1..+6 riêng.
 Bỏ cuộc trong Series: người bỏ cuộc -20 RP, người còn lại +20 RP, không random.
 """
 mode=get_rank_mode(mode_code); rp=mode.get('rp') or {}; rng=rng or random
 if mode.get('series_type')=='single': return {'formula':'rank_current'}
 if forfeit or series_result.get('reason')=='forfeit':
  offender=series_result.get('forfeiting_side')
  win_points=int(rp.get('forfeit_win') if rp.get('forfeit_win') is not None else 20)
  loss_points=int(rp.get('forfeit_loss') if rp.get('forfeit_loss') is not None else -20)
  result={'key':'forfeit','forfeit_win':win_points,'forfeit_loss':loss_points,'winner':win_points,'loser':loss_points}
  if offender in ('player1','player2'):
   result.update({'player1':loss_points if offender=='player1' else win_points,'player2':loss_points if offender=='player2' else win_points})
  return result
 if series_result.get('winner_side')=='draw' or not winner_side:
  p1,p2=_mode_draw_points(player1_rp,player2_rp,rng)
  return {'player1':p1,'player2':p2,'key':'draw','player1_base':None,'player1_variance':None,'player1_final':p1,'player2_base':None,'player2_variance':None,'player2_final':p2}

 code=normalize_rank_mode_code(mode_code)
 p1wins=int(series_result.get('p1_wins') or 0); p2wins=int(series_result.get('p2_wins') or 0); draws=int(series_result.get('draws') or 0)
 if code=='home_away':
  if max(p1wins,p2wins)>=2:
   key='win_both'; win_base=int(rp.get('win_both') or 30); lose_base=int(rp.get('lose_both') or -28)
  elif draws>=1 and max(p1wins,p2wins)>=1:
   key='one_win_one_draw'; win_base=int(rp.get('one_win_one_draw_win') or 22); lose_base=int(rp.get('one_win_one_draw_loss') or -22)
  else:
   key='split_aggregate'; win_base=int(rp.get('split_aggregate_win') or 15); lose_base=int(rp.get('split_aggregate_loss') or -10)
 else:
  score=str(series_result.get('score') or '')
  if score=='2-0': key='2-0'; win_base=int(rp.get('win_2_0') or 32); lose_base=int(rp.get('lose_0_2') or -28)
  else: key='2-1'; win_base=int(rp.get('win_2_1') or 25); lose_base=int(rp.get('lose_1_2') or -23)

 wb,wv,wf=_with_variance(win_base,rng); lb,lv,lf=_with_variance(lose_base,rng)
 result={'winner':wf,'loser':lf,'key':key,'winner_base':wb,'winner_variance':wv,'winner_final':wf,'loser_base':lb,'loser_variance':lv,'loser_final':lf}
 if winner_side=='player1':
  result.update({'player1':wf,'player2':lf,'player1_base':wb,'player1_variance':wv,'player1_final':wf,'player2_base':lb,'player2_variance':lv,'player2_final':lf})
 elif winner_side=='player2':
  result.update({'player1':lf,'player2':wf,'player1_base':lb,'player1_variance':lv,'player1_final':lf,'player2_base':wb,'player2_variance':wv,'player2_final':wf})
 return result

def mode_rp_audit_payload(rp_result):
 """Các cột audit chỉ lưu Supabase; UI người chơi không sử dụng chúng."""
 rp_result=rp_result or {}
 return {
  'rp_base1':rp_result.get('player1_base'), 'rp_variance1':rp_result.get('player1_variance'), 'rp_final1':rp_result.get('player1_final',rp_result.get('player1')),
  'rp_base2':rp_result.get('player2_base'), 'rp_variance2':rp_result.get('player2_variance'), 'rp_final2':rp_result.get('player2_final',rp_result.get('player2')),
 }


def mode_series_rp_audit_payload(rp_result):
 """Payload tương ứng bảng match_series, chỉ lưu Supabase."""
 rp_result=rp_result or {}
 return {
  'rp_base_player1':rp_result.get('player1_base'), 'rp_variance_player1':rp_result.get('player1_variance'), 'rp_final_player1':rp_result.get('player1_final',rp_result.get('player1')),
  'rp_base_player2':rp_result.get('player2_base'), 'rp_variance_player2':rp_result.get('player2_variance'), 'rp_final_player2':rp_result.get('player2_final',rp_result.get('player2')),
 }
