import os
import requests
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def extract_playlist_id(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("list", [None])[0]

def get_youtube_songs(playlist_url):
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        raise ValueError("Invalid YouTube playlist URL")

    songs = []
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": YOUTUBE_API_KEY
    }

    while True:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            title = item["snippet"]["title"]
            songs.append(title)

        next_page = data.get("nextPageToken")
        if not next_page:
            break
        params["pageToken"] = next_page

    return songs
