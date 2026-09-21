"""Public GD2 ceremony art. Filenames and bucket path supplied by project owner.
Browser CSS uses progressive fallback; deployment cannot verify remote HTTP here.
Icons spritesheet requires cropping coordinates and is intentionally not shown whole.
"""
GD2_ASSET_BASE = "https://wlnvdfghatgeygecwrqb.supabase.co/storage/v1/object/public/pes-assets/LeBocThamGD2/"
GD2_ASSETS = {
    "crowd_silhouette": GD2_ASSET_BASE + "gd2_crowd_silhouette.webp",
    "ui_icons_spritesheet": GD2_ASSET_BASE + "gd2_ui_icons_spritesheet.webp",
    "coach_avatar_placeholder": GD2_ASSET_BASE + "gd2_coach_avatar_placeholder.webp",
    "club_reveal_frame": GD2_ASSET_BASE + "gd2_club_reveal_frame.webp",
    "club_reveal_stage": GD2_ASSET_BASE + "gd2_club_reveal_stage.webp",
    "random_club_card": GD2_ASSET_BASE + "gd2_random_club_card.webp",
    "stadium_lights_frame": GD2_ASSET_BASE + "gd2_stadium_lights_frame.webp",
    "draw_ceremony_stadium": GD2_ASSET_BASE + "gd2_draw_ceremony_stadium.webp",
}
