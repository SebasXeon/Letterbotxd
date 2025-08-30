import random
import re
import html
from datetime import datetime
from urllib.parse import urljoin

import requests
from parsel import Selector

from bot.models import Movie, Review

# Setup 
BASE = "https://letterboxd.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; Letterbotxd/0.1; +https://github.com/SebasXeon/Letterbotxd)"
    ),
    "X-Requested-With": "XMLHttpRequest",
}

# Mapas de órdenes posibles → endpoint AJAX
LISTINGS = [
    "popular/",
    "popular/this/week/",
    "popular/this/month/",
    "popular/this/year/",
    "by/rating/",
    "by/rating-lowest/",
]


# Utils
def _get_selector(url: str) -> Selector:
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return Selector(text=r.text)


def _clean(txt_list: list[str]) -> str:
    return " ".join(t.strip() for t in txt_list if t and t.strip())


# Pick a random film URL from the listing URLs
def _random_film_choice() -> str:
    path = random.choice(LISTINGS)
    ajax_url = f"{BASE}/films/ajax/{path}?esiAllowFilters=true"

    sel = _get_selector(ajax_url)
    items = sel.xpath("//li[contains(@class,'poster-container')]")
    if not items:
        raise RuntimeError("Letterboxd AJAX devolvió 0 películas")

    li = random.choice(items)

    slug = li.xpath(".//div/@data-film-slug").get().strip("/")
    film_url = urljoin(BASE, f"/film/{slug}/")

    return film_url


# Scrape movie details from the film URL
def _scrape_movie(film_url: str) -> dict:
    sel = _get_selector(film_url)

    def xp(path: str) -> str | None:
        txt = sel.xpath(path + "/text()").get()
        return txt.strip() if txt else None
    
    slug = sel.xpath(".//div/@data-film-slug").get().strip("/")


    title = xp('//h1/span')
    year_txt = sel.xpath('//section[1]//span/a/text()').re_first(r"\d{4}")
    director = xp('//section[1]/div/div/p/span[2]/a/span')
    description = xp('//section[2]/section/div[1]/div/p')
    duration = sel.xpath('//div[2]/div/div/div[2]/section[2]/p/text()').re_first(r"\d+")
    # /html/body/div[2]/div/div/div[1]/section[1]/a/div[1]/div/img
    poster_url = (f"{BASE}/ajax/poster/film/{slug}/std/1000x1500/")

    return dict(
        url=film_url,
        title=title,
        year=int(year_txt) if year_txt else None,
        director=director,
        description=description,
        duration=int(duration) if duration else None,
        image_url=poster_url,
    )


# Scrape reviews from the film URL
def _scrape_reviews(film_url: str, max_reviews=10) -> list[Review]:
    slug = film_url.rstrip("/").split("/")[-1]
    reviews_url = f"https://letterboxd.com/film/{slug}/reviews/by/activity/"
    sel = _get_selector(reviews_url)

    articles = sel.xpath('//article[contains(@class,"production-viewing")]').getall()[:max_reviews] #/html/body/div[1]/div/div/section/div[3]
    rvws: list[Review] = []

    for art in articles:
        art = Selector(text=art)
        
        reviewer = art.xpath(
            '//a[contains(@class,"avatar")]/@href'
        ).re_first(r"/([^/]+)/") or "anon" #/html/body/div[1]/div/div/section/div[3]/div[1]/article/a
        reviewer_pic = art.xpath(
            '//a[contains(@class,"avatar")]/img/@src'
        ).get()
        rating_text = art.xpath('//span[contains(@class,"rating")]/text()').get()
        if rating_text:
            rating = rating_text.count('★') + 0.5 * rating_text.count('½')
        else:
            rating = 0
        date_iso = art.xpath('//time/@datetime').get()
        date = datetime.fromisoformat(date_iso) if date_iso else None
        likes_txt = art.xpath(
            '//span[contains(@class,"like-link")]'
        ).get() #/html/body/div[1]/div/div/section/div[3]/div[1]/article/div/div[2]/div[2]/div/p/span/a/span
        likes = int(likes_txt.replace(",", "")) if likes_txt else None
        review_div = art.xpath('//div[contains(@class,"js-review-body")]')
        review_lines = []

        B_TAG_OPEN  = re.compile(r"(?i)<\s*(b|strong)(\s+[^>]*)?>")   # <b ...>  or <strong ...>
        B_TAG_CLOSE = re.compile(r"(?i)</\s*(b|strong)\s*>")          # </b>     or </strong>

        for p in review_div.css("p"):
            # 1) Reemplazar <br> por salto de línea real
            cleaned_html = re.sub(r"(?i)<br\s*/?>", "\n", p.get())

            # 2) Cambiar etiquetas de negrita por tokens [b] y [/b]
            cleaned_html = B_TAG_OPEN.sub("[b]",  cleaned_html)
            cleaned_html = B_TAG_CLOSE.sub("[/b]", cleaned_html)

            # 3) Convertir a texto con las marcas preservadas
            p_text = Selector(text=cleaned_html).xpath("string()").get()

            # 4) Procesar cada línea resultante
            for raw in p_text.splitlines():
                clean = (html.unescape(raw)        # &nbsp; → ' '
                        .replace("\xa0", " ")     # NBSP unicode → espacio normal
                        .strip())
                if clean:
                    review_lines.append(clean)

        rvws.append(
            Review(
                reviewer=reviewer,
                reviewer_pic=reviewer_pic,
                rating=rating,
                date=date,
                likes=likes,
                text= "\n".join(review_lines) if review_lines else "",
            )
        )
    return rvws


# Entry point to get a random movie with reviews
def get_random_movie(film_url: str = None) -> Movie:
    if not film_url:
        film_url = _random_film_choice()
    movie_data = _scrape_movie(film_url)
    movie_data["reviews"] = _scrape_reviews(film_url)
    return Movie(**movie_data)


# Main
if __name__ == "__main__":
    movie = get_random_movie()
    print(movie.model_dump())
