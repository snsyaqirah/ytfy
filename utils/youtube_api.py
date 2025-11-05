import os
import requests
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import re
from typing import List, Dict, Optional
from flask import session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", "http://127.0.0.1:5000/youtube_callback")

# Quota tracking (rough estimate)
quota_used = 0
SEARCH_COST = 100  # Each search costs 100 quota units
INSERT_COST = 50   # Each playlist item insert costs 50 quota units
DAILY_QUOTA = 10000  # Default YouTube API daily quota

def extract_playlist_id(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("list", [None])[0]

def get_playlist_info(playlist_url):
    """Get playlist title and songs from YouTube"""
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        raise ValueError("Invalid YouTube playlist URL")

    # Get playlist details (title)
    playlist_url_api = "https://www.googleapis.com/youtube/v3/playlists"
    playlist_params = {
        "part": "snippet",
        "id": playlist_id,
        "key": YOUTUBE_API_KEY
    }
    
    playlist_response = requests.get(playlist_url_api, params=playlist_params)
    playlist_response.raise_for_status()
    playlist_data = playlist_response.json()
    
    if not playlist_data.get("items"):
        raise ValueError("Playlist not found")
    
    playlist_title = playlist_data["items"][0]["snippet"]["title"]

    # Get playlist items (songs)
    songs = []
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet,contentDetails",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": YOUTUBE_API_KEY
    }

    while True:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if "items" not in data:
            raise ValueError("Invalid API response - no items found")

        for item in data["items"]:
            if "snippet" in item and "title" in item["snippet"]:
                title = item["snippet"]["title"]
                channel_name = item["snippet"].get("videoOwnerChannelTitle", "")
                
                if title not in ["Private video", "Deleted video"]:
                    # Parse and clean the title
                    parsed_info = parse_song_info(title, channel_name)
                    songs.append(parsed_info)

        next_page = data.get("nextPageToken")
        if not next_page:
            break
        params["pageToken"] = next_page

    if not songs:
        raise ValueError("No valid songs found in playlist")

    return {
        "title": playlist_title,
        "songs": songs
    }

def parse_song_info(title, channel_name):
    """Extract artist and song name from YouTube title"""
    original_title = title
    
    # Remove common suffixes and patterns
    patterns_to_remove = [
        r'\(Official Video\)', r'\(Official Music Video\)', r'\[Official Video\]',
        r'\[Official Music Video\]', r'\(Official Audio\)', r'\[Official Audio\]',
        r'\(Lyrics\)', r'\[Lyrics\]', r'- Lyrics', r'Lyrics',
        r'\(Audio\)', r'\[Audio\]',
        r'\(HD\)', r'\[HD\]', r'HD', r'HQ',
        r'\(Official\)', r'\[Official\]',
        r'\(Music Video\)', r'\[Music Video\]',
        r'\(Visualizer\)', r'\[Visualizer\]',
        r"it's lofi hip hop", r"but it's", r"but lofi",
        r'\d{4}',  # Remove years
    ]
    
    cleaned = title
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove extra whitespace and special characters at the end
    cleaned = re.sub(r'[|•\-\s]+$', '', cleaned).strip()
    
    # Try to extract artist and song name
    artist = None
    song_name = None
    
    # Pattern 1: "Artist - Song Name"
    if ' - ' in cleaned:
        parts = cleaned.split(' - ', 1)
        artist = parts[0].strip()
        song_name = parts[1].strip()
    
    # Pattern 2: "Artist: Song Name"
    elif ': ' in cleaned:
        parts = cleaned.split(': ', 1)
        artist = parts[0].strip()
        song_name = parts[1].strip()
    
    # Pattern 3: "Song Name by Artist"
    elif ' by ' in cleaned.lower():
        match = re.search(r'(.+?)\s+by\s+(.+)', cleaned, re.IGNORECASE)
        if match:
            song_name = match.group(1).strip()
            artist = match.group(2).strip()
    
    # Pattern 4: Check if channel name is the artist (common for official channels)
    elif channel_name and " - Topic" in channel_name:
        artist = channel_name.replace(" - Topic", "").strip()
        song_name = cleaned
    
    # If no artist found, just use the cleaned title as song name
    if not artist or not song_name:
        song_name = cleaned
        artist = None
    
    return {
        'original_title': original_title,
        'cleaned_title': cleaned,
        'artist': artist,
        'song_name': song_name,
        'channel_name': channel_name
    }

