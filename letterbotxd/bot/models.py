from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class Review(BaseModel):
    reviewer: str
    reviewer_pic: HttpUrl | None = None
    rating: float | None = 0
    date: datetime
    likes: int | None = None
    text: str

class Movie(BaseModel):
    url: HttpUrl
    title: str
    year: int | None = None
    director: str | None = None
    description: str | None = None
    duration: int | None = None  # in minutes
    image_url: HttpUrl | None = None
    reviews: list[Review]
    picked_review: Review | None = None