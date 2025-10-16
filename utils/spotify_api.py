import os
import requests
import base64
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/callback"  # Change for production

# Step 1: Get Spotify Auth URL
def get_spotify_auth_url():
    scope = "playlist-modify-public playlist-modify-private"
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": scope,
    }
    return f"https://accounts.spotify.com/authorize?{urlencode(params)}"

# Step 2: Exchange code for access token
def get_spotify_token(code):
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth}"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
    }

    response = requests.post("https://accounts.spotify.com/api/token", data=data, headers=headers)
    response.raise_for_status()
    return response.json()

# Step 3: Create playlist
def create_spotify_playlist(songs, token_info):
    access_token = token_info.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    # Get current user profile
    user_resp = requests.get("https://api.spotify.com/v1/me", headers=headers)
    user_resp.raise_for_status()
    user_id = user_resp.json()["id"]

    # Create new playlist
    payload = {"name": "ytfy Playlist", "description": "Imported from YouTube", "public": False}
    playlist_resp = requests.post(f"https://api.spotify.com/v1/users/{user_id}/playlists",
                                  json=payload, headers=headers)
    playlist_resp.raise_for_status()
    playlist_id = playlist_resp.json()["id"]

    # Search and add tracks
    track_uris = []
    for song in songs:
        query = urlencode({"q": song, "type": "track", "limit": 1})
        search_resp = requests.get(f"https://api.spotify.com/v1/search?{query}", headers=headers)
        if search_resp.ok and search_resp.json().get("tracks", {}).get("items"):
            uri = search_resp.json()["tracks"]["items"][0]["uri"]
            track_uris.append(uri)

    if track_uris:
        requests.post(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                      json={"uris": track_uris}, headers=headers)

    return f"https://open.spotify.com/playlist/{playlist_id}"
