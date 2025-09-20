

import os
import pickle
import pandas as pd
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========================
# Download helper
# ========================
def download_file(file_id, output):
    """Download a file from Google Drive if not present locally."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    if not os.path.exists(output):
        with st.spinner(f"Downloading {output}... Please wait."):
            r = requests.get(url, allow_redirects=True)
            r.raise_for_status()
            with open(output, "wb") as f:
                f.write(r.content)

# ========================
# Download model files
# ========================
download_file("1HJziR65p1k0yb1wB00RhdQ5Ja9jSleOT", "similar.pkl")      # replace with your real ID
download_file("1tzcEeyuMhQSaTb-kJUHWD8j4I1e-QDGV", "movies_dict.pkl")     # replace with your real ID

# Load model data
with open("similar.pkl", "rb") as f:
    similar = pickle.load(f)

with open("movies_dict.pkl", "rb") as f:
    movies_dict = pickle.load(f)

movies = pd.DataFrame(movies_dict)

st.success("Models loaded successfully!")

# ========================
# TMDB API Setup
# ========================
TMDB_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2MzRkNTEzM2VmZDBjNjgzMDdhNDE0N2E4NjczOGVlOSIsIm5iZiI6MTc1ODMwMDY1Mi44OTUsInN1YiI6IjY4Y2Q4OWVjODQ0YTFmMGUxZWZlOGEyZCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.VEemY92tW5uyL3fgVMga0bfX57FBPCAV_E-ONpIVttg"

session = requests.Session()
retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

def fetch_poster(movie_id: int) -> str:
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    headers = {"accept": "application/json", "Authorization": f"Bearer {TMDB_BEARER_TOKEN}"}
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        return f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "https://via.placeholder.com/500x750.png?text=No+Poster"
    except Exception as e:
        print(f"⚠️ Error fetching poster for movie_id={movie_id}: {e}")
        return "https://via.placeholder.com/500x750.png?text=Error"

def recommend(movie: str):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similar[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    titles, posters = [], []
    for idx, _ in movies_list:
        movie_id = movies.iloc[idx].movie_id
        titles.append(movies.iloc[idx].title)
        posters.append(fetch_poster(movie_id))
    return titles, posters

# ========================
# Streamlit UI
# ========================
st.title("🎬 Movie Recommendation System")

option = st.selectbox("Select a movie you like:", movies['title'].values)

if st.button("Recommend"):
    recommendations, posters = recommend(option)
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.text(recommendations[idx])
            st.image(posters[idx])
