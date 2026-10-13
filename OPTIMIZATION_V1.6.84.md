# PES Arena V1.6.84 — Admin + Tournament Query Optimization

## Admin
- `/admin` no longer performs duplicate-room cleanup during GET.
- Recent matches are limited in Supabase (80 rows); playing/disputed are filtered in DB.
- Recent rooms are limited in Supabase; active/cancelled room sets are filtered in DB.
- Match report filters the requested date range in Supabase before rows reach Vercel.
- Match-report room mode lookup reads only `match_id,team_tier` in chunks.
- Eight migration probes are cached for 10 minutes per warm instance.
- Admin activity log reads explicit columns.

## Tournament
- Read-heavy Tournament queries now use explicit column lists for tournaments, registrations, members, matches and unmatched fees.
- Tournament landing center room query reads only fields used by the UI.
- Admin Tournament context uses a short 15-second process TTL to avoid rebuilding the same query bundle on every Admin request.

## Compatibility
- No gameplay write/action route was intentionally changed.
- V1.6.83 Players/BXH RPC behavior remains intact.
- Asset strategy is unchanged.
