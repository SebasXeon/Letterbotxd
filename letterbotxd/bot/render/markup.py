from PIL import ImageDraw, ImageFont
import re
from typing import Tuple, Optional

def draw_markup_text(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    bold_font: ImageFont.FreeTypeFont,
    fill: str = "black",
    max_width: Optional[int] = None,
    line_spacing: float = 1.2,
) -> Tuple[int, int]:
    def parse_markup(block: str):
        idx = 0
        for m in re.finditer(r"\[b\](.*?)\[/b\]", block, flags=re.DOTALL):
            if m.start() > idx:
                yield block[idx:m.start()], False
            yield m.group(1), True
            idx = m.end()
        if idx < len(block):
            yield block[idx:], False

    def text_len(segment: str, is_bold: bool) -> int:
        f = bold_font if is_bold else font
        return draw.textlength(segment, font=f)

    x0, y0 = xy
    y = y0
    for paragraph in text.split("\n"):
        tokens = list(parse_markup(paragraph))

        lines = []
        if max_width:
            buf, buf_px = [], 0
            for seg, is_b in tokens:
                seg_px = text_len(seg, is_b)
                if buf_px + seg_px > max_width and buf:
                    lines.append(buf)
                    buf, buf_px = [], 0
                buf.append((seg, is_b))
                buf_px += seg_px
            if buf:
                lines.append(buf)
        else:
            lines = [tokens]

        for line in lines:
            x = x0
            for seg, is_b in line:
                fnt = bold_font if is_b else font
                draw.text((x, y), seg, font=fnt, fill=fill)
                x += text_len(seg, is_b)
            ascent, descent = font.getmetrics()
            line_h = (ascent + descent)
            y += int(line_h * line_spacing)

    return (x0, y)
