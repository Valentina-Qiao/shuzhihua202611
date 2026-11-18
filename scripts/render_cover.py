"""Render a 1080 × 1920 cover with the fixed speaker artwork and a new photo."""

import argparse
import json
import os
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ASSETS = Path(__file__).resolve().parent.parent / "assets"
WIDTH, HEIGHT = 1080, 1920
RESAMPLE = Image.Resampling.LANCZOS
FONT_PATH = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "NotoSansSC-VF.ttf"
LATIN_FONT = FONT_PATH.with_name("arialbi.ttf")
BRUSH_FONT = Path.home() / "AppData/Local/Microsoft/Windows/Fonts/字魂110号-武林江湖体.ttf"


def y_px(reference_y):
    return round(reference_y * HEIGHT / 1672)


def gradient(size, start, end):
    ratios = np.linspace(0, 1, size[1])[:, None]
    rows = np.round(np.asarray(start) * (1 - ratios) + np.asarray(end) * ratios)
    return Image.fromarray(rows.astype(np.uint8)[:, None, :]).resize(size)


def smoothstep(value):
    fraction = np.clip(value, 0, 1)
    return fraction * fraction * (3 - 2 * fraction)


def photo_mask(top, bottom):
    x = np.linspace(0, 1, WIDTH)
    y = np.arange(top, bottom)[:, None] * 1672 / HEIGHT
    # Position the photo between the two fixed neon sweeps in the lower half.
    anchors = [0, .1, .23, .4, .55, .68, .8, .9, 1]
    opening = np.interp(x, anchors, [982, 926, 893, 902, 912, 911, 897, 877, 845])
    closing = np.interp(x, anchors, [1502, 1541, 1569, 1569, 1533, 1494, 1465, 1440, 1425])
    photo_start = top * 1672 / HEIGHT
    opacity = smoothstep((y - opening) / 55) * smoothstep((closing - y) / 132)
    opacity *= smoothstep((y - photo_start) / 46)
    return Image.fromarray(np.round(255 * opacity).astype(np.uint8))


