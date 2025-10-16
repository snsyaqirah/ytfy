from flask import Flask, render_template, request, redirect, session
from utils.youtube_api import get_youtube_songs
from utils.spotify_api import create_spotify_playlist
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/transfer', methods=['POST'])
def transfer():
    yt_url = request.form.get('yt_url')
    songs = get_youtube_songs(yt_url)
    playlist_link = create_spotify_playlist(songs)
    return f"<p>Done! Your playlist: <a href='{playlist_link}'>{playlist_link}</a></p>"

if __name__ == "__main__":
    app.run(debug=True)
