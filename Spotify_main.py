# import necessary modules
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

# initialize Flask app
app = Flask(__name__)

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = 'acbdefghi2618'

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'

# route to handle logging in
@app.route('/')
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # redirect the user to the authorization URL
    return redirect(auth_url)

# route to handle the redirect URI after authorization
@app.route('/redirect')
def redirect_page():
    # clear the session
    session.clear()
    # get the authorization code from the request parameters
    code = request.args.get('code')
    # exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # save the token info in the session
    session[TOKEN_INFO] = token_info
    # redirect the user to the save_discover_weekly route
    return redirect(url_for('save_discover_weekly',_external=True))

# route to save the Discover Weekly songs to a playlist
@app.route('/saveDiscoverWeekly')
def save_discover_weekly():
    try:
        token_info = get_token()
    except Exception as e:
        print(e)
        return redirect('/')

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']

    # Print user ID for debugging
    print(f"User ID: {user_id}")

    # Search for the Discover Weekly playlist
    results = sp.search(q='Discover Weekly', type='playlist', limit=10)
    
    discover_weekly_playlist_id = None

    for playlist in results['playlists']['items']:
        if playlist['name'] == 'Discover Weekly':
            discover_weekly_playlist_id = playlist['id']
            break

    if not discover_weekly_playlist_id:
        return 'Discover Weekly playlist not found'

    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    discover_weekly_song_uris = [song['track']['uri'] for song in discover_weekly_playlist['items']]  # Highlighted Change
    song_uris = [song['track']['uri'] for song in discover_weekly_playlist['items']]

    # Retrieve all user playlists and print their names
    current_playlists =  sp.current_user_playlists()['items']
    
    saved_weekly_playlist_id = None

    for playlist in current_playlists:
        if playlist['name'] == "Saved Weekly":
            saved_weekly_playlist_id = playlist['id']

    # Create Saved Weekly playlist if it doesn't exist
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']

    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)

    return 'Discover Weekly songs added'

# function to get the token info from the session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = '9fa60da69909415a9ab5bf0c79cf107c',
        client_secret = '1288efbdf9da40179ce66ceb4d81f1c3',
        redirect_uri = url_for('redirect_page', _external=True),
        scope='user-library-modify playlist-modify-public playlist-modify-private'
    )

app.run(debug=True)