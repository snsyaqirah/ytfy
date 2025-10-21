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
        "part": "snippet",
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
                if title not in ["Private video", "Deleted video"]:
                    # Clean up common YouTube title patterns
                    cleaned_title = clean_song_title(title)
                    songs.append(cleaned_title)

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

def clean_song_title(title):
    """Clean YouTube title for better Spotify matching"""
    # Remove common patterns
    patterns_to_remove = [
        "(Official Video)", "(Official Music Video)", "(Lyrics)", 
        "(Audio)", "[Official Video]", "[Official Music Video]",
        "| Official Music Video", "- Official Music Video",
        "(Official Audio)", "[Official Audio]", "HD", "HQ"
    ]
    
    cleaned = title
    for pattern in patterns_to_remove:
        cleaned = cleaned.replace(pattern, "")
    
    # Remove extra whitespace
    cleaned = " ".join(cleaned.split())
    
    return cleaned

def get_youtube_songs(playlist_url):
    """Legacy function for backward compatibility"""
    info = get_playlist_info(playlist_url)
    return info["songs"]