"""Chuẩn hóa ảnh vật phẩm Shop sang WebP tối ưu cho web.

Ví dụ:
    python tools/process_shop_assets.py /duong-dan/Cuahang static/shop/items
"""

from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageOps

ASSETS = {
    "avatar_frame_common": ("Khung avatar/Khung_Avatar_Phothong.png", "icon", 0.92),
    "avatar_frame_rare": ("Khung avatar/Khung_Avatar_Hiem.png", "icon", 0.92),
    "avatar_frame_epic": ("Khung avatar/Khung_Avatar_Suthi.png", "icon", 0.92),
    "avatar_frame_ice_elite": ("Khung avatar/Khung_banglamtinhanh.png", "icon", 0.92),
    "avatar_frame_fire_warrior": ("Khung avatar/Khung_luachienthan.png", "icon", 0.92),
    "avatar_frame_legendary_crown": ("Khung avatar/Khung_Huyenthoaivuongmieng.png", "icon", 0.92),
    "profile_banner_stadium_blue": ("Banner/profile_banner_common_01.webp.png", "banner", 1.0),
    "profile_banner_stadium_premium": ("Banner/profile_banner_premium_01.webp.png", "banner", 1.0),
    "profile_banner_ice": ("Banner/Banner Băng Lam.png", "banner", 1.0),
    "profile_banner_neon_green": ("Banner/Banner Xanh Lục.png", "banner", 1.0),
    "profile_banner_fire": ("Banner/Banner_dolua.png", "banner", 1.0),
    "profile_banner_legendary_red_purple": ("Banner/Banner Huyền Thoại Đỏ Tím.png", "banner", 1.0),
    "profile_badge_rising_rookie": ("Huy_Hieu/Tân_Binh_Sáng_Giá.png", "badge", 0.76),
    "profile_badge_pitch_warrior": ("Huy_Hieu/Chiến Binh Sân Cỏ.png", "badge", 0.74),
    "profile_badge_fire_streak": ("Huy_Hieu/Chuỗi Thắng Rực Lửa.png", "badge", 0.76),
    "profile_badge_elite_crown": ("Huy_Hieu/Vương Miện Elite.png", "badge", 0.76),
    "profile_badge_legendary_diamond": ("Huy_Hieu/Huyền Thoại Kim Cương.png", "badge", 0.76),
    "name_style_neon_blue": ("The-Doi_mau-ten/name_color_neon_blue_01.png", "card", 0.84),
    "name_style_elite_purple": ("The-Doi_mau-ten/name_color_elite_purple_01.png", "card", 0.84),
    "name_style_champion_gold": ("The-Doi_mau-ten/name_color_champion_gold_01.png", "card", 0.84),
    "discount_coupon_05": ("PhieuGiamGia/5%.png", "card", 0.84),
    "discount_coupon_10": ("PhieuGiamGia/10%.png", "card", 0.84),
    "discount_coupon_20": ("PhieuGiamGia/20%.png", "card", 0.84),
    "discount_coupon_30": ("PhieuGiamGia/30%.png", "card", 0.84),
    "display_name_change_ticket": ("The-doi-ten/display_name_change_ticket_01.png.png", "card", 0.84),
}


def fit_transparent(source: Image.Image, output_size: int, content_ratio: float) -> Image.Image:
    rgba = source.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if not bbox:
        return Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    content = rgba.crop(bbox)
    max_content = max(1, round(output_size * content_ratio))
    content.thumbnail((max_content, max_content), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    canvas.alpha_composite(
        content,
        ((output_size - content.width) // 2, (output_size - content.height) // 2),
    )
    return canvas


def save_webp(image: Image.Image, path: Path, quality: int = 88) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "WEBP", quality=quality, method=4, lossless=False)


def process(source_root: Path, output_root: Path) -> None:
    missing = [relative for relative, _, _ in ASSETS.values() if not (source_root / relative).is_file()]
    if missing:
        raise FileNotFoundError("Thiếu ảnh nguồn: " + ", ".join(missing))

    for code, (relative, kind, ratio) in ASSETS.items():
        with Image.open(source_root / relative) as opened:
            image = ImageOps.exif_transpose(opened)
            if kind == "banner":
                rendered = ImageOps.fit(
                    image.convert("RGB"),
                    (1600, 400),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
                save_webp(rendered, output_root / f"{code}.webp", quality=86)
            else:
                rendered = fit_transparent(image, 512, ratio)
                save_webp(rendered, output_root / f"{code}.webp", quality=90)
                if kind == "badge":
                    save_webp(
                        rendered.resize((96, 96), Image.Resampling.LANCZOS),
                        output_root / f"{code}_96.webp",
                        quality=92,
                    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Thư mục Cuahang đã giải nén")
    parser.add_argument("output", type=Path, nargs="?", default=Path("static/shop/items"))
    args = parser.parse_args()
    process(args.source.resolve(), args.output.resolve())
    print(f"Đã tạo {len(ASSETS)} ảnh vật phẩm tại {args.output}")


if __name__ == "__main__":
    main()
