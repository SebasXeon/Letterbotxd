import json
from google import genai
from pydantic import BaseModel
from bot.models import Movie, Review

class ResponseSchema(BaseModel):
    index: int
    text: str


class GeminiWrapper:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key)

    def pick_best_review(self, movie: Movie) -> Review:
        if not movie.reviews:
            raise ValueError("No reviews available for the movie.")

        # Prepare the prompt for Gemini
        prompt = (
            f"Choose the best review for this movie, choose a review either funny or serious. Censor bad words(drugs, sex, etc) changing a letter with * \n"
            f"Title: {movie.title} ({movie.year})\n"
            f"Directed by {movie.director}\n"
            f"Description: {movie.description}\n"
            f"Reviews:\n"
            + "\n".join(f"{i+1}. {review.text}" for i, review in enumerate(movie.reviews))
        )

        # Call Gemini to get the best review
        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            #max_output_tokens=100,
            #temperature=0.5
            config={
                'response_mime_type': 'application/json',
                'response_schema': ResponseSchema,
            },
        )

        respon_data = json.loads(response.text)

        picked_review = movie.reviews[respon_data['index'] - 1]
        picked_review.text = respon_data['text']

        return picked_review