# PES Arena V1.6.88 — Realtime Final Optimization

- Quick Match: Realtime wake-up + authoritative HTTP; fallback 120s healthy / 45s disconnected.
- Global Chat page: removed 10s polling; Realtime primary; fallback 180s healthy / 45s disconnected.
- Room State: fallback 180s while room Realtime healthy; faster state-aware fallback only when disconnected.
- Room Chat: fallback 180s healthy / 12s disconnected.
- Invite: fallback 180s healthy; removed independent 15s watchdog.
- Announcement: added ANNOUNCEMENT_CHANGED Realtime signal; fallback 15 min.
- Tournament Host Ready: Realtime primary; fallback 5 min.
- HTTP business writes remain authoritative and unchanged.
- BXH hotfix, assets, database rules and gameplay business logic are preserved.
