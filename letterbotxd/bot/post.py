from PIL import (Image, ImageDraw, ImageFont, ImageFilter)
import textwrap
import random
from pilmoji import Pilmoji

from bot.models import Movie, Review
from bot.config import Settings
from bot.gemini import GeminiWrapper
from bot.fb import FaceAPI
from bot.render.rounder import circle_image, round_image
from bot.render.text_fit import best_fit
from bot.render.markup import draw_markup_text
from bot.letterboxd import get_random_movie
from bot.utils import download_letterboxd_poster, download_image

color_title = (255, 255, 255)
color_primary = (153, 170, 187)
color_secondary = (255, 255, 255, 160)

font_title_path = "assets/fonts/Manrope-Medium.ttf"
font_body_path = "assets/fonts/Faustina-Regular.ttf"
font_body_bold_path = "assets/fonts/Faustina-Bold.ttf"

icon_star_full_path = "assets/images/star.png"
icon_star_half_path = "assets/images/star_half.png"

design = {
    "titleX": 512,
    "titleY": 32,
    "directorX": 512,
    "directorY": 88,
    "profilePicX": 512,
    "profilePicY": 176,
    "reviewX": 512,
    "reviewY": 242,
    "reviewWidth": 448,
    "reviewHeight": 336,
    "dateX": 854,
    "dateY": 654,
    "starsX": 512,
    "starsY": 656,
}

def draw_grid(img: Image.Image, grid_size: int = 16):
    draw = ImageDraw.Draw(img)
    width, height = img.size

    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill=(255, 0, 0, 64), width=1)

    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill=(255, 0, 0, 64), width=1)

