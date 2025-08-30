from typing import Sequence, Union, Tuple
from PIL import Image, ImageDraw, ImageFilter


def round_image(
    img: Image.Image,
    radius: Union[int, Sequence[int]],
    oversample: int = 4,
    blur: float = 0.5,
) -> Image.Image:
    if isinstance(radius, int):
        r_tl = r_tr = r_br = r_bl = radius
    elif len(radius) == 4:
        r_tl, r_tr, r_br, r_bl = radius
    else:
        raise ValueError(
            "radius debe ser un int o una secuencia de 4 enteros"
        )

    w, h = img.size
    max_r = min(w, h) // 2 
    r_tl, r_tr, r_br, r_bl = [
        max(0, min(int(r), max_r)) for r in (r_tl, r_tr, r_br, r_bl)
    ]

    n = max(1, int(oversample))
    w2, h2 = w * n, h * n
    r_tl2, r_tr2, r_br2, r_bl2 = [r * n for r in (r_tl, r_tr, r_br, r_bl)]

    mask = Image.new("L", (w2, h2), 0)
    draw = ImageDraw.Draw(mask)

    draw.rectangle((r_tl2, 0, w2 - r_tr2, h2), fill=255)
    draw.rectangle((0, r_tl2, w2, h2 - r_bl2), fill=255)

    if r_tl2 > 0:
        draw.pieslice((0, 0, 2 * r_tl2, 2 * r_tl2), 180, 270, fill=255)
    if r_tr2 > 0:
        draw.pieslice(
            (w2 - 2 * r_tr2, 0, w2, 2 * r_tr2), 270, 360, fill=255
        )
    if r_br2 > 0:
        draw.pieslice(
            (w2 - 2 * r_br2, h2 - 2 * r_br2, w2, h2), 0, 90, fill=255
        )
    if r_bl2 > 0:
        draw.pieslice((0, h2 - 2 * r_bl2, 2 * r_bl2, h2), 90, 180, fill=255)

    mask = mask.resize((w, h), Image.LANCZOS)
    if blur > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))

    img_rgba = img.convert("RGBA")
    out = Image.new("RGBA", (w, h))
    out.paste(img_rgba, (0, 0), mask=mask)
    return out

def circle_image(img: Image.Image, size: int | None = None) -> Image.Image:
    
    img = img.copy()
    
    if size is None:
        size = min(img.size)
    
    img.thumbnail((size, size))
    
    width, height = img.size
    if width != height:
        min_side = min(width, height)
        left = (width - min_side) / 2
        top = (height - min_side) / 2
        right = (width + min_side) / 2
        bottom = (height + min_side) / 2
        img = img.crop((left, top, right, bottom))
    
    if img.size != (size, size):
        img = img.resize((size, size), Image.LANCZOS)
    
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size-1, size-1), fill=255)
    
    result = Image.new('RGBA', (size, size))
    result.paste(img, (0, 0), mask)
    
    return result