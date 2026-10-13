# PES Arena V1.6.81 optimization

## Completed in this pass
- Tournament live Host Ready: event-driven refresh + 90-second safety fallback.
- Global lobby chat: Realtime wake-up + sparse HTTP fallback.
- Ranking: narrower season stats query.
- Existing Invite, Room Chat, Room State, Match Found, Ready, Presence, reconnect/resync/fallback from V1.6.80 preserved.

## Deliberately deferred
- Supabase Storage/CDN migration, per owner request.
- True database-side Match History pagination: the UI already pages at 20 items, but the current server filters include enriched names, archived users, cancellation/forfeit rules and visibility rules. This needs a dedicated repository query/RPC to preserve exact behavior; V1.6.81 does not trade correctness for lower reads.
