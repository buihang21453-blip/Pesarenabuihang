# V1.2.50 — Room CSS ownership

- `room_v2.css`: layout/geometry of room only.
- `room/buttons.css`: sole visual owner of `.room-neon-btn`.
- `room/mode_cards.css`: sole owner of the 7 mode-logo image dimensions.
- `quick_match.css`: quick-match behavior/modal; legacy visual rules exclude `.room-neon-btn`.
- No per-logo `transform: scale(...)` is allowed for mode-card logos.
- All 7 mode logos use one fixed image box per breakpoint.
