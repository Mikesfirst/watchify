from flask import Flask, render_template, request, redirect, url_for, session
from os import environ
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import random

# Load environment variables from .env file
load_dotenv('.env')

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

# Spotify API Credentials
SPOTIPY_CLIENT_ID = 'ecec60c9a316409a84a45c923f7473ee'
SPOTIPY_CLIENT_SECRET = '3129b9225476463d86ddc4074cfc8500'
SPOTIPY_REDIRECT_URI = 'https://shamp00the-cat.github.io/movierecs/callback'
SPOTIPY_REDIRECT_URI = 'https://shamp00the-cat.github.io/movierecs/displayhistory'

sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope=["user-top-read"])
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
    'pop': ['Adventure', 'Action'],
    'art pop': ['Romance', 'Fantasy'],
    'reggaeton': ['Adventure', 'Action'],
    'urbano latino': ['Adventure', 'Action'],
    'trap latino': ['Crime', 'Thriller'],
    'rock': ['Action', 'War'],
    'indie rock': ['Romance', 'Drama'],
    'classical': ['History', 'Romance'],
    'hip hop': ['Crime', 'Drama'],
    'jazz': ['Romance', 'Biography'],
    'country': ['Family', 'Romance'],
    'electronic': ['Sci-Fi', 'Mystery'],
    'metal': ['Horror', 'War'],
    'folk': ['History', 'Family'],
    'blues': ['Drama', 'Film-noir'],
    'r&b': ['Crime', 'Romance'],
    'soul': ['Drama', 'Family'],
    'punk': ['Thriller', 'Action'],
    'disco': ['Comedy', 'Romance'],
    'house': ['Mystery', 'Thriller'],
    'techno': ['Sci-Fi', 'Action'],
    'edm': ['Action', 'Sci-Fi'],
    'latin': ['Family', 'Romance'],
    'reggae': ['Adventure', 'Comedy'],
    'funk': ['Romance', 'Comedy'],
    'k-pop': ['Comedy', 'Romance'],
    'psychedelic': ['Animation', 'Mystery'],
    'world': ['Family', 'History'],
    'ambient': ['Animation', 'Sci-Fi'],
    'lo-fi beats': ['Drama', 'Animation'],
    'vaporwave': ['Sci-Fi', 'Mystery'],
    'emo': ['Romance', 'Drama'],
    'hardcore': ['Thriller', 'Action'],
    'dubstep': ['Action', 'Sci-Fi'],
    'ska': ['Comedy', 'Adventure'],
    'swing': ['History', 'Family'],
    'trance': ['Thriller', 'Fantasy'],
    'grime': ['Action', 'Drama'],
    'bluegrass': ['Drama', 'Family'],
    'new wave': ['Sci-Fi', 'Mystery'],
    'post-punk': ['Drama', 'Mystery'],
    'trip hop': ['Drama', 'Sci-Fi'],
    'neosoul': ['Romance', 'Family'],
    'afrobeat': ['Drama', 'Family'],
    'chillhop': ['Animation', 'Drama'],
    'synthwave': ['Drama', 'Action'],
    'latin viral pop': ['Adventure', 'Comedy'],
    'r&b en espanol': ['Music', 'Musical']
}

# Genre mapping for TV Shows
tvshow_genre_mapping = {
    'pop': ['Adventure', 'Action'],
    'art pop': ['Animation', 'Fantasy'],
    'reggaeton': ['Adventure', 'Action'],
    'urbano latino': ['Comedy', 'Documentary'],
    'trap latino': ['Crime', 'Thriller'],
    'rock': ['Adventure', 'Action'],
    'indie rock': ['Drama', 'Romance'],
    'classical': ['Biography', 'History'],
    'hip hop': ['Crime', 'Game-Show'],
    'jazz': ['Musical', 'Music'],
    'country': ['Family', 'Western'],
    'electronic': ['Mystery', 'Sci-Fi'],
    'metal': ['Horror', 'Action'],
    'folk': ['History', 'Family'],
    'blues': ['Biography', 'Drama'],
    'r&b': ['Romance', 'Talk-Show'],
    'soul': ['Family', 'Drama'],
    'punk': ['Thriller', 'Action'],
    'disco': ['Romance', 'Comedy'],
    'house': ['Sci-Fi', 'Reality-TV'],
    'techno': ['Sport', 'News'],
    'edm': ['Adventure', 'Short'],
    'latin': ['Family', 'Romance'],
    'reggae': ['Adventure', 'Comedy'],
    'funk': ['Romance', 'Comedy'],
    'k-pop': ['Comedy', 'Romance'],
    'psychedelic': ['Fantasy', 'Animation'],
    'world': ['Family', 'History'],
    'ambient': ['Sci-Fi', 'Mystery'],
    'lo-fi beats': ['Romance', 'Drama'],
    'vaporwave': ['Mystery', 'Sci-Fi'],
    'emo': ['Romance', 'Drama'],
    'hardcore': ['Thriller', 'Action'],
    'dubstep': ['Action', 'War'],
    'ska': ['Family', 'Comedy'],
    'swing': ['Romance', 'History'],
    'trance': ['Fantasy', 'Sci-Fi'],
    'grime': ['Crime', 'Action'],
    'bluegrass': ['History', 'Family'],
    'new wave': ['Sci-Fi', 'Drama'],
    'post-punk': ['Mystery', 'Drama'],
    'trip hop': ['Drama', 'Mystery'],
    'neosoul': ['Romance', 'Drama'],
    'afrobeat': ['Drama', 'History'],
    'chillhop': ['Animation', 'Drama'],
    'synthwave': ['Action', 'Sci-Fi'],
    'latin viral pop': ['Adventure', 'Comedy'],
    'r&b en espanol': ['Music', 'Musical']
}


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args['code']
    token = sp_oauth.get_access_token(code, as_dict=False)
    session['token'] = token
    return render_template('loginpage.html')

