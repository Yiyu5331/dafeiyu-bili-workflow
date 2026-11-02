"""封面：把成片里的一帧做成 1080x1920 竖屏封面。"""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/msyh.ttc",
]


def _font(size: int):
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    raise SystemExit("找不到中文字体，请把任一中文字体路径加进 dyfish/cover.py 的 FONTS")


def _wrap(draw, text: str, font, maxw: int) -> list[str]:
    punct = "，。！？、；：）"
    out, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) <= maxw or ch in punct:
            cur += ch
        else:
            out.append(cur)
            cur = ch
    if cur:
        out.append(cur)
    while len(out) > 1 and len(out[-1]) <= 2:
        out[-2] += out[-1][0]
        out[-1] = out[-1][1:]
        if not out[-1]:
            out.pop()
    return out


def grab_frame(mp4: Path, out_jpg: Path, ratio: float = 0.55) -> Path:
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                               capture_output=True, text=True).stdout.strip() or 8)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dur*ratio:.2f}", "-i", str(mp4), "-frames:v", "1",
                    str(out_jpg)], check=True)
    return out_jpg


def make_cover(frame: Path, title: str, subtitle: str, out: Path) -> Path:
    im = Image.open(frame).convert("RGB").resize((1080, 1920))
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(0, 760):
        d.line([(0, y), (1080, y)], fill=(5, 7, 13, int(235 * (1 - y / 760) ** 0.7)))

    size = 92
    while size > 58:
        f_try = _font(size)
        if len(_wrap(d, title, f_try, 900)) <= 3:
            break
        size -= 6
    f_title, f_kick, f_sub, f_sign = _font(size), _font(44), _font(46), _font(34)

    y = 120
    if subtitle:
        d.text((72, y), f"— {subtitle}", font=f_kick, fill=(94, 225, 255, 255))
        y += 80
    for i, ln in enumerate(_wrap(d, title, f_title, 900)[:4]):
        d.text((72, y), ln, font=f_title, fill=(255, 214, 102, 255) if i == 0 else (255, 255, 255, 255),
               stroke_width=3, stroke_fill=(0, 0, 0, 160))
        y += int(size * 1.26)
    d.text((72, y + 16), "大肥鱼 · 16 秒讲明白", font=f_sub, fill=(178, 186, 204, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=92)
    return out