def clean_song_title(title):
    """Legacy function - kept for backward compatibility"""
    patterns_to_remove = [
        "(Official Video)", "(Official Music Video)", "(Lyrics)", 
        "(Audio)", "[Official Video]", "[Official Music Video]",
        "| Official Music Video", "- Official Music Video",
        "(Official Audio)", "[Official Audio]", "HD", "HQ"
    ]
    
    cleaned = title
    for pattern in patterns_to_remove:
        cleaned = cleaned.replace(pattern, "")
    
    cleaned = " ".join(cleaned.split())
    return cleaned

def get_youtube_songs(playlist_url):
    """Legacy function for backward compatibility"""
    info = get_playlist_info(playlist_url)
    return info["songs"]

# ============================================
# YouTube OAuth & Playlist Creation Functions
# ============================================

def get_youtube_oauth_flow():
    """Create YouTube OAuth flow"""
    client_config = {
        "web": {
            "client_id": YOUTUBE_CLIENT_ID,
            "client_secret": YOUTUBE_CLIENT_SECRET,
            "redirect_uris": [YOUTUBE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/youtube.force-ssl'],
        redirect_uri=YOUTUBE_REDIRECT_URI
    )
    return flow

def get_youtube_client():
    """Get authenticated YouTube client from session"""
    if 'youtube_token' not in session:
        return None
    
    credentials = Credentials(**session['youtube_token'])
    youtube = build('youtube', 'v3', credentials=credentials)
    return youtube

def search_youtube_video(query: str, max_results: int = 10) -> Optional[Dict]:
    """Search for a video on YouTube and YouTube Music, return the best match"""
    global quota_used
    
    try:
        # Use simple API key search (no auth needed for searching)
        base_url = "https://www.googleapis.com/youtube/v3/search"
        
        # Try multiple search strategies (but stop when we find a good match!)
        search_queries = [
            query,  # Original query with "official"
            query.replace(" official", ""),  # Without "official"
            query.replace(" official", " audio"),  # Try "audio" instead
            query.replace(" official", " lyrics"),  # Try "lyrics" version
        ]
        
        for attempt, search_query in enumerate(search_queries):
            params = {
                "part": "snippet",
                "q": search_query,
                "type": "video",
                "maxResults": max_results,
                "key": YOUTUBE_API_KEY,
                "videoCategoryId": "10"  # Music category
            }
            
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Track quota usage
                quota_used += SEARCH_COST
                remaining = DAILY_QUOTA - quota_used
                print(f"   [Quota: {quota_used}/{DAILY_QUOTA} used, {remaining} remaining]")
                
                if data.get("items") and len(data["items"]) > 0:
                    # Look for best match in results
                    for item in data["items"]:
                        video_id = item["id"]["videoId"]
                        title = item["snippet"]["title"]
                        channel = item["snippet"]["channelTitle"]
                        
                        # Prefer official channels and videos with "Official" in title
                        is_official = (
                            "Official" in title or
                            "VEVO" in channel.upper() or
                            "Topic" in channel or
                            "Music" in title
                        )
                        
                        # If first attempt and we found official video, use it immediately
                        if attempt == 0 and is_official:
                            print(f"   ✓ Found (official): {title} by {channel}")
                            return {
                                'video_id': video_id,
                                'title': title,
                                'channel': channel
                            }
                        
                        # If not first attempt, take any result
                        if attempt > 0:
                            print(f"   ✓ Found (attempt {attempt + 1}): {title} by {channel}")
                            return {
                                'video_id': video_id,
                                'title': title,
                                'channel': channel
                            }
                    
                    # If first attempt but no official video, take the first result anyway
                    if attempt == 0 and data["items"]:
                        first = data["items"][0]
                        print(f"   ✓ Found (best match): {first['snippet']['title']}")
                        return {
                            'video_id': first["id"]["videoId"],
                            'title': first["snippet"]["title"],
                            'channel': first["snippet"]["channelTitle"]
                        }
                
                # Only try next search variation if this one found nothing
                if attempt < len(search_queries) - 1:
                    print(f"   → Trying alternative search (attempt {attempt + 2})...")
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print(f"   ✗ YouTube API quota exceeded! Please wait 24 hours or use a different API key.")
                    return None
                raise
        
        print(f"   ✗ No YouTube results found after {len(search_queries)} attempts")
        return None
    except Exception as e:
        print(f"   ✗ Error searching YouTube: {str(e)}")
        return None

def create_youtube_playlist(playlist_name: str, songs: List[Dict], existing_playlist_id: Optional[str] = None) -> Dict:
    """Create a YouTube playlist or add to existing one"""
    global quota_used
    
    youtube = get_youtube_client()
    
    if not youtube:
        raise Exception("Not authenticated with YouTube. Please connect your YouTube account.")
    
    # Create new playlist or use existing
    if existing_playlist_id:
        playlist_id = existing_playlist_id
        # Get playlist details
        playlist_response = youtube.playlists().list(
            part="snippet",
            id=playlist_id
        ).execute()
        playlist_name = playlist_response["items"][0]["snippet"]["title"]
        is_new = False
    else:
        # Create new playlist
        playlist_request = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_name,
                    "description": "Playlist imported from Spotify using YTfy"
                },
                "status": {
                    "privacyStatus": "private"  # Can be: private, public, unlisted
                }
            }
        ).execute()
        playlist_id = playlist_request["id"]
        is_new = True
    
    print(f"Working with playlist ID: {playlist_id}")
    print(f"📊 Starting conversion - Estimated quota cost: {len(songs) * (SEARCH_COST + INSERT_COST)} units")
    print(f"📊 Current quota used: {quota_used}/{DAILY_QUOTA}")
    
    # Search and add videos
    matched_songs = []
    unmatched_songs = []
    
    for idx, song in enumerate(songs):
        artist = song.get('artist', '')
        track_name = song.get('track_name', '')
        
        # Create search query - try multiple variations
        if artist and track_name:
            search_query = f"{artist} {track_name} official"
        else:
            search_query = track_name or artist or str(song)
        
        print(f"[{idx+1}/{len(songs)}] Searching: {search_query.replace(' official', '')}")
        
        # Search for video
        video_result = search_youtube_video(search_query)
        
        if video_result and video_result.get('video_id'):
            video_id = video_result['video_id']
            video_title = video_result.get('title', 'Unknown')
            
            try:
                # Add video to playlist with retry logic
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        youtube.playlistItems().insert(
                            part="snippet",
                            body={
                                "snippet": {
                                    "playlistId": playlist_id,
                                    "resourceId": {
                                        "kind": "youtube#video",
                                        "videoId": video_id
                                    }
                                }
                            }
                        ).execute()
                        
                        # Track quota usage for insert
                        quota_used += INSERT_COST
                        
                        print(f"✓ Added: {video_title}")
                        
                        matched_songs.append({
                            'spotify_track': f"{artist} - {track_name}" if artist else track_name,
                            'youtube_title': video_title,
                            'video_id': video_id,
                            'youtube_url': f"https://www.youtube.com/watch?v={video_id}"
                        })
                        break  # Success, exit retry loop
                        
                    except Exception as insert_error:
                        if retry < max_retries - 1:
                            print(f"   → Retry {retry + 1}/{max_retries} due to: {str(insert_error)[:50]}")
                            import time
                            time.sleep(1)  # Wait 1 second before retry
                        else:
                            # Final retry failed
                            raise insert_error
                            
            except Exception as e:
                error_msg = str(e)
                print(f"✗ Error adding {video_id}: {error_msg}")
                unmatched_songs.append({
                    'title': f"{artist} - {track_name}" if artist else track_name,
                    'reason': f'Found but failed to add: {error_msg}'
                })
        else:
            print(f"✗ No video found for: {search_query}")
            unmatched_songs.append({
                'title': f"{artist} - {track_name}" if artist else track_name,
                'reason': 'No video found on YouTube'
            })
    
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    
    print(f"\n✓ Playlist complete: {len(matched_songs)} matched, {len(unmatched_songs)} unmatched")
    print(f"📊 Total quota used this session: {quota_used}/{DAILY_QUOTA} ({(quota_used/DAILY_QUOTA*100):.1f}%)")
    print(f"📊 Remaining quota: {DAILY_QUOTA - quota_used} units (~{(DAILY_QUOTA - quota_used)//(SEARCH_COST + INSERT_COST)} more songs)")
    
    return {
        'playlist_url': playlist_url,
        'playlist_id': playlist_id,
        'playlist_name': playlist_name,
        'matched_songs': matched_songs,
        'unmatched_songs': unmatched_songs,
        'total_songs': len(songs),
        'matched_count': len(matched_songs),
        'unmatched_count': len(unmatched_songs),
        'is_new': is_new
    }

def get_user_youtube_playlists():
    """Get user's YouTube playlists"""
    youtube = get_youtube_client()
    
    if not youtube:
        return []
    
    try:
        playlists = []
        request = youtube.playlists().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=50
        )
        
        while request:
            response = request.execute()
            
            for item in response.get("items", []):
                playlists.append({
                    'id': item['id'],
                    'name': item['snippet']['title'],
                    'tracks_total': item['contentDetails']['itemCount']
                })
            
            request = youtube.playlists().list_next(request, response)
        
        return playlists
    except Exception as e:
        print(f"Error fetching YouTube playlists: {str(e)}")
        return []
