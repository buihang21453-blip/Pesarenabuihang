-- PES Arena V1.3.35 — RP Series audit fields
-- Chạy 1 lần trong Supabase SQL Editor trước khi deploy source V1.3.35.
-- Các cột audit này chỉ dùng backend/Admin/debug; giao diện người chơi chỉ đọc delta/rp_final tổng.

begin;

alter table public.matches
  add column if not exists rp_base1 integer,
  add column if not exists rp_variance1 integer,
  add column if not exists rp_final1 integer,
  add column if not exists rp_base2 integer,
  add column if not exists rp_variance2 integer,
  add column if not exists rp_final2 integer;

alter table public.match_series
  add column if not exists rp_base_player1 integer,
  add column if not exists rp_variance_player1 integer,
  add column if not exists rp_final_player1 integer,
  add column if not exists rp_base_player2 integer,
  add column if not exists rp_variance_player2 integer,
  add column if not exists rp_final_player2 integer;

comment on column public.matches.rp_base1 is 'RP co so player1; chi dung audit Supabase';
comment on column public.matches.rp_variance1 is 'Bien dong RP player1; series -2..+3, hoa de null';
comment on column public.matches.rp_final1 is 'RP cuoi player1; UI nguoi choi chi hien tong nay/delta1';
comment on column public.matches.rp_base2 is 'RP co so player2; chi dung audit Supabase';
comment on column public.matches.rp_variance2 is 'Bien dong RP player2; series -2..+3, hoa de null';
comment on column public.matches.rp_final2 is 'RP cuoi player2; UI nguoi choi chi hien tong nay/delta2';

comment on column public.match_series.rp_base_player1 is 'RP co so series player1; audit only';
comment on column public.match_series.rp_variance_player1 is 'RP variance series player1; audit only';
comment on column public.match_series.rp_final_player1 is 'RP final series player1; audit only';
comment on column public.match_series.rp_base_player2 is 'RP co so series player2; audit only';
comment on column public.match_series.rp_variance_player2 is 'RP variance series player2; audit only';
comment on column public.match_series.rp_final_player2 is 'RP final series player2; audit only';

commit;
