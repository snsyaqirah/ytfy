from flask import Flask, render_template, request, redirect, url_for, session
from utils.youtube_api import get_youtube_songs
from utils.spotify_api import create_spotify_playlist
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    try:
        playlist_url = request.form.get("playlist_url")
        if not playlist_url:
            raise ValueError("Please provide a YouTube playlist URL")

        songs = get_youtube_songs(playlist_url)
        playlist_url = create_spotify_playlist(songs)
        
        return render_template("result.html", playlist_url=playlist_url)
    
    except Exception as e:
        return render_template("error.html", error=str(e))

if __name__ == "__main__":
    app.run(debug=True)