import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import session
from typing import List
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

def get_spotify_client():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-modify-public",
        cache_handler=cache_handler,
        show_dialog=True
    )
    return spotipy.Spotify(auth_manager=auth_manager)

def create_spotify_playlist(song_titles: List[str]) -> str:
    sp = get_spotify_client()
    
    # Verify we have a valid token
    if not sp.auth_manager.get_cached_token():
        raise Exception("No Spotify token available")

    user_id = sp.me()['id']  # Use me() instead of current_user()
    
    # Create playlist
    playlist = sp.user_playlist_create(
        user_id, 
        "YouTube Imported Playlist",
        public=True,
        description="Playlist imported from YouTube using YTFY"
    )

    # Search and add tracks
    track_ids = []
    for title in song_titles:
        try:
            results = sp.search(q=title, type="track", limit=1)
            if results["tracks"]["items"]:
                track_ids.append(results["tracks"]["items"][0]["id"])
        except Exception as e:
            print(f"Error searching for track {title}: {str(e)}")

    if track_ids:
        # Add tracks in batches of 100 (Spotify API limit)
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i + 100]
            sp.playlist_add_items(playlist["id"], batch)

    return playlist["external_urls"]["spotify"]