@app.route('/history')
def display_history():
    # Fetch user's top tracks from the past 30 days (short term)
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='short_term')
    # Extract artists from the top tracks
    artist_ids = [track['album']['artists'][0]['id'] for track in top_tracks['items']]
    # Fetch artist details for these artists
    artists = sp.artists(artist_ids)['artists']
    # Count frequency of each genre
    genre_count = {}
    for artist in artists:
        for genre in artist['genres']:
            if genre in genre_count:
              genre_count[genre] += 1
            else:
              genre_count[genre] = 1

    # Ensure that the genres from Spotify are in lowercase for the mapping.
    top_5_genres = [genre.lower() for genre in sorted(genre_count, key=genre_count.get, reverse=True)[:5]]
    print("Your top 5 most listened to genres over the past 30 days are: ("top_5_genres")")
    return render_template('displayhistory.html', history=recommendations_db.to_dict(orient='records'))

@app.route('/recommendation', methods=['POST'])
def recommendation():
    token = session.get('token')
    if not token:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token)
    
    choice = request.form.get('choice')
    matching_genres_weighted = []

    # Identify the appropriate genre mapping based on choice
    if choice == "movie":
        genre_mapping = movie_genre_mapping
    elif choice == "tvshow":
        genre_mapping = tvshow_genre_mapping
    else:
        print("Invalid choice!")
        return

    # Loop through each Spotify genre and weight the movie genres
    for spotify_genre in top_5_genres:
        # Check if the Spotify genre exists in the mapping
        if spotify_genre in genre_mapping:
            for corresponding_genre in genre_mapping[spotify_genre]:
                matching_genres_weighted.extend([corresponding_genre] * genre_count[spotify_genre])

    # Movie Filtering
    if choice == "movie":
        df = pd.read_csv('') # Change
        df = df[(df['rating'] >= 8) & (df['votes'] >= 20000)]
        # Filter movies using case-insensitive matching
        filtered_movies = df[df['genre'].str.lower().str.contains('|'.join([g.lower() for g in matching_genres_weighted]))]
        if filtered_movies.empty:
            print("No movies found matching the criteria.")
        else:
            recommended_genre = random.choice(matching_genres_weighted)
            filtered_genre_movies = filtered_movies[filtered_movies['genre'].str.lower().str.contains(recommended_genre.lower())]
            if not filtered_genre_movies.empty:
              recommended_movie = filtered_genre_movies.sample().iloc[0]
            else:
              print("No movies found for the genre:", recommended_genre)
              return
        print(f"Recommended Movie: {recommended_movie['movie_name']} (Genre: {recommended_movie['genre'].capitalize()}, Rating: {recommended_movie['rating']}, Release Year: {recommended_movie['year']})")
        save_recommendation(top_5_genres, 'Movie', recommended_movie['movie_name'], recommended_movie['genre'].capitalize(), recommended_movie['rating']) 

    # TV Show Filtering
    elif choice == "tvshow":
        df = pd.read_csv(' ', on_bad_lines='warn') # Change
        df_copy = df.copy()
        df_copy['votes'] = df_copy['votes'].astype(str)
        df_copy['votes'] = df_copy['votes'].str.replace(',', '').astype(float)
        df_copy.loc[df_copy['votes'].notna(), 'votes'] = df_copy['votes'].dropna().astype(int)
        df_copy['genre'] = df_copy['genre'].astype(str)

        # Filter TV shows using case-insensitive matching
        filtered_tvshows = df_copy[df_copy['genre'].str.split(', ').apply(lambda x: bool(set([y.lower() for y in x]) & set([g.lower() for g in matching_genres_weighted])) if x != 'nan' else False)]
        filtered_tvshows = filtered_tvshows[filtered_tvshows['rating'] >= 8]
        filtered_tvshows = filtered_tvshows[filtered_tvshows['votes'] >= 20000]
        if filtered_tvshows.empty:
            print("No TV shows found matching the criteria.")
        else:
            recommended_genre = random.choice(matching_genres_weighted)
            filtered_genre_tvshows = filtered_tvshows[filtered_tvshows['genre'].str.lower().str.contains(recommended_genre.lower())]
            if not filtered_genre_tvshows.empty:
              recommended_show = filtered_genre_tvshows.sample().iloc[0]
            else:
              print("No TV shows found for the genre:", recommended_genre)
              return
        earliest_year = str(recommended_show['year']).split('–')[0].strip().replace('-', '')
        print(f"Recommended TV Show: {recommended_show['title']} (Genre: {recommended_genre}, Rating: {recommended_show['rating']}, Release Year: {earliest_year.strip('()')})")
    return render_template('displayrecommendation.html', recommended_movie=recommended_movie, recommended_show=recommended_show)

new_recommendation = Recommendation(','.join(top_5_genres), 'Movie', recommended_movie['movie_name'], recommended_movie['genre'].capitalize(), recommended_movie['rating'])
new_recommendation = Recommendation(','.join(top_5_genres), 'TV Show', recommended_tvshow['title'], recommended_tvshow['genre'].capitalize(), recommended_tvshow['rating'])
db.session.add(new_recommendation)
db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=3000)
