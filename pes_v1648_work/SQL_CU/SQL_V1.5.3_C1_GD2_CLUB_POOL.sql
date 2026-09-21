-- PES ARENA V1.5.3 — C1 Giai đoạn 2
-- Pool Random CLB chính thức: đúng 24 CLB / 3 Pot.
-- App V1.5.3 tự đồng bộ pool khi Admin mở Random CLB Top 1–3 hoặc Random hạng 4–16.
-- File này bổ sung cột pot_no để Admin có thể truy vấn/báo cáo Pot CLB trực tiếp từ DB.
alter table if exists public.tournament_clubs
  add column if not exists pot_no int;

-- Không tự UPDATE theo tournament_id ở migration vì mỗi môi trường có UUID giải khác nhau.
-- Mapping chính thức:
-- Pot 1: Bayern, Real Madrid, Barcelona, PSG, Liverpool, Man City, Arsenal, Inter
-- Pot 2: Atlético Madrid, Man United, Aston Villa, Napoli, Roma, Fenerbahçe, Galatasaray, Dortmund
-- Pot 3: PSV, Villarreal, Real Betis, Lille, Lens, Como, Porto, RB Leipzig
