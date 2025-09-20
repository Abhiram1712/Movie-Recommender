
import streamlit as st
import pickle
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# TMDB API Setup
TMDB_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2MzRkNTEzM2VmZDBjNjgzMDdhNDE0N2E4NjczOGVlOSIsIm5iZiI6MTc1ODMwMDY1Mi44OTUsInN1YiI6IjY4Y2Q4OWVjODQ0YTFmMGUxZWZlOGEyZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.VEemY92tW5uyL3fgVMga0bfX57FBPCAV_E-ONpIVttg"

# Create a session with retries
session = requests.Session()
retry = Retry(
    total=5,                  # retry up to 5 times
    backoff_factor=1,         # wait 1s, 2s, 4s... between retries
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]   # retry only on GET
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)


# Helper Functions
def fetch_poster(movie_id: int) -> str:
    """Fetch poster URL from TMDB safely with retries & error handling."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_BEARER_TOKEN}"
    }
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
        else:
            return "https://via.placeholder.com/500x750.png?text=No+Poster+Available"
    except Exception as e:
        print(f"⚠️ Error fetching poster for movie_id={movie_id}: {e}")
        return "https://via.placeholder.com/500x750.png?text=Error"


def recommend(movie: str):
    """Recommend top 5 similar movies with posters."""
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similar[movie_index]
    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    titles, posters = [], []
    for idx, _ in movies_list:
        # Ensure your movies dataset has a "movie_id" column
        movie_id = movies.iloc[idx].movie_id
        titles.append(movies.iloc[idx].title)
        posters.append(fetch_poster(movie_id))
    return titles, posters


# Load Data
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
similar = pickle.load(open('similar.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)


# Streamlit UI
st.title('Movie Recommendation System')

option = st.selectbox(
    "Select a movie you like:",
    movies['title'].values
)

if st.button('Recommend'):
    recommendations, posters = recommend(option)

    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.text(recommendations[idx])
            st.image(posters[idx])
