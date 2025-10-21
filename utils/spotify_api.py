import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import session
from typing import List, Dict
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

def create_spotify_playlist(playlist_name: str, song_titles: List[str]) -> Dict:
    """Create a Spotify playlist from song titles with detailed results.
    
    Returns:
        Dict with playlist_url, matched_songs, and unmatched_songs
    """
    sp = get_spotify_client()
    
    if not sp.auth_manager.get_cached_token():
        raise Exception("No Spotify token available")

    user_id = sp.me()['id']
    
    # Create playlist with custom name
    playlist = sp.user_playlist_create(
        user_id, 
        playlist_name,
        public=True,
        description="Playlist imported from YouTube using YTfy"
    )

    # Search and add tracks with better matching
    track_ids = []
    matched_songs = []
    unmatched_songs = []
    
    for title in song_titles:
        try:
            # Try multiple search strategies
            results = search_track_fuzzy(sp, title)
            
            if results:
                track_ids.append(results['id'])
                matched_songs.append({
                    'youtube_title': title,
                    'spotify_name': results['name'],
                    'spotify_artist': results['artists'][0]['name']
                })
            else:
                unmatched_songs.append(title)
                
        except Exception as e:
            print(f"Error searching for track {title}: {str(e)}")
            unmatched_songs.append(title)

    # Add tracks in batches
    if track_ids:
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i + 100]
            sp.playlist_add_items(playlist["id"], batch)

    return {
        'playlist_url': playlist["external_urls"]["spotify"],
        'playlist_name': playlist_name,
        'matched_songs': matched_songs,
        'unmatched_songs': unmatched_songs,
        'total_songs': len(song_titles),
        'matched_count': len(matched_songs),
        'unmatched_count': len(unmatched_songs)
    }

def search_track_fuzzy(sp, title):
    """Try multiple search strategies for better matching"""
    # Strategy 1: Exact title search
    results = sp.search(q=title, type="track", limit=1)
    if results["tracks"]["items"]:
        return results["tracks"]["items"][0]
    
    # Strategy 2: Remove special characters
    cleaned = ''.join(e for e in title if e.isalnum() or e.isspace())
    results = sp.search(q=cleaned, type="track", limit=1)
    if results["tracks"]["items"]:
        return results["tracks"]["items"][0]
    
    # Strategy 3: Try splitting by common separators (-, |, ft., feat.)
    separators = [' - ', ' | ', ' ft.', ' ft ', ' feat.', ' feat ']
    for sep in separators:
        if sep in title.lower():
            parts = title.split(sep)
            search_query = f"track:{parts[0].strip()}"
            if len(parts) > 1:
                search_query += f" artist:{parts[1].strip()}"
            results = sp.search(q=search_query, type="track", limit=1)
            if results["tracks"]["items"]:
                return results["tracks"]["items"][0]
    
    return None