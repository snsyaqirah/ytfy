# YTfy - Bidirectional Playlist Converter 🎵

Convert playlists between YouTube/YouTube Music and Spotify!

## ✨ New Feature: Two-Way Conversion

- **YouTube → Spotify**: Convert YouTube Music playlists to Spotify
- **Spotify → YouTube**: Convert Spotify playlists to YouTube (NEW!)

---

## 🔧 Setup Instructions for Spotify → YouTube

### Prerequisites
You already have:
- ✅ Spotify API credentials (Client ID & Secret)
- ✅ YouTube Data API v3 key

### What You Need to Add:

#### 1. Create YouTube OAuth 2.0 Credentials

Go to [Google Cloud Console](https://console.cloud.google.com/):

1. **Select your existing project** (or create new one)
2. **Enable YouTube Data API v3** (if not already enabled)
3. **Create OAuth 2.0 Client ID**:
   - Go to: APIs & Services → Credentials
   - Click: "Create Credentials" → "OAuth client ID"
   - Application type: **Web application**
   - Name: `YTfy OAuth Client`
   - **Authorized redirect URIs**:
     - `http://127.0.0.1:5000/youtube_callback`
     - `http://localhost:5000/youtube_callback`
   - Click "Create"
   - **Save the Client ID and Client Secret**

4. **Add Test Users** (for development):
   - Go to: APIs & Services → OAuth consent screen
   - Scroll to "Test users"
   - Click "Add Users"
   - Add the 3 Google/YouTube accounts that will use the app
   - Click "Save"

#### 2. Update Your `.env` File

Add these new variables to your `.env`:

```bash
# Existing Spotify credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback

# Existing YouTube Data API
YOUTUBE_API_KEY=your_youtube_api_key

# NEW: YouTube OAuth credentials
YOUTUBE_CLIENT_ID=your_youtube_oauth_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_oauth_client_secret
YOUTUBE_REDIRECT_URI=http://127.0.0.1:5000/youtube_callback

# Flask
FLASK_SECRET_KEY=your_secret_key_here
```

#### 3. Update Dependencies

The `requirements.txt` already includes the new packages:
- `google-auth==2.23.0`
- `google-auth-oauthlib==1.1.0`
- `google-api-python-client==2.108.0`

Just rebuild your Docker container:
```bash
docker-compose up -d --build ytfy
```

---

## 🎮 How to Use

### YouTube → Spotify (Existing)
1. Click "Connect Spotify"
2. Paste YouTube playlist URL
3. Choose: Create new or add to existing Spotify playlist
4. Click "Convert to Spotify"

### Spotify → YouTube (NEW!)
1. Click "Connect Spotify"
2. Click "Connect YouTube"
3. Toggle to "Spotify → YouTube" mode
4. Paste Spotify playlist URL
5. Choose: Create new or add to existing YouTube playlist
6. Click "Convert to YouTube"

---

## 📊 API Quotas

### YouTube Data API v3
- **Daily quota**: 10,000 units
- **Create playlist**: 50 units
- **Add video**: 50 units per video
- **Example**: 1 playlist with 50 songs = ~2,550 units
- **Estimate**: ~3-4 full playlist conversions per day

### Spotify API
- No strict daily limits for playlist modifications
- Rate limited to ~180 requests per minute

---

## 🔒 Privacy & Security

- OAuth tokens stored in Flask session (encrypted)
- No data stored on server after conversion
- All API calls made directly between your account and Spotify/YouTube
- Private playlists are kept private

---

## 🐛 Known Issues & Solutions

### Issue: YouTube API quota exceeded
**Solution**: Wait 24 hours for quota reset (resets at midnight Pacific Time)

### Issue: Can't find some songs on YouTube
**Cause**: 
- Song not available as video on YouTube
- Different language/romanization (Korean/Japanese → English)
**Solution**: These songs will be listed as "Not Found" - you can add manually

### Issue: Wrong songs matched
**Cause**: Multiple versions (live, remix, cover) on YouTube
**Future Enhancement**: Add manual review/approval before adding

---

## 🚀 Deployment Notes

### For Development (Current Setup)
- Add up to 100 test users in Google Cloud Console
- No verification needed
- Perfect for personal use with friends

### For Production (If you want public access)
- Need to submit for Google OAuth verification
- Requires privacy policy, terms of service
- Organization/company required (not individual)
- Takes 4-6 weeks for approval

---

## 💡 Tips

1. **Accuracy**: YouTube → Spotify is more accurate than Spotify → YouTube (better song metadata)
2. **Language Issues**: For K-pop/J-pop, results may vary due to title translations
3. **Playlist Size**: Larger playlists (100+ songs) take longer to process
4. **Private Playlists**: Created YouTube playlists are private by default

---

## 🎉 Credits

Made with 💖 by Syaqi
