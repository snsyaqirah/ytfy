import os
import requests
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import re

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

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