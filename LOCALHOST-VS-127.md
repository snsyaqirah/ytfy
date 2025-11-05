# ⚠️ Important: Use 127.0.0.1, NOT localhost

## The Issue

When you try to access the app using different URLs, you'll run into problems:
- ❌ `http://localhost:5000` - Will NOT work properly
- ✅ `http://127.0.0.1:5000` - Will work correctly

## Why?

### Technical Explanation
Even though `localhost` and `127.0.0.1` resolve to the same IP address, they are treated as **different domains** by your browser for security purposes.

### The Problem
1. **Cookies are domain-specific**
   - Flask stores your session in a cookie
   - If you authorize with Spotify at `127.0.0.1:5000`, the cookie is set for `127.0.0.1`
   - If you then visit `localhost:5000`, your browser won't send that cookie
   - The app thinks you're not logged in!

2. **OAuth redirects**
   - Your `.env` file has: `SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback`
   - If you start at `localhost:5000`, Spotify redirects to `127.0.0.1:5000`
   - Domain mismatch = lost session = broken auth

3. **YouTube OAuth same issue**
   - `YOUTUBE_REDIRECT_URI=http://127.0.0.1:5000/youtube_callback`
   - Must use `127.0.0.1` consistently

## The Solution

**ALWAYS use `http://127.0.0.1:5000`** in your browser!

### Quick Fix
If you accidentally used `localhost`:
1. Clear your browser cookies for both domains
2. Close all browser tabs with the app
3. Open a new tab and go to `http://127.0.0.1:5000`
4. Re-authenticate with Spotify and YouTube

### Alternative (Advanced)
If you really want to use `localhost`, update ALL these places:
1. `.env` file:
   ```bash
   SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
   YOUTUBE_REDIRECT_URI=http://localhost:5000/youtube_callback
   ```
2. Google Cloud Console:
   - OAuth 2.0 redirect URIs
   - Change from `127.0.0.1` to `localhost`
3. Spotify Developer Dashboard:
   - Redirect URIs
   - Change from `127.0.0.1` to `localhost`

**But honestly? Just use `127.0.0.1` and save yourself the trouble! 😄**

---

## Current Configuration

Your current setup uses:
- ✅ Docker binds to: `127.0.0.1:5000`
- ✅ Spotify redirects to: `http://127.0.0.1:5000/callback`
- ✅ YouTube redirects to: `http://127.0.0.1:5000/youtube_callback`

**Bookmark this:** http://127.0.0.1:5000

---

## Still Getting Errors?

### Error: "Internal Server Error" after YouTube OAuth
**Fix applied!** We added `OAUTHLIB_INSECURE_TRANSPORT=1` to allow HTTP in development.

### Error: Lost session after authorization
**Check:** Make sure you're using `127.0.0.1` in your browser address bar, not `localhost`.

### Error: "Invalid redirect URI"
**Fix:** Make sure your Google Cloud Console OAuth settings have exactly:
```
http://127.0.0.1:5000/youtube_callback
```

---

Happy converting! 🎵
