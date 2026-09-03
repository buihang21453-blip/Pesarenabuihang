-- PES Arena V1.4.7 - Configurable Rank Season Rewards
insert into public.system_settings(setting_key,setting_value,updated_at)
values ('rank_season_reward_config', jsonb_build_object(
  'top1', jsonb_build_object('zcoin',20000,'lucky_box',3),
  'top2', jsonb_build_object('zcoin',15000,'lucky_box',2),
  'top3', jsonb_build_object('zcoin',10000,'lucky_box',1)
), now())
on conflict (setting_key) do nothing;
