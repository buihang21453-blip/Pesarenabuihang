from pathlib import Path

CSS = Path("static/css/gaming_neon_buttons.css").read_text(encoding="utf-8")


def test_global_skin_does_not_target_bare_button_elements():
    # Structural UI cards/tabs are also implemented as <button>; bare-button targeting
    # is what caused Room mode cards to inherit the Gaming Neon background in V1.3.80.
    assert "  button,\n  .btn," not in CSS
    assert ":is(.arena-room-v2,.invite-banner,.player-main) :is(button,.btn" not in CSS


def test_room_mode_cards_are_not_action_button_targets():
    # These are component surfaces, not action buttons. They must keep their own CSS.
    for structural_class in (
        ".room-master-mode-card",
        ".room-mode-select-btn",
        ".series-club-btn",
    ):
        # Presence is documentation-only in STRUCTURAL BUTTON SAFETY, and they must not
        # appear in any selector that assigns Gaming Neon background/border/glow.
        blocks = CSS.split("}")
        offenders = [b for b in blocks if structural_class in b and any(x in b for x in ("background:", "border-color:", "box-shadow:"))]
        assert offenders == []


def test_real_room_action_buttons_remain_in_neon_scope():
    # Standard Room actions carry .btn/.arena-btn and are therefore covered by the
    # explicit action scope; special CTA classes also keep dedicated final colors.
    assert "  .btn," in CSS
    assert "  .arena-btn," in CSS
    for special in (
        ".room-submit-result-btn",
        ".room-guest-card-kick-btn",
        ".room-center-random-trigger",
    ):
        assert special in CSS


def test_parsec_exclusion_remains_present():
    assert ".parsec-room-panel" in CSS
    assert "#parsec-profile" in CSS
