from flask import Flask, render_template, request, redirect, url_for, session
from os import environ
#from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import random

# Load environment variables from .env file
#load_dotenv('.env')

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

top_5_genres = ''
genre_count = {}
recommended_tvshow = []
recommended_movie = []

# Spotify API Credentials
# SPOTIPY_CLIENT_ID = 'ecec60c9a316409a84a45c923f7473ee'
# SPOTIPY_CLIENT_SECRET = '3129b9225476463d86ddc4074cfc8500'
# SPOTIPY_REDIRECT_URI = 'https://shamp00the-cat.github.io/movierecs/callback'

#Michael's ID just to run locally
SPOTIPY_CLIENT_ID = "6f8bacd4931e41839442e43813d4fcfb"
SPOTIPY_CLIENT_SECRET = "bd500cdc7b674c3087c2eadbdb0ec058" 
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'

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
    'pop': ['Comedy', 'Romance'],
    'art pop': ['Fantasy', 'Drama'],
    'reggaeton': ['Action', 'Adventure'],
    'urbano latino': ['Action', 'Drama'],
    'trap latino': ['Crime', 'Action'],
    'rock': ['Action', 'Adventure'],
    'indie rock': ['Drama', 'Romance'],
    'classical': ['History', 'Biography'],
    'hip hop': ['Drama', 'Crime'],
    'jazz': ['Drama', 'Biography'],
    'country': ['Drama', 'Family'],
    'electronic': ['Sci-Fi', 'Mystery'],
    'metal': ['Horror', 'Thriller'],
    'folk': ['Drama', 'History'],
    'blues': ['Drama', 'Crime'],
    'r&b': ['Romance', 'Drama'],
    'soul': ['Drama', 'Romance'],
    'punk': ['Action', 'Thriller'],
    'disco': ['Comedy', 'Romance'],
    'house': ['Sci-Fi', 'Thriller'],
    'techno': ['Sci-Fi', 'Action'],
    'edm': ['Action', 'Sci-Fi'],
    'latin': ['Drama', 'Romance'],
    'reggae': ['Comedy', 'Adventure'],
    'funk': ['Comedy', 'Action'],
    'k-pop': ['Comedy', 'Romance'],
    'psychedelic': ['Fantasy', 'Adventure'],
    'world': ['History', 'Family'],
    'ambient': ['Drama', 'Sci-Fi'],
    'lo-fi beats': ['Drama', 'Romance'],
    'vaporwave': ['Sci-Fi', 'Fantasy'],
    'emo': ['Drama', 'Romance'],
    'hardcore': ['Action', 'Thriller'],
    'dubstep': ['Action', 'Sci-Fi'],
    'ska': ['Comedy', 'Adventure'],
    'swing': ['Comedy', 'Romance'],
    'trance': ['Sci-Fi', 'Adventure'],
    'grime': ['Crime', 'Action'],
    'bluegrass': ['Drama', 'Adventure'],
    'new wave': ['Sci-Fi', 'Romance'],
    'post-punk': ['Drama', 'Thriller'],
    'trip hop': ['Mystery', 'Drama'],
    'neosoul': ['Romance', 'Drama'],
    'afrobeat': ['Drama', 'Adventure'],
    'chillhop': ['Drama', 'Romance'],
    'synthwave': ['Sci-Fi', 'Action'],
    'latin viral pop': ['Comedy', 'Adventure'],
    'r&b en espanol': ['Romance', 'Drama']
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
    top_5_genres = [genre.lower() for genre in sorted(genre_count, key=genre_count.get, reverse=True)[:5]]
    return render_template('displayhistory.html', top_5_genres=top_5_genres)

