from flask import Flask, redirect, request, session, url_for, render_template
from os import environ
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set secret key from environment variable
app.secret_key = environ.get('SECRET_KEY')

# Set the Spotify API credentials
client_id = environ.get('CLIENT_ID')
client_secret = environ.get('CLIENT_SECRET')
redirect_uri = 'https://shamp00the-cat.github.io/movierecs/callback' 
redirect_uri = 'https://shamp00the-cat.github.io/movierecs/displayhistory'

# Initialize Spotify API client
sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope='user-top-read')
sp = spotipy.Spotify(auth_manager=sp_oauth)

@app.route('/')
def index():
    if not session.get('token_info'):
        return redirect(url_for('loginpage'))
    token_info = session.get('token_info')
    sp = spotipy.Spotify(auth=token_info['access_token'])

    time_range = 'short_term'
    top_artists = sp.current_user_top_artists(time_range='short_term', limit=50)

    genre_count = {}
    for artist in top_artists['items']:
        for genre in artist['genres']:
            genre_count[genre] = genre_count.get(genre, 0) + 1

    most_listened_genre = max(genre_count.keys(), key=lambda genre: genre_count[genre])

    return f"The most listened genre over the past 30 days is: {most_listened_genre}"

@app.route('/loginpage')
def loginpage():
    auth_url = sp_oauth.get_authorize_url()
    return render_template('loginpage.html', auth_url=auth_url)

@app.route('/displayhistory')
def display_history():
    if not session.get('token_info'):
        return redirect(url_for('loginpage'))
    return render_template('displayhistory.html')

@app.route('/callback')
def callback():
    token_info = sp_oauth.get_access_token(request.args['code'], as_dict=False)
    session['token_info'] = token_info
    # Redirect to the display_history route after obtaining the token information
    return redirect(url_for('display_history'))


if __name__ == '__main__':
    app.run(debug=True, port=3000)
