from flask import Flask, render_template, request, redirect, session, url_for
from utils.youtube_api import get_youtube_songs
from utils.spotify_api import (
    create_spotify_playlist,
    get_spotify_auth_url,
    get_spotify_token
)
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/callback"  # Update for production

# 🏠 Home Page
@app.route('/')
def home():
    if "spotify_token" in session:
        return render_template("index.html", logged_in=True)
    return render_template("index.html", logged_in=False)

# 🎧 Step 1: Redirect to Spotify authorization
@app.route('/authorize')
def authorize():
    auth_url = get_spotify_auth_url()
    return redirect(auth_url)

# 🔑 Step 2: Handle Spotify callback
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Authorization failed — no code provided", 400

    try:
        token_info = get_spotify_token(code)
        session['spotify_token'] = token_info
        return redirect(url_for('home'))
    except Exception as e:
        return f"Error fetching Spotify token: {e}", 500

# 🔁 Step 3: Transfer YouTube playlist → Spotify
@app.route('/transfer', methods=['POST'])
def transfer():
    yt_url = request.form.get('yt_url')
    if not yt_url:
        return render_template('error.html', message="Please provide a YouTube playlist URL")

    try:
        songs = get_youtube_songs(yt_url)
        if not songs:
            return render_template('error.html', message="Couldn't fetch songs from YouTube")

        if 'spotify_token' not in session:
            return redirect(url_for('authorize'))

        playlist_link = create_spotify_playlist(songs, session['spotify_token'])
        return render_template('result.html', playlist_link=playlist_link)

    except Exception as e:
        return render_template('error.html', message=str(e))


if __name__ == "__main__":
    app.run(debug=True)
