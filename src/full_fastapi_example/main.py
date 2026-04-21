import os

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Movies API")

MY_MOVIES = [
    {"name": "Chinatown"},
    {"name": "One Battle After Another"},
]


class MovieLookupRequest(BaseModel):
    tmdb_id: int


@app.get("/movies")
def list_movies() -> list[dict[str, str]]:
    return MY_MOVIES


@app.post("/movies")
def lookup_movie(request: MovieLookupRequest) -> dict[str, str]:
    api_key = os.environ["TMDB_API_KEY"]
    response = httpx.get(
        f"https://api.themoviedb.org/3/movie/{request.tmdb_id}",
        params={"api_key": api_key},
        timeout=10.0,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"title": response.json()["title"]}


def run() -> None:
    uvicorn.run(
        "full_fastapi_example.main:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
