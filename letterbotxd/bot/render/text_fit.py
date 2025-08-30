from PIL import Image, ImageDraw, ImageFont
import textwrap

def wrap_text_pixels(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.ImageDraw
) -> list[str]:
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip() == "":
            lines.append("")
            continue

        buf = []
        for word in paragraph.split():
            buf.append(word)
            test_line = " ".join(buf)
            if draw.textlength(test_line, font=font) > max_width and len(buf) > 1:
                buf.pop()
                lines.append(" ".join(buf))
                buf = [word]
        if buf:
            lines.append(" ".join(buf))
    return lines

def best_fit(text, box, font_path, min_size=10, max_size=250, line_spacing=0.1):
    w_box, h_box = box
    lo, hi, best = min_size, max_size, None

    dummy_img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_img)

    while lo <= hi:
        mid = (lo + hi) // 2
        font = ImageFont.truetype(font_path, mid)
        lines = wrap_text_pixels(text, font, w_box, draw)

        bbox = draw.textbbox((0, 0), "Ay", font=font)
        line_height = bbox[3] - bbox[1]
        total_h = int(line_height * (1 + line_spacing) * len(lines))

        if total_h <= h_box and all(draw.textlength(line, font=font) <= w_box for line in lines):
            best = (font, lines)
            lo = mid + 1
        else:
            hi = mid - 1

    if best is None:
        best_font = ImageFont.truetype(font_path, min_size)
        best_lines = wrap_text_pixels(text, best_font, w_box, draw)
        return best_font, best_lines
    return best

# Test
if __name__ == "__main__":
    TEXT = ("Esto funciona igual.")
    W, H = 600, 400
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    font, lines = best_fit(TEXT, (W, H), FONT_PATH)

    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    y = 0
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    for line in lines:
        draw.text((0, y), line, fill="black", font=font)
        y += int(line_height * 1.1)      # 10 % de leading opcional

    img.save("resultado.png")
    print("Generado resultado.png con font size =", font.size)