@app.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    print("Request Method:", request.method)
    choice = ""
    token = session.get('token')
    if not token:
        return redirect(url_for('login'))

    #sp = spotipy.Spotify(auth=token)
    if request.method == 'POST':
        choice = request.form.get('choice')
        matching_genres_weighted = []

        # Identify the appropriate genre mapping based on choice
        if choice == "movie":
            genre_mapping = movie_genre_mapping
        elif choice == "tvshow":
            genre_mapping = tvshow_genre_mapping

        # Loop through each Spotify genre and weight the movie genres
        selection_of_genres = []
        for spotify_genre in top_5_genres:
            # Check if the Spotify genre exists in the mapping
            if spotify_genre in genre_mapping:
                for corresponding_genre in genre_mapping[spotify_genre]:
                    selection_of_genres.append(corresponding_genre)
        if len(selection_of_genres) > 0:
            genre_choice = random.choice(selection_of_genres)
        else:
            genre_choice = random.choice(list(genre_mapping.values()))
        
        # Movie Filtering
        # if choice == "movie":
        #     df = pd.read_csv('') # Change
        #     df = df[(df['rating'] >= 8) & (df['votes'] >= 20000)]
        #     # Filter movies using case-insensitive matching
        #     filtered_movies = df[df['genre'].str.lower().str.contains('|'.join([g.lower() for g in matching_genres_weighted]))]
        #     if filtered_movies.empty:
        #         print("No movies found matching the criteria.")
        #     else:
        #         recommended_genre = random.choice(matching_genres_weighted)
        #         filtered_genre_movies = filtered_movies[filtered_movies['genre'].str.lower().str.contains(recommended_genre.lower())]
        #         if not filtered_genre_movies.empty:
        #             recommended_movie = filtered_genre_movies.sample().iloc[0]
        #         else:
        #             print("No movies found for the genre:", recommended_genre)
        #         return
        #     print(f"Recommended Movie: {recommended_movie} (Genre: {recommended_movie}, Rating: {recommended_movie}")
        #     # leaving this here for now just cleaning up the code//save_recommendation(top_5_genres, 'Movie', recommended_movie['movie_name'], recommended_movie['genre'].capitalize(), recommended_movie['rating']) 

        # # TV Show Filtering
        # elif choice == "tvshow":
        #     df = pd.read_csv(' ', on_bad_lines='warn') # Change
        #     df_copy = df.copy()
        #     df_copy['votes'] = df_copy['votes'].astype(str)
        #     df_copy['votes'] = df_copy['votes'].str.replace(',', '').astype(float)
        #     df_copy.loc[df_copy['votes'].notna(), 'votes'] = df_copy['votes'].dropna().astype(int)
        #     df_copy['genre'] = df_copy['genre'].astype(str)

        #     # Filter TV shows using case-insensitive matching
        #     filtered_tvshows = df_copy[df_copy['genre'].str.split(', ').apply(lambda x: bool(set([y.lower() for y in x]) & set([g.lower() for g in matching_genres_weighted])) if x != 'nan' else False)]
        #     filtered_tvshows = filtered_tvshows[filtered_tvshows['rating'] >= 8]
        #     filtered_tvshows = filtered_tvshows[filtered_tvshows['votes'] >= 20000]
        #     if filtered_tvshows.empty:
        #         print("No TV shows found matching the criteria.")
        #     else:
        #         recommended_genre = random.choice(matching_genres_weighted)
        #         filtered_genre_tvshows = filtered_tvshows[filtered_tvshows['genre'].str.lower().str.contains(recommended_genre.lower())]
        #         if not filtered_genre_tvshows.empty:
        #             recommended_show = filtered_genre_tvshows.sample().iloc[0]
        #         else:
        #             print("No TV shows found for the genre:", recommended_genre)
        #         return
        #     earliest_year = str(recommended_show['year']).split('–')[0].strip().replace('-', '')
        #     print(f"Recommended TV Show: {recommended_show['title']} (Genre: {recommended_genre}, Rating: {recommended_show['rating']}, Release Year: {earliest_year.strip('()')})")
        recommended_movie = "Star Wars"
        recommended_show = "How I Met Your Mother"
        return render_template('displayrecommendation.html', recommended_movie=recommended_movie, recommended_show=recommended_show)
    else:
        return render_template('displayrecommendation.html', choice=choice)


# new_recommendation = Recommendation(','.join(top_5_genres), 'Movie', recommended_movie)
# new_recommendation = Recommendation(','.join(top_5_genres), 'TV Show', recommended_tvshow)
# db.session.add(new_recommendation)
# db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
