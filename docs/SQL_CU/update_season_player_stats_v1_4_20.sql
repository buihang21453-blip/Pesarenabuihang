-- PES Arena V1.4.20 - Repair Current Season Stats
-- Vá lỗi V1.4.19 đã copy W/D/L toàn thời gian từ users sang season_player_stats.
-- KHÔNG reset RP. KHÔNG xóa matches. KHÔNG sửa snapshot Season cũ.
-- Chỉ dựng lại W/D/L/total_matches/recent_form của MÙA HIỆN TẠI từ matches theo started_at.

DO $$
DECLARE
  v_setting jsonb;
  v_current_season integer := 1;
  v_started_at timestamptz;
BEGIN
  SELECT setting_value INTO v_setting
  FROM public.system_settings
  WHERE setting_key = 'rank_season_current'
  LIMIT 1;

  IF v_setting IS NOT NULL THEN
    v_current_season := COALESCE((v_setting->>'season_number')::integer, 1);
    v_started_at := NULLIF(v_setting->>'started_at','')::timestamptz;
  END IF;

  IF v_started_at IS NULL THEN
    SELECT started_at INTO v_started_at
    FROM public.rank_seasons
    WHERE season_number = v_current_season
    LIMIT 1;
  END IF;

  IF v_current_season > 1 AND v_started_at IS NULL THEN
    RAISE EXCEPTION 'Không tìm thấy started_at của Season %. Dừng sửa để tránh trộn dữ liệu mùa.', v_current_season;
  END IF;

  -- 1) Đưa users W/D/L về đúng thống kê của current season.
  -- RP tuyệt đối không bị đụng tới.
  UPDATE public.users
  SET wins = 0,
      draws = 0,
      losses = 0,
      total_matches = 0
  WHERE role = 'player';

  WITH participant_results AS (
    SELECT m.player1_id AS user_id,
           CASE WHEN m.score1 > m.score2 THEN 1 ELSE 0 END AS win,
           CASE WHEN m.score1 = m.score2 THEN 1 ELSE 0 END AS draw,
           CASE WHEN m.score1 < m.score2 THEN 1 ELSE 0 END AS loss
    FROM public.matches m
    WHERE m.status = 'confirmed'
      AND m.player1_id IS NOT NULL AND m.player2_id IS NOT NULL
      AND m.score1 IS NOT NULL AND m.score2 IS NOT NULL
      AND (v_started_at IS NULL OR m.created_at >= v_started_at)
    UNION ALL
    SELECT m.player2_id AS user_id,
           CASE WHEN m.score2 > m.score1 THEN 1 ELSE 0 END,
           CASE WHEN m.score2 = m.score1 THEN 1 ELSE 0 END,
           CASE WHEN m.score2 < m.score1 THEN 1 ELSE 0 END
    FROM public.matches m
    WHERE m.status = 'confirmed'
      AND m.player1_id IS NOT NULL AND m.player2_id IS NOT NULL
      AND m.score1 IS NOT NULL AND m.score2 IS NOT NULL
      AND (v_started_at IS NULL OR m.created_at >= v_started_at)
  ), totals AS (
    SELECT user_id,
           SUM(win)::integer AS wins,
           SUM(draw)::integer AS draws,
           SUM(loss)::integer AS losses,
           COUNT(*)::integer AS total_matches
    FROM participant_results
    GROUP BY user_id
  )
  UPDATE public.users u
  SET wins = t.wins,
      draws = t.draws,
      losses = t.losses,
      total_matches = t.total_matches
  FROM totals t
  WHERE u.id = t.user_id AND u.role = 'player';

  -- 2) Tạo/ghi đè record current season cho TOÀN BỘ player.
  -- RP lấy từ users hiện tại; W/D/L vừa được sửa đúng Season ở bước trên.
  INSERT INTO public.season_player_stats(
    season_number,user_id,username,display_name,rank_points,
    wins,draws,losses,total_matches,recent_form,updated_at
  )
  SELECT v_current_season,u.id,u.username,u.display_name,
         COALESCE(u.rank_points,1000),COALESCE(u.wins,0),COALESCE(u.draws,0),
         COALESCE(u.losses,0),COALESCE(u.total_matches,0),'[]'::jsonb,now()
  FROM public.users u
  WHERE u.role='player'
  ON CONFLICT(season_number,user_id) DO UPDATE SET
    username=excluded.username,
    display_name=excluded.display_name,
    rank_points=excluded.rank_points,
    wins=excluded.wins,
    draws=excluded.draws,
    losses=excluded.losses,
    total_matches=excluded.total_matches,
    recent_form='[]'::jsonb,
    updated_at=now();

  -- 3) Dựng lại đúng 5 trận gần nhất của current season.
  WITH participant_form AS (
    SELECT m.id AS match_id,m.created_at,m.player1_id AS user_id,
           CASE WHEN m.score1 > m.score2 THEN 'win' WHEN m.score1 < m.score2 THEN 'loss' ELSE 'draw' END AS form_code
    FROM public.matches m
    WHERE m.status='confirmed'
      AND m.player1_id IS NOT NULL AND m.player2_id IS NOT NULL
      AND m.score1 IS NOT NULL AND m.score2 IS NOT NULL
      AND (v_started_at IS NULL OR m.created_at >= v_started_at)
    UNION ALL
    SELECT m.id,m.created_at,m.player2_id,
           CASE WHEN m.score2 > m.score1 THEN 'win' WHEN m.score2 < m.score1 THEN 'loss' ELSE 'draw' END
    FROM public.matches m
    WHERE m.status='confirmed'
      AND m.player1_id IS NOT NULL AND m.player2_id IS NOT NULL
      AND m.score1 IS NOT NULL AND m.score2 IS NOT NULL
      AND (v_started_at IS NULL OR m.created_at >= v_started_at)
  ), ranked_form AS (
    SELECT pf.*,
           ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY created_at DESC,match_id DESC) AS rn
    FROM participant_form pf
  ), forms AS (
    SELECT user_id,
           jsonb_agg(
             jsonb_build_object(
               'code',form_code,
               'short',CASE form_code WHEN 'win' THEN 'T' WHEN 'loss' THEN 'B' ELSE 'H' END,
               'label',CASE form_code WHEN 'win' THEN 'Thắng' WHEN 'loss' THEN 'Bại' ELSE 'Hòa' END
             ) ORDER BY created_at DESC,match_id DESC
           ) FILTER (WHERE rn <= 5) AS recent_form
    FROM ranked_form
    GROUP BY user_id
  )
  UPDATE public.season_player_stats s
  SET recent_form=COALESCE(f.recent_form,'[]'::jsonb),updated_at=now()
  FROM forms f
  WHERE s.season_number=v_current_season AND s.user_id=f.user_id;
END $$;

-- Trigger mirror vẫn giữ để code Rank cũ hoạt động, nhưng sau migration này
-- users.wins/draws/losses chính là stats của CURRENT SEASON, không phải toàn sự nghiệp.