def place_photo(canvas, photo, fit, focus, earliest_top=0):
    top, bottom = max(y_px(875), earliest_top), y_px(1578)
    size = (WIDTH, bottom - top)
    background = canvas.crop((0, top, WIDTH, bottom))
    fitted = ImageOps.fit(photo, size, RESAMPLE, centering=focus)
    if fit == "cover":
        fitted = Image.blend(fitted, background, .08)
    else:
        blurred = fitted.filter(ImageFilter.GaussianBlur(43))
        fitted = Image.blend(background, blurred, .17)
        inset = ImageOps.contain(photo, (round(WIDTH * .91), y_px(374)), RESAMPLE)
        inset_x = (WIDTH - inset.width) // 2
        inset_y = y_px(1162) - top - inset.height // 2
        feather = Image.new("L", inset.size)
        feather_draw = ImageDraw.Draw(feather)
        edge = max(1, min(12, inset.width // 8, inset.height // 8))
        feather_draw.rectangle(
            (edge, edge, inset.width - edge - 1, inset.height - edge - 1),
            fill=255,
        )
        fitted.paste(inset, (inset_x, inset_y), feather.filter(ImageFilter.GaussianBlur(edge / 2)))
    mask = photo_mask(top, bottom)
    canvas.paste(fitted, (0, top), mask)
    _, visible_top, _, visible_bottom = mask.point(lambda value: 255 if value >= 20 else 0).getbbox()
    return top + visible_top, top + visible_bottom


def place_cutout(canvas, photo, title_bottom):
    alpha = photo.getchannel("A")
    if alpha.getextrema()[0] == 255:
        raise ValueError("cutout 模式需要有实际透明背景的 PNG。")
    photo.putalpha(alpha.point(lambda value: round(255 * max(0, value - 18) / 237)))
    bounds = photo.getbbox()
    if bounds is None:
        raise ValueError("抠图没有可见主体，请检查透明蒙版。")
    photo = photo.crop(bounds)
    top, bottom = max(1126, title_bottom + y_px(32)), 1634
    scale = WIDTH / photo.width
    if round(photo.height * scale) > bottom - top:
        scale = (bottom - top) / photo.height
    photo = photo.resize(tuple(max(1, round(dimension * scale)) for dimension in photo.size), RESAMPLE)
    x = (WIDTH - photo.width) // 2
    y = top + (bottom - top - photo.height) // 2
    tail = min(48, photo.height // 8)
    if tail > 1 and y + photo.height > bottom - 24:
        fade = np.ones(photo.height)
        fade[-tail:] = np.linspace(1, 0, tail) ** .7
        alpha = np.asarray(photo.getchannel("A"), dtype=float) * fade[:, None]
        photo.putalpha(Image.fromarray(alpha.astype(np.uint8)))
    canvas.paste(photo, (x, y), photo.getchannel("A"))
    return y, y + photo.height


def glyph_mask(line, font_path, font_size):
    font = ImageFont.truetype(str(font_path), font_size)
    font.set_variation_by_axes([900])
    stroke = max(1, round(font_size * .013))
    left, top, right, bottom = font.getbbox(line, stroke_width=stroke)
    mask = Image.new("L", (right - left, bottom - top))
    ImageDraw.Draw(mask).text(
        (-left, -top), line, font=font, fill=255, stroke_width=stroke
    )
    return mask.crop(mask.getbbox())


def tracked_line_mask(line, font, tracking):
    # Space the visible glyph edges evenly, retaining the font's shared baseline.
    glyphs = []
    x = 0
    for character in line:
        if character.isspace():
            x += round(font.getlength(character))
            continue
        left, top, right, bottom = font.getbbox(character)
        glyph = Image.new("L", (right - left, bottom - top))
        ImageDraw.Draw(glyph).text((-left, -top), character, font=font, fill=255)
        bounds = glyph.getbbox()
        if bounds is None:
            continue
        glyph = glyph.crop(bounds)
        glyphs.append((glyph, x, top + bounds[1]))
        x += glyph.width + tracking
    if not glyphs:
        raise ValueError("标题行需要有可见文字。")
    top = min(y for _, _, y in glyphs)
    bottom = max(y + glyph.height for glyph, _, y in glyphs)
    mask = Image.new("L", (x - tracking, bottom - top))
    for glyph, x, y in glyphs:
        mask.paste(glyph, (x, y - top))
    return mask


def three_line_masks(lines, font_path, max_width, available_height):
    size = 127
    while size >= 30:
        font = ImageFont.truetype(str(font_path), size)
        font.set_variation_by_axes([760])
        masks = [tracked_line_mask(line, font, tracking=7) for line in lines]
        longest = max(mask.width for mask in masks)
        height = sum(mask.height for mask in masks)
        if longest <= max_width and height <= available_height:
            return masks
        size = min(size - 1, round(size * min(max_width / longest, available_height / height)))
    raise ValueError("标题排版过小。请调整三行之间的断句。")


def word_mask(word, font_path, ink_height):
    font = ImageFont.truetype(str(font_path), 172)
    missing = bytes(font.getmask("\u0378"))
    for character in word:
        if not character.isspace() and bytes(font.getmask(character)) == missing:
            raise ValueError(f"{font_path.name} 缺少字形「{character}」。")
    left, top, right, bottom = font.getbbox(word)
    mask = Image.new("L", (right - left, bottom - top))
    ImageDraw.Draw(mask).text((-left, -top), word, fill=255, font=font)
    mask = mask.crop(mask.getbbox())
    return mask.resize((round(mask.width * ink_height / mask.height), ink_height), RESAMPLE)


def gold_headline_mask(line, brush_font, scale):
    runs = re.findall(r"\s+|[!-~]+|[^\s!-~]+", line)
    baseline = round(148 * scale)
    gap = round(21 * scale)
    positions = []
    x = 0
    for run in runs:
        if run.isspace():
            x += round(22 * scale) * len(run)
            continue
        ascii_run = run.isascii()
        mask = word_mask(run, LATIN_FONT if ascii_run else brush_font,
                         round((125 if ascii_run else 148) * scale))
        positions.append((mask, x, round(17 * scale) if ascii_run else 0))
        x += mask.width + gap
    headline = Image.new("L", (x - gap, baseline))
    for mask, x, y in positions:
        headline.paste(mask, (x, y))
    return headline.crop(headline.getbbox())


def place_gold_title(canvas, lines, font_path, brush_font):
    max_width, max_height = round(WIDTH * .86), 384
    scale = 1.0
    while scale >= .45:
        subtitle_font = ImageFont.truetype(str(font_path), round(101 * scale))
        subtitle_font.set_variation_by_axes([790])
        masks = [gold_headline_mask(lines[0], brush_font, scale)]
        masks.extend(tracked_line_mask(line, subtitle_font, tracking=round(7 * scale))
                     for line in lines[1:])
        gap = round(19 * scale)
        width = max(mask.width for mask in masks)
        height = sum(mask.height for mask in masks) + gap * (len(masks) - 1)
        if width <= max_width and height <= max_height:
            break
        scale *= min(.98, max_width / width, max_height / height)
    else:
        raise ValueError("标题过长，无法在保留主副标题层级的情况下排下。请按语义重新分行。")

    title_top = 894 - height // 2
    y = title_top
    for index, mask in enumerate(masks):
        colors = ((255, 242, 182), (246, 178, 63)) if index == 0 else (
            (255, 234, 164), (245, 186, 75)
        )
        x = (WIDTH - mask.width) // 2
        canvas.paste((34, 25, 66), (x, y + 3, x + mask.width, y + 3 + mask.height), mask)
        canvas.paste(gradient(mask.size, *colors), (x, y), mask)
        y += mask.height + gap
    return title_top, title_top + height


def place_title(canvas, lines, font_path):
    three_lines = len(lines) == 3
    max_width = round(WIDTH * .86)
    line_gap = y_px(18 if three_lines else 17)
    max_height = y_px(326 if three_lines else 202)
    available_height = max_height - line_gap * (len(lines) - 1)
    if three_lines:
        masks = three_line_masks(lines, font_path, max_width, available_height)
    else:
        masks = [glyph_mask(line, font_path, size) for line, size in zip(lines, (154, 116))]
        scale = min(1, max_width / max(mask.width for mask in masks),
                    available_height / sum(mask.height for mask in masks))
        masks = [
            mask.resize((max(1, round(mask.width * scale)), max(1, round(mask.height * scale))), RESAMPLE)
            for mask in masks
        ]
    if min(mask.height for mask in masks) < 26:
        raise ValueError("标题排版过小。请在词组边界换行，最多三行。")
    height = sum(mask.height for mask in masks) + line_gap * (len(masks) - 1)
    title_top = y_px(780 if three_lines else 756) - height // 2
    y = title_top
    for index, mask in enumerate(masks):
        colors = ((119, 229, 251), (186, 248, 255)) if three_lines or index == 0 else (
            (159, 234, 255), (224, 251, 255)
        )
        x = (WIDTH - mask.width) // 2
        shadow_offset = 2 if three_lines else 3
        shadow_y = y + shadow_offset
        canvas.paste((16, 29, 78), (x, shadow_y, x + mask.width, shadow_y + mask.height), mask)
        canvas.paste(gradient(mask.size, *colors), (x, y), mask)
        y += mask.height + line_gap
    return title_top, title_top + height


def center_content(canvas, bounds):
    top = min(start for start, _ in bounds)
    bottom = max(end for _, end in bounds)
    height = min(bottom - top, round(HEIGHT * .86))
    width = round(WIDTH * height / (bottom - top))
    margin = (HEIGHT - height) // 2
    strips = (
        (0, top, margin),
        (top, bottom, height),
        (bottom, HEIGHT, HEIGHT - margin - height),
    )
    centered = Image.new("RGB", (width, HEIGHT))
    y = 0
    for start, end, target_height in strips:
        strip = canvas.crop((0, start, WIDTH, end))
        centered.paste(strip.resize((width, target_height), RESAMPLE), (0, y))
        y += target_height
    side = (WIDTH - width) // 2
    padded = np.pad(np.asarray(centered), ((0, 0), (side, WIDTH - width - side), (0, 0)), mode="reflect")
    return Image.fromarray(padded), margin, HEIGHT - margin - height


def number_list(value, count):
    return (
        isinstance(value, (tuple, list))
        and len(value) == count
        and all(type(item) in (int, float) and 0 <= item <= 1 for item in value)
    )


def render(request, font_path, brush_font=BRUSH_FONT):
    title = request.get("title")
    if not isinstance(title, str):
        raise ValueError("请提供标题原文。")
    lines = [line.strip() for line in title.splitlines() if line.strip()]
    if not 1 <= len(lines) <= 3 or len(title) > 160:
        raise ValueError("标题需要一至三行，最多 160 字符。")
    photo_path = request.get("photo")
    if not isinstance(photo_path, str) or not Path(photo_path).is_absolute():
        raise ValueError("请提供下方配图的绝对路径。")
    fit = request.get("fit")
    style = request.get("style", "gold")
    focus = request.get("focus", (.5, .5))
    if fit not in (None, "cutout", "cover", "contain") or not number_list(focus, 2):
        raise ValueError("fit 必须为 cutout、cover 或 contain，focus 是两个 0 至 1 的数。")
    if style not in ("gold", "ice"):
        raise ValueError("style 必须为 gold 或 ice。")
    with Image.open(photo_path) as source:
        photo = ImageOps.exif_transpose(source).convert("RGBA")
    if fit is None:
        fit = "cutout" if photo.getchannel("A").getextrema()[0] < 255 else "cover"
    crop = request.get("crop")
    if crop is not None:
        if not number_list(crop, 4) or not (crop[0] < crop[2] and crop[1] < crop[3]):
            raise ValueError("crop 应为 [左, 上, 右, 下]，且范围非空。")
        box = tuple(round(value * axis) for value, axis in zip(crop, photo.size * 2))
        if box[0] >= box[2] or box[1] >= box[3]:
            raise ValueError("crop 小于 1 像素。")
        photo = photo.crop(box)
    with Image.open(ASSETS / "base.png") as base:
        canvas = base.convert("RGB")
    if style == "gold":
        if not brush_font.is_file() and not lines[0].isascii():
            raise ValueError("找不到字魂武林江湖体，请用 --brush-font 指定同款字体文件。")
        title_bounds = place_gold_title(canvas, lines, font_path, brush_font)
    else:
        title_bounds = place_title(canvas, lines, font_path)
    if fit == "cutout":
        photo_bounds = place_cutout(canvas, photo, title_bounds[1])
    else:
        photo = Image.alpha_composite(Image.new("RGBA", photo.size, "#065bca"), photo).convert("RGB")
        earliest_top = title_bounds[1] + y_px(10) if fit == "cover" else 0
        photo_bounds = place_photo(canvas, photo, fit, focus, earliest_top)
    # Bounds of the fixed speaker pair and the neon curves bordering the content.
    fixed_bounds = y_px(176), y_px(1585)
    return center_content(canvas, (fixed_bounds, photo_bounds, title_bounds))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--font", type=Path, default=FONT_PATH)
    parser.add_argument("--brush-font", type=Path, default=BRUSH_FONT)
    args = parser.parse_args()
    try:
        if not args.font.is_file():
            raise ValueError("找不到 NotoSansSC-VF.ttf，请用 --font 指定同款字体文件。")
        request = json.loads(args.request.read_text(encoding="utf-8-sig"))
        if not isinstance(request, dict):
            raise ValueError("请求 JSON 必须是对象。")
        image, top, bottom = render(request, args.font, args.brush_font)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as out:
            image.save(out, "PNG")
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"{WIDTH} × {HEIGHT} | 上方 {top}px | 下方 {bottom}px")


if __name__ == "__main__":
    main()
