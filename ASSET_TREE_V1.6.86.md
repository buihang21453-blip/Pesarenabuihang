# Cây thư mục Assets — V1.6.86

Đặt asset hệ thống vào **`static/assets/`** trên GitHub. Không đặt CSS/JS vào đây.

```text
static/
├── css/                         # code CSS hiện có
├── js/                          # code JS hiện có
├── vendor/                      # thư viện hiện có
└── assets/                      # ẢNH HỆ THỐNG — đưa lên GitHub tại đây
    ├── pes-arena-logo.webp
    ├── login-background.webp
    ├── parsec-logo.webp
    ├── zcoin-logo.webp
    ├── podium_top3_reference.webp
    │
    ├── ranks/
    │   ├── <rank-slug>.webp
    │   └── <rank-slug>-card.webp
    │
    ├── rank_frames/
    │   ├── ga.png
    │   └── <rank-slug>.png
    │
    ├── shop/
    │   └── items/
    │       ├── avatar_frame_common.webp
    │       ├── avatar_frame_rare.webp
    │       ├── avatar_frame_epic.webp
    │       ├── avatar_frame_ice_elite.webp
    │       ├── avatar_frame_fire_warrior.webp
    │       ├── avatar_frame_legendary_crown.webp
    │       ├── profile_banner_stadium_blue.webp
    │       ├── profile_banner_stadium_premium.webp
    │       ├── profile_banner_ice.webp
    │       ├── profile_banner_neon_green.webp
    │       ├── profile_banner_fire.webp
    │       ├── profile_banner_legendary_red_purple.webp
    │       ├── profile_badge_rising_rookie.webp
    │       ├── profile_badge_rising_rookie_96.webp
    │       ├── profile_badge_pitch_warrior.webp
    │       ├── profile_badge_pitch_warrior_96.webp
    │       ├── profile_badge_fire_streak.webp
    │       ├── profile_badge_fire_streak_96.webp
    │       ├── profile_badge_elite_crown.webp
    │       ├── profile_badge_elite_crown_96.webp
    │       ├── profile_badge_legendary_diamond.webp
    │       ├── profile_badge_legendary_diamond_96.webp
    │       ├── name_style_neon_blue.webp
    │       ├── name_style_elite_purple.webp
    │       ├── name_style_champion_gold.webp
    │       ├── display_name_change_ticket.webp
    │       ├── discount_coupon_05.webp
    │       ├── discount_coupon_10.webp
    │       ├── discount_coupon_20.webp
    │       └── discount_coupon_30.webp
    │
    └── luckybox/
        ├── luckybox-pes-arena.webp
        ├── no-reward.webp
        └── exclusive/
            ├── profile-banner-bernardo-silva.webp
            ├── profile-banner-bruno-fernandes.webp
            ├── profile-banner-cristiano-ronaldo.webp
            ├── profile-banner-erling-haaland.webp
            ├── profile-banner-harry-kane.webp
            ├── profile-banner-khvicha-kvaratskhelia.webp
            ├── profile-banner-kylian-mbappe.webp
            ├── profile-banner-lamine-yamal.webp
            ├── profile-banner-lionel-messi.webp
            ├── profile-banner-michael-olise.webp
            ├── profile-banner-ousmane-dembele.webp
            ├── profile-banner-raphinha.webp
            ├── profile-banner-vinicius-junior.webp
            └── avatar-frame-royal-dominator.webp
```

## Cách hoạt động khi đang chuyển dữ liệu
Ví dụ `zcoin-logo.webp`:

1. Web gọi `/static/assets/zcoin-logo.webp`.
2. Nếu file đã có trên GitHub/Vercel -> dùng ngay Vercel.
3. Nếu file chưa có -> IMG tự fallback về Supabase `.../v1.14.41/zcoin-logo.webp`.

Shop và LuckyBox cũng tương tự nhưng fallback về namespace Supabase riêng tương ứng. Vì vậy có thể copy từng file/từng thư mục, không cần chuyển toàn bộ một lần.

## Nhóm Tournament/C1 legacy
Source hiện còn một số background được CSS tham chiếu trực tiếp từ Supabase (`Giaidau/C1mua1`, `LeBocThamGD2`, `v1.3.40`, `v1/Khung`). Chúng vẫn hoạt động trong giai đoạn chuyển tiếp. Không cần copy nhóm này ngay để V1.6.86 chạy.
