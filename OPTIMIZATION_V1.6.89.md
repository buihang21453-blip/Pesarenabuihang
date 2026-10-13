# PES Arena V1.6.89 — Asset Path Mapping Hotfix

## Scope
Correct asset routing using the actual 243-file `assets.zip` tree supplied by the project owner.

## Correct mapping
- Main UI logical assets -> `v1/` (logo, login background, Parsec, Zcoin, podium, ranks).
- `shop/*` -> `v1.14.41/shop/*`.
- `luckybox/*` -> `v1.14.41/luckybox/*`.
- Explicit namespaces `Giaidau/`, `v1/`, `v1.3.40/`, `v1.14.41/`, `LeBocThamGD2/` remain unchanged.
- `team-logos/*` remains a separate Supabase bucket for fallback.

## Additional fix
`static/js/zcoin_rewards.js` now points to `/static/assets/v1/zcoin-logo.webp` instead of bypassing the router at `/static/assets/zcoin-logo.webp`.

## Verified against supplied archive
The supplied archive contains the main assets under `assets/v1/`, while `assets/v1.14.41/` contains Shop/LuckyBox content.

## Not changed
Realtime V1.6.88, BXH hotfix, DB/RPC, gameplay, Admin/Tournament logic and user-upload assets are unchanged.
