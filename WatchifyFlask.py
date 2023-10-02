from flask import Flask, redirect, request, session, url_for, render_template
from os import environ  # Ensure this import is here
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set secret key from environment variable
app.secret_key = environ.get('SECRET_KEY')

# Set the Spotify API credentials
client_id = '6f8bacd4931e41839442e43813d4fcfb'
client_secret = 'bd500cdc7b674c3087c2eadbdb0ec058'
redirect_uri = 'http://localhost:3000/callback'

# Initialize Spotify API client
sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope='user-top-read')
sp = spotipy.Spotify(auth_manager=sp_oauth)

@app.route('/')
def index():
    if not session.get('token_info'):
        return redirect(url_for('login'))
    token_info = session.get('token_info')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    time_range = 'short_term'
    limit = 10
    top_artists = sp.current_user_top_artists(time_range='short_term', limit=50)

    genre_count = {}
    for artist in top_artists['items']:
        for genre in artist['genres']:
            genre_count[genre] = genre_count.get(genre, 0) + 1

    most_listened_genre = max(genre_count.keys(), key=lambda genre: genre_count[genre])
    
    return f"The most listened genre over the past 30 days is: {most_listened_genre}"

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return render_template('login.html', auth_url=auth_url)

@app.route('/callback')
def callback():
    token_info = sp_oauth.get_access_token(request.args['code'], as_dict=False)  # Update here
    session['token_info'] = token_info
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=3000)
