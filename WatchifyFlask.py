from flask import Flask, render_template, request, redirect, url_for, session
from flask_bootstrap import Bootstrap
from os import environ
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import random
import requests
import json

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

bootstrap = Bootstrap(app)

genre_count = {}
recommended_tvshow = []
recommended_movie = []

# Spotify API Credentials
SPOTIPY_CLIENT_ID = '55118ada9eb54f9aa5633d24c6e5e0cf'
SPOTIPY_CLIENT_SECRET = '012b2b6b819a43d895e2b48e59b62d64'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'
 #SPOTIPY_REDIRECT_URI = 'https://shamp00the-cat.github.io/movierecs/callback'

#Michael's ID just to run locally
#SPOTIPY_CLIENT_ID = "6f8bacd4931e41839442e43813d4fcfb"
#SPOTIPY_CLIENT_SECRET = "bd500cdc7b674c3087c2eadbdb0ec058" 
#SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'

sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope=["user-top-read"])

# DALL-E API endpoint and API Key (replace 'YOUR_API_KEY' with your actual API key)
DALL_E_API_ENDPOINT = "https://api.openai.com/v1/images/generations"
DALL_E_API_KEY = "YOUR_API_KEY"

# DB Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@YOUR_RDS_ENDPOINT:5432/watchify' # change
db = SQLAlchemy(app)
class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_genres = db.Column(db.String)
    recommendation_type = db.Column(db.String)
    title = db.Column(db.String)
    genre = db.Column(db.String)
    rating = db.Column(db.Float)
    
    def __init__(self, spotify_genres, recommendation_type, title, genre, rating):
        self.spotify_genres = spotify_genres
        self.recommendation_type = recommendation_type
        self.title = title
        self.genre = genre
        self.rating = rating

# Movie Genre Mapping
movie_genre_mapping = {
    'pop': ['Romance', 'Comedy', 'Family'],
    'art pop': ['Fantasy', 'Drama', 'Adventure'],
    'reggaeton': ['Action', 'Adventure', 'Crime'],
    'urbano latino': ['Action', 'Drama', 'Romance'],
    'trap latino': ['Crime', 'Action', 'Thriller'],
    'rock': ['Action', 'Adventure', 'Drama'],
    'indie rock': ['Drama', 'Romance', 'Comedy'],
    'classical': ['History', 'Biography'],
    'hip hop': ['Drama', 'Crime', 'Action'],
    'jazz': ['Drama', 'Biography', 'Romance'],
    'country': ['Drama', 'Family', 'Romance'],
    'electronic': ['Science Fiction', 'Mystery', 'Action'],
    'metal': ['Horror', 'Thriller', 'Action'],
    'folk': ['Drama', 'History', 'Romance'],
    'blues': ['Drama', 'Crime', 'Romance'],
    'r&b': ['Romance', 'Drama', 'Comedy'],
    'soul': ['Drama', 'Romance', 'Comedy'],
    'punk': ['Action', 'Thriller', 'Comedy'],
    'disco': ['Comedy', 'Romance', 'Action'],
    'house': ['Science Fiction', 'Thriller', 'Action'],
    'techno': ['Science Fiction', 'Action', 'Mystery'],
    'edm': ['Action', 'Science Fiction', 'Thriller'],
    'latin': ['Drama', 'Romance', 'Comedy'],
    'reggae': ['Comedy', 'Adventure', 'Action'],
    'funk': ['Comedy', 'Action', 'Romance'],
    'k-pop': ['Comedy', 'Romance', 'Action'],
    'psychedelic': ['Fantasy', 'Adventure', 'Action'],
    'world': ['History', 'Family', 'Adventure'],
    'ambient': ['Drama', 'Science Fiction', 'Mystery'],
    'lo-fi beats': ['Drama', 'Romance', 'Comedy'],
    'vaporwave': ['Science Fiction', 'Fantasy', 'Romance'],
    'emo': ['Drama', 'Romance', 'Thriller'],
    'hardcore': ['Action', 'Thriller', 'Crime'],
    'dubstep': ['Action', 'Science Fiction', 'Horror'],
    'ska': ['Comedy', 'Adventure', 'Action'],
    'swing': ['Comedy', 'Romance', 'Action'],
    'trance': ['Science Fiction', 'Adventure', 'Action'],
    'grime': ['Crime', 'Action', 'Thriller'],
    'bluegrass': ['Drama', 'Adventure', 'Romance'],
    'new wave': ['Science Fiction', 'Romance', 'Action'],
    'post-punk': ['Drama', 'Thriller', 'Action'],
    'trip hop': ['Mystery', 'Drama', 'Romance'],
    'neosoul': ['Romance', 'Drama', 'Comedy'],
    'afrobeat': ['Drama', 'Adventure', 'Romance'],
    'chillhop': ['Drama', 'Romance', 'Comedy'],
    'synthwave': ['Science Fiction', 'Action', 'Thriller'],
    'latin viral pop': ['Comedy', 'Adventure', 'Romance'],
    'r&b en espanol': ['Romance', 'Drama', 'Comedy']
}

