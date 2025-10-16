import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI]):
    raise ValueError("Missing Spotify credentials in environment variables")

def create_spotify_playlist(song_titles: List[str]) -> str:
    """Create a Spotify playlist from song titles.
    
    Args:
        song_titles: List of song titles to search and add
        
    Returns:
        str: URL of the created Spotify playlist
    """
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-modify-public"
    ))

    # Create new playlist
    user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(
        user_id, 
        "YouTube Imported Playlist",
        public=True,
        description="Playlist imported from YouTube using YTFY"
    )

    # Search and add tracks
    track_ids = []
    for title in song_titles:
        results = sp.search(q=title, type="track", limit=1)
        if results["tracks"]["items"]:
            track_ids.append(results["tracks"]["items"][0]["id"])

    if track_ids:
        sp.playlist_add_items(playlist["id"], track_ids)

    return playlist["external_urls"]["spotify"]