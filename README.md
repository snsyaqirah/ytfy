# ytfy

ytfy is a bidirectional playlist converter that transfers playlists between YouTube Music and Spotify using Flask and the official APIs from both platforms.

---

## Overview

Manually recreating playlists across music platforms is time-consuming.  
ytfy solves this by automating the process in both directions:
- **YouTube → Spotify**: Paste your YouTube playlist URL, and it will create the same playlist on Spotify
- **Spotify → YouTube**: Paste your Spotify playlist URL, and it will create the same playlist on YouTube

---

## Features

- 🎵 **Bidirectional Conversion**: Convert playlists from YouTube to Spotify OR Spotify to YouTube
- 🔍 **Smart Song Matching**: Automatically searches and matches songs across platforms
- 📝 **Flexible Playlist Options**: Create new playlists or add to existing ones
- 🔒 **Private Playlist Support**: Access and convert your private playlists
- 🎨 **Modern UI**: Clean, responsive interface with real-time auth status
- 📊 **Quota Tracking**: Monitor YouTube API usage to optimize conversions
- 🔄 **Retry Logic**: Automatically handles transient API errors
- ✅ **High Match Rate**: Advanced search algorithm with multiple fallback strategies

---

## Tech Stack

**Backend:** Flask 3.0.0 (Python)  
**Frontend:** HTML + Tailwind CSS  
**APIs:** YouTube Data API v3, Spotify Web API  
**Container:** Docker with Gunicorn WSGI server  
**Deployment:** Render-ready with Docker Compose support

---

## How It Works

### YouTube → Spotify
1. Paste YouTube playlist URL
2. ytfy reads the playlist (no auth needed)
3. Searches for each song on Spotify
4. Creates/updates your Spotify playlist

### Spotify → YouTube
1. Connect both Spotify and YouTube accounts
2. Paste Spotify playlist URL
3. ytfy reads your playlist (including private ones)
4. Searches for each song on YouTube (with smart fallback strategies)
5. Creates/updates your YouTube playlist

---

## Privacy & Security

- ✅ All connections use HTTPS encryption
- ✅ No data storage - everything is processed in real-time
- ✅ Session-based authentication only
- ✅ You can revoke access anytime through Spotify/YouTube settings
- ✅ Open source - audit the code yourself!

---

## API Usage

**YouTube API**: Uses search (100 units/song) and playlist insertion (50 units/song)  
**Daily Quota**: 10,000 units = ~66 songs converted per day  
**Quota Tracking**: Real-time monitoring displayed in console logs

---