# Genre mapping for TV Shows
tvshow_genre_mapping = {
    'pop': ['Comedy', 'Family'],
    'art pop': ['Drama', 'Fantasy'],
    'reggaeton': ['Reality-TV', 'Music'],
    'urbano latino': ['Comedy', 'Music'],
    'trap latino': ['Crime', 'Drama'],
    'rock': ['Adventure', 'Drama'],
    'indie rock': ['Drama', 'Romance'],
    'classical': ['Biography', 'History'],
    'hip hop': ['Documentary', 'Drama'],
    'jazz': ['Music', 'Documentary'],
    'country': ['Drama', 'Western'],
    'electronic': ['Sci-Fi', 'Drama'],
    'metal': ['Thriller', 'Horror'],
    'folk': ['Drama', 'History'],
    'blues': ['Documentary', 'Music'],
    'r&b': ['Drama', 'Romance'],
    'soul': ['Biography', 'Music'],
    'punk': ['Documentary', 'Music'],
    'disco': ['Comedy', 'Music'],
    'house': ['Reality-TV', 'Music'],
    'techno': ['Documentary', 'Music'],
    'edm': ['Reality-TV', 'Music'],
    'latin': ['Drama', 'Romance'],
    'reggae': ['Documentary', 'Music'],
    'funk': ['Comedy', 'Music'],
    'k-pop': ['Reality-TV', 'Music'],
    'psychedelic': ['Drama', 'Fantasy'],
    'world': ['Documentary', 'Travel'],
    'ambient': ['Documentary', 'Sci-Fi'],
    'lo-fi beats': ['Drama', 'Romance'],
    'vaporwave': ['Sci-Fi', 'Drama'],
    'emo': ['Drama', 'Music'],
    'hardcore': ['Documentary', 'Music'],
    'dubstep': ['Reality-TV', 'Sci-Fi'],
    'ska': ['Comedy', 'Music'],
    'swing': ['Musical', 'History'],
    'trance': ['Sci-Fi', 'Drama'],
    'grime': ['Documentary', 'Crime'],
    'bluegrass': ['Documentary', 'Music'],
    'new wave': ['Drama', 'Sci-Fi'],
    'post-punk': ['Documentary', 'Music'],
    'trip hop': ['Crime', 'Drama'],
    'neosoul': ['Drama', 'Romance'],
    'afrobeat': ['Documentary', 'Music'],
    'chillhop': ['Drama', 'Animation'],
    'synthwave': ['Sci-Fi', 'Drama'],
    'latin viral pop': ['Reality-TV', 'Comedy'],
    'r&b en espanol': ['Drama', 'Music']
}

def generate_dalle_image(prompt):
    headers = {
        "Authorization": f"Bearer {DALL_E_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "n": 1,
        "size": "200x200"
    }
    response = requests.post(DALL_E_API_ENDPOINT, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        image_data = response.json()['data'][0]['image']
        return image_data
    else:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return render_template('loginpage.html', auth_url=auth_url)

@app.route('/callback')
def callback():
    code = request.args['code']
    token = sp_oauth.get_access_token(code, as_dict=False)
    session['token'] = token
    global sp
    sp = spotipy.Spotify(auth=token)
    return redirect(url_for('display_history'))

@app.route('/history')
def display_history():
    # Fetch user's top tracks from the past 30 days (short term)
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='short_term')
    artist_ids = [track['album']['artists'][0]['id'] for track in top_tracks['items']]
    artists = sp.artists(artist_ids)['artists']
    for artist in artists:
        for genre in artist['genres']:
            if genre in genre_count:
              genre_count[genre] += 1
            else:
              genre_count[genre] = 1

    # Ensure that the genres from Spotify are in lowercase for the mapping.
    global top_5_genres 
    top_5_genres = [genre.lower() for genre in sorted(genre_count, key=genre_count.get, reverse=True)[:5]]
    return render_template('displayhistory.html', top_5_genres=top_5_genres)

@app.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    choice = ""
    token = session.get('token')
    if not token:
        return redirect(url_for('login'))

    #sp = spotipy.Spotify(auth=token)
    if request.method == 'POST':
        #Obtains the user choice from the post request
        choice = request.form.get('choice')
        if choice == "movie":
            genre_mapping = movie_genre_mapping
        elif choice == "tvshow":
            genre_mapping = tvshow_genre_mapping
        selection_of_genres = []
        #Goes through the user's top genres
        for spotify_genre in top_5_genres:
            #Splits up the string into individual words
            spotify_genre = spotify_genre.split()
            for word in spotify_genre:  
                #checks to see if one of the words in the genre string is in our dictionary
                if word in genre_mapping:
                    for corresponding_genre in genre_mapping[word]:
                         #Goes through the list in the corresponding dictionary key
                        if corresponding_genre not in selection_of_genres:
                            selection_of_genres.append(corresponding_genre)

        #If no genre was found, it picks a random one
        if len(selection_of_genres) > 0:
            genre_choice = random.choice(selection_of_genres)
        else:
            genre_choice = random.choice(list(genre_mapping.values()))
        if choice == "movie":
            df = pd.read_csv('combined_movies.csv') 
            #filters CSV files by genre and movies with a value in genre
            df_filtered = df[df['genres'].notna() & df['genres'].str.contains(genre_choice)]
            recommended_movie = df_filtered.sample().iloc[0]
            return render_template('displayrecommendation.html', recommended_movie=recommended_movie, choice=choice, genre_choice=genre_choice)
        # # TV Show Filtering
        elif choice == "tvshow":
            df = pd.read_csv('tvshowdata.csv') 
            df_filtered = df[(df['rating'] >= 7.0) & df['genre'].str.contains(genre_choice)]
            recommended_show = df_filtered.sample().iloc[0]
            return render_template('displayrecommendation.html', recommended_show=recommended_show, choice=choice)
        
def generate_image():
    title = request.form.get('title')
    year = request.form.get('year')
    genre = request.form.get('genre')
    rating = request.form.get('rating')
    description = request.form.get('description')
    prompt = f"{title}, released in {year}, is a {genre} with a rating of {rating}/10. {description}"
    image_data = generate_dalle_image(prompt)
    if image_data:
        return render_template('displayrecommendation.html', image_data=image_data)
    else:
        return render_template('displayrecommendation.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)