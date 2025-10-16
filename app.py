from flask import Flask, render_template, request, redirect, url_for, session
from utils.youtube_api import get_youtube_songs
from utils.spotify_api import get_spotify_client, create_spotify_playlist
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

@app.route("/", methods=["GET"])
def index():
    sp = get_spotify_client()
    if not sp.auth_manager.get_cached_token():
        return render_template("index.html", authenticated=False)
    return render_template("index.html", authenticated=True)

@app.route("/convert", methods=["GET", "POST"])
def convert():
    try:
        sp = get_spotify_client()
        if not sp.auth_manager.get_cached_token():
            if request.method == "POST":
                session['pending_playlist_url'] = request.form.get("playlist_url")
            return redirect(url_for('spotify_auth'))

        if request.method == "GET":
            playlist_url = session.pop('pending_playlist_url', None)
        else:
            playlist_url = request.form.get("playlist_url")

        if not playlist_url:
            return redirect(url_for('index'))

        songs = get_youtube_songs(playlist_url)
        spotify_url = create_spotify_playlist(songs)
        
        return render_template("result.html", playlist_url=spotify_url)
    
    except Exception as e:
        return render_template("error.html", error=str(e))

@app.route('/spotify_auth')
def spotify_auth():
    sp = get_spotify_client()
    auth_url = sp.auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp = get_spotify_client()
    # Update to use get_cached_token to address deprecation warning
    token_info = sp.auth_manager.get_cached_token()
    if not token_info:
        token_info = sp.auth_manager.get_access_token(request.args.get('code'), as_dict=False)
    
    if session.get('pending_playlist_url'):
        return redirect(url_for('convert'))
    
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)