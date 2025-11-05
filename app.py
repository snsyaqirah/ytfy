from flask import Flask, render_template, request, redirect, url_for, session
from utils.youtube_api import get_playlist_info, get_youtube_oauth_flow, get_youtube_client, create_youtube_playlist, get_user_youtube_playlists
from utils.spotify_api import get_spotify_client, create_spotify_playlist, get_user_playlists, get_spotify_playlist_tracks
import os
from datetime import datetime
from dotenv import load_dotenv

# Allow insecure transport for local development (HTTP instead of HTTPS)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

@app.route("/", methods=["GET"])
def index():
    # Check both auth states independently
    sp = get_spotify_client()
    spotify_authenticated = bool(sp.auth_manager.get_cached_token())
    youtube_authenticated = 'youtube_token' in session
    
    # Get playlists if authenticated
    user_playlists = []
    youtube_playlists = []
    
    if spotify_authenticated:
        user_playlists = get_user_playlists()
    
    if youtube_authenticated:
        youtube_playlists = get_user_youtube_playlists()
    
    return render_template("index.html", 
                         spotify_authenticated=spotify_authenticated,
                         youtube_authenticated=youtube_authenticated,
                         user_playlists=user_playlists,
                         youtube_playlists=youtube_playlists)

@app.route("/convert", methods=["POST"])
def convert():
    try:
        # Check authentication
        sp = get_spotify_client()
        if not sp.auth_manager.get_cached_token():
            return redirect(url_for('spotify_auth'))

        # Get form data
        playlist_url = request.form.get("playlist_url")
        custom_name = request.form.get("playlist_name", "")
        playlist_option = request.form.get("playlist_option", "new")
        existing_playlist_id = request.form.get("existing_playlist", "")

        if not playlist_url:
            raise ValueError("Please provide a YouTube playlist URL")

        # Get YouTube playlist info
        yt_info = get_playlist_info(playlist_url)
        
        # Determine playlist name and ID
        if playlist_option == "existing" and existing_playlist_id:
            # Add to existing playlist
            result = create_spotify_playlist(None, yt_info["songs"], existing_playlist_id=existing_playlist_id)
        else:
            # Create new playlist
            playlist_name = custom_name if custom_name else yt_info["title"]
            result = create_spotify_playlist(playlist_name, yt_info["songs"])
        
        return render_template("result.html", 
                             playlist_url=result['playlist_url'],
                             playlist_name=result['playlist_name'],
                             matched_songs=result['matched_songs'],
                             unmatched_songs=result['unmatched_songs'],
                             total_songs=result['total_songs'],
                             matched_count=result['matched_count'],
                             unmatched_count=result['unmatched_count'],
                             is_new=result['is_new'],
                             conversion_type='youtube_to_spotify')
    
    except Exception as e:
        return render_template("error.html", error=str(e))

@app.route('/spotify_auth')
def spotify_auth():
    sp = get_spotify_client()
    auth_url = sp.auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/logout')
def logout():
    """Clear session and logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/callback')
def callback():
    sp = get_spotify_client()
    token_info = sp.auth_manager.get_cached_token()
    if not token_info:
        token_info = sp.auth_manager.get_access_token(request.args.get('code'), as_dict=False)
    
    # Always redirect to index after auth (no pending conversion)
    return redirect(url_for('index'))

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', last_updated=datetime.now().strftime("%B %d, %Y"))

@app.route("/convert_reverse", methods=["POST"])
def convert_reverse():
    """Convert Spotify playlist to YouTube"""
    try:
        # Check Spotify authentication
        sp = get_spotify_client()
        if not sp.auth_manager.get_cached_token():
            return redirect(url_for('spotify_auth'))
        
        # Check YouTube authentication
        if not get_youtube_client():
            return redirect(url_for('youtube_auth'))

        # Get form data
        playlist_url = request.form.get("playlist_url")
        custom_name = request.form.get("playlist_name", "")
        playlist_option = request.form.get("playlist_option", "new")
        existing_playlist_id = request.form.get("existing_playlist", "")

        if not playlist_url:
            raise ValueError("Please provide a Spotify playlist URL")

        # Get Spotify playlist info
        spotify_info = get_spotify_playlist_tracks(playlist_url)
        
        # Determine playlist name and ID
        if playlist_option == "existing" and existing_playlist_id:
            # Add to existing playlist
            result = create_youtube_playlist(None, spotify_info["songs"], existing_playlist_id=existing_playlist_id)
        else:
            # Create new playlist
            playlist_name = custom_name if custom_name else spotify_info["playlist_name"]
            result = create_youtube_playlist(playlist_name, spotify_info["songs"])
        
        return render_template("result.html", 
                             playlist_url=result['playlist_url'],
                             playlist_name=result['playlist_name'],
                             matched_songs=result['matched_songs'],
                             unmatched_songs=result['unmatched_songs'],
                             total_songs=result['total_songs'],
                             matched_count=result['matched_count'],
                             unmatched_count=result['unmatched_count'],
                             is_new=result['is_new'],
                             conversion_type='spotify_to_youtube')
    
    except Exception as e:
        return render_template("error.html", error=str(e))

@app.route('/youtube_auth')
def youtube_auth():
    """Initiate YouTube OAuth"""
    flow = get_youtube_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['youtube_state'] = state
    return redirect(authorization_url)

@app.route('/youtube_callback')
def youtube_callback():
    """Handle YouTube OAuth callback"""
    state = session.get('youtube_state')
    flow = get_youtube_oauth_flow()
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    session['youtube_token'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    return redirect(url_for('index'))

@app.route('/youtube_logout')
def youtube_logout():
    """Clear YouTube session"""
    if 'youtube_token' in session:
        del session['youtube_token']
    if 'youtube_state' in session:
        del session['youtube_state']
    return redirect(url_for('index'))

if __name__ == "__main__":
    # For local development
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)