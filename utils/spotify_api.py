import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import session
from typing import List, Dict, Optional
from dotenv import load_dotenv
import re

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
        scope="playlist-modify-public playlist-modify-private",
        cache_handler=cache_handler,
        show_dialog=True
    )
    return spotipy.Spotify(auth_manager=auth_manager)

def get_user_playlists():
    """Get all user's playlists"""
    sp = get_spotify_client()
    
    if not sp.auth_manager.get_cached_token():
        return []
    
    user_id = sp.me()['id']
    playlists = []
    offset = 0
    limit = 50
    
    while True:
        results = sp.current_user_playlists(limit=limit, offset=offset)
        
        for item in results['items']:
            # Only include playlists owned by the user
            if item['owner']['id'] == user_id:
                playlists.append({
                    'id': item['id'],
                    'name': item['name'],
                    'tracks_total': item['tracks']['total']
                })
        
        if not results['next']:
            break
        offset += limit
    
    return playlists

def create_spotify_playlist(playlist_name: str, song_infos: List[Dict], existing_playlist_id: Optional[str] = None) -> Dict:
    """Create a new playlist or add to existing playlist."""
    sp = get_spotify_client()
    
    if not sp.auth_manager.get_cached_token():
        raise Exception("No Spotify token available")

    user_id = sp.me()['id']
    
    # Create new playlist or use existing one
    if existing_playlist_id:
        playlist = sp.playlist(existing_playlist_id)
        playlist_url = playlist["external_urls"]["spotify"]
        playlist_name = playlist["name"]
    else:
        # Create new playlist with custom name
        playlist = sp.user_playlist_create(
            user_id, 
            playlist_name,
            public=True,
            description="Playlist imported from YouTube using YTfy"
        )
        playlist_url = playlist["external_urls"]["spotify"]

    # Search and add tracks with smart fallback
    track_ids = []
    matched_songs = []
    unmatched_songs = []
    
    for song_info in song_infos:
        try:
            result = search_track_intelligent(sp, song_info)
            
            if result:
                track_ids.append(result['id'])
                matched_songs.append({
                    'youtube_title': song_info['original_title'],
                    'spotify_name': result['name'],
                    'spotify_artist': result['artists'][0]['name'],
                    'match_confidence': result.get('confidence', 'medium')
                })
            else:
                unmatched_songs.append({
                    'title': song_info['original_title'],
                    'reason': 'No confident match found - skipped to avoid incorrect song'
                })
                
        except Exception as e:
            print(f"Error searching for track {song_info['original_title']}: {str(e)}")
            unmatched_songs.append({
                'title': song_info['original_title'],
                'reason': f'Search error'
            })

    # Add tracks in batches
    if track_ids:
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i + 100]
            sp.playlist_add_items(playlist["id"], batch)

    return {
        'playlist_url': playlist_url,
        'playlist_name': playlist_name,
        'matched_songs': matched_songs,
        'unmatched_songs': unmatched_songs,
        'total_songs': len(song_infos),
        'matched_count': len(matched_songs),
        'unmatched_count': len(unmatched_songs),
        'is_new': not existing_playlist_id
    }

def search_track_intelligent(sp, song_info) -> Optional[Dict]:
    """Smart search with multiple fallback levels - only returns confident matches."""
    
    artist = song_info.get('artist')
    song_name = song_info.get('song_name')
    original_title = song_info.get('original_title')
    
    # Level 1: Search with both artist and song name (HIGHEST CONFIDENCE)
    if artist and song_name:
        search_query = f'track:"{song_name}" artist:"{artist}"'
        results = sp.search(q=search_query, type="track", limit=10)
        
        if results["tracks"]["items"]:
            best_match = find_best_match(results["tracks"]["items"], artist, song_name, min_threshold=0.65)
            if best_match:
                best_match['confidence'] = 'high'
                return best_match
    
    # Level 2: Search song name, filter by artist manually
    if artist and song_name:
        search_query = f'"{song_name}"'
        results = sp.search(q=search_query, type="track", limit=20)
        
        if results["tracks"]["items"]:
            for track in results["tracks"]["items"]:
                track_artists = [a['name'].lower() for a in track['artists']]
                artist_lower = artist.lower()
                
                if any(artist_lower == ta or ta in artist_lower for ta in track_artists):
                    from difflib import SequenceMatcher
                    name_similarity = SequenceMatcher(None, song_name.lower(), track['name'].lower()).ratio()
                    
                    if name_similarity > 0.7:
                        track['confidence'] = 'high'
                        return track
    
    # Level 3: No artist info - search title and pick most popular
    if song_name and not artist:
        search_query = f'"{song_name}"'
        results = sp.search(q=search_query, type="track", limit=10)
        
        if results["tracks"]["items"]:
            sorted_tracks = sorted(results["tracks"]["items"], key=lambda x: x.get('popularity', 0), reverse=True)
            
            from difflib import SequenceMatcher
            for track in sorted_tracks[:3]:
                name_similarity = SequenceMatcher(None, song_name.lower(), track['name'].lower()).ratio()
                
                if name_similarity > 0.8:
                    track['confidence'] = 'medium'
                    return track
    
    # Level 4: Check if artist name appears in original title
    if song_name:
        search_query = f'"{song_name}"'
        results = sp.search(q=search_query, type="track", limit=15)
        
        if results["tracks"]["items"]:
            original_lower = original_title.lower()
            
            for track in results["tracks"]["items"]:
                track_artists = [a['name'].lower() for a in track['artists']]
                
                if any(ta in original_lower or original_lower in ta for ta in track_artists):
                    from difflib import SequenceMatcher
                    name_similarity = SequenceMatcher(None, song_name.lower(), track['name'].lower()).ratio()
                    
                    if name_similarity > 0.75:
                        track['confidence'] = 'medium'
                        return track
    
    return None

def find_best_match(tracks, artist, song_name, min_threshold=0.65):
    """Find the best matching track with minimum quality threshold."""
    from difflib import SequenceMatcher
    
    best_score = 0
    best_track = None
    
    for track in tracks:
        song_similarity = SequenceMatcher(None, song_name.lower(), track['name'].lower()).ratio()
        track_artists = ' '.join([a['name'] for a in track['artists']]).lower()
        artist_similarity = SequenceMatcher(None, artist.lower(), track_artists).ratio()
        
        score = (artist_similarity * 0.7) + (song_similarity * 0.3)
        
        if artist_similarity > 0.6 and song_similarity > 0.6 and score > best_score:
            best_score = score
            best_track = track
    
    if best_score >= min_threshold:
        return best_track
    
    return None