def render(movie: Movie):
    w, h = 1024, 720
    padding = 32
    img = Image.new('RGBA', (w, h), (20, 24, 28))
    img_overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    img_poster = Image.open("temp/poster.png").convert("RGBA")

    img_poster_blurred = img_poster.resize((w - padding, h - padding), Image.LANCZOS)
    img_poster_blurred = img_poster_blurred.filter(ImageFilter.GaussianBlur(radius=200))
    img_poster_blurred.putalpha(64)
    img_poster_blurred = round_image(img_poster_blurred, radius=16)
    img.alpha_composite(img_poster_blurred, (int(padding / 2), int(padding / 2)))

    img_poster.thumbnail((w - padding, h - padding), Image.LANCZOS)
    if img_poster.size[0] > 459:
        img_poster = img_poster.crop((0, 0, 459, img_poster.size[1]))
    img_poster = round_image(img_poster, radius=(16, 0, 0, 16))
    img.paste(img_poster, (int(padding / 2), int(padding / 2)), img_poster)

    draw = ImageDraw.Draw(img_overlay)

    font_title = ImageFont.truetype(font_title_path, 32)
    font_body = ImageFont.truetype(font_body_path, 24)
    font_body_bold = ImageFont.truetype(font_body_bold_path, 24)
    font_review = ImageFont.truetype(font_body_path, 20)

    title = f"{movie.title} ({movie.year})"
    title = textwrap.fill(title, width=30)
    vertical_padding = 64 if "\n" in title else 0

    draw.text((design["titleX"], design["titleY"]), title, font=font_title, fill=(color_title))

    design["directorY"] = design["directorY"] + vertical_padding
    directed = "Directed by"
    draw.text((design["directorX"], design["directorY"]), directed, font=font_body, fill=(color_primary))
    draw.text((design["directorX"], design["directorY"] + 32), movie.director, font=font_body_bold, fill=(color_title))

    if movie.duration:
        duration = f"{movie.duration:>6} min"
        draw.text((design["directorX"] + 365, design["directorY"]), duration, font=font_body, fill=(color_primary))

    design["profilePicY"] = design["profilePicY"] + vertical_padding
    img_profile_pic = Image.open("temp/profile_pic.png").convert("RGBA")
    img_profile_pic = circle_image(img_profile_pic, size=48)
    img.paste(img_profile_pic, (design["profilePicX"], design["profilePicY"]), img_profile_pic)

    watched_by = "Watched by"
    draw.text((design["profilePicX"] + 64, design["profilePicY"] + 6), watched_by, font=font_body, fill=(color_primary))
    draw.text((design["profilePicX"] + 186, design["profilePicY"] + 6), movie.picked_review.reviewer, font=font_body_bold, fill=(color_title))

    # Draw a rectagle over the review area for debugging
    #draw.rectangle((design["reviewX"], design["reviewY"], design["reviewX"] + design["reviewWidth"], design["reviewY"] + design["reviewHeight"]), outline=(255, 0, 0, 64), width=1)

    review_text = f'"{movie.picked_review.text}"'
    font_review, lines = best_fit(review_text, (design["reviewWidth"], design["reviewHeight"]), font_body_path)
    font_review_bold = ImageFont.truetype(font_body_bold_path, font_review.size)

    line_height = font_review.getbbox("Ay")[3] - font_review.getbbox("Ay")[1]
    design["reviewY"] = design["reviewY"] + vertical_padding
    for line in lines:
        #with Pilmoji(img_overlay) as pilmoji:
        #    pilmoji.text((design["reviewX"], design["reviewY"]), line, color_secondary, font_review)
        draw_markup_text(draw, (design["reviewX"], design["reviewY"]), line, font_review,font_review_bold, color_secondary)
        design["reviewY"] += int(line_height * 1.1)

    date_str = f"{movie.picked_review.date.day} {movie.picked_review.date.strftime('%b')} {movie.picked_review.date.year}"
    draw.text((design["dateX"], design["dateY"]), date_str, font=font_body, fill=color_primary)

    # Draw stars
    star_full = Image.open(icon_star_full_path).convert("RGBA").resize((32, 32), Image.LANCZOS)
    star_half = Image.open(icon_star_half_path).convert("RGBA").resize((32, 32), Image.LANCZOS)
    star_size = 32
    for i in range(5):
        if i < int(movie.picked_review.rating):
            img.paste(star_full, (design["starsX"] + i * star_size, design["starsY"]), star_full)
        elif i < movie.picked_review.rating:
            img.paste(star_half, (design["starsX"] + i * star_size, design["starsY"]), star_half)

    # Draw grid for debugging
    #draw_grid(img)

    alpha = img_overlay.getchannel('A')
    shadow_opacity = 120 
    alpha_shadow = alpha.point(lambda p: shadow_opacity if p > 200 else 0)

    img_shadow = Image.new('RGBA', img_overlay.size, (0, 0, 0, 0))  # fondo transparente
    img_shadow.putalpha(alpha_shadow)

    img_shadow = img_shadow.filter(ImageFilter.GaussianBlur(radius=1))

    img.paste(img_shadow, (1, 1), img_shadow)     # 1 px de desplazamiento, por ejemplo
    img.paste(img_overlay, (0, 0), img_overlay)
    img.save("temp/post.png")

def post():
    """
    Post to Letterbotxd Facebook page.
    """

    settings = Settings()
    gemini = GeminiWrapper(settings.gemini_api_key)
    fb_api = FaceAPI(settings.page_access_token)

    # Load movie data from json
    with open("temp/movie.json", "r") as f:
        movie_data = f.read()
        movie = Movie.parse_raw(movie_data)

    
    movie = get_random_movie()
    movie.picked_review = movie.reviews[1] 
    try:
        movie.picked_review = gemini.pick_best_review(movie)
    except Exception as e:
        print(f"Error picking best review: {e}")
        movie.picked_review = random.choice(movie.reviews)
    download_letterboxd_poster(movie.image_url, "temp/poster.png")
    download_image(movie.picked_review.reviewer_pic, "temp/profile_pic.png")

    render(movie)

    post_msg = f"{movie.title} ({movie.year}) \n" \
               f"Directed by {movie.director}\n\n" \
               f"Watched by {movie.picked_review.reviewer} on {movie.picked_review.date.strftime('%d %b %Y')}\n" \
               f"Rating: {movie.picked_review.rating} stars"
    print(f"Posting review for {movie.title} by {movie.picked_review.reviewer} to Facebook")

    # Post to Facebook
    post_id = fb_api.post(post_msg, "temp/post.png")

    # Comment on the post with the movie link
    fb_api.comment_post(post_id, f"Check out the movie here\n{movie.url}")

    # Save movie data to JSON
    with open("temp/movie.json", "w") as f:
        f.write(movie.model_dump_json(indent=4))