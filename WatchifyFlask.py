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
SPOTIPY_CLIENT_SECRET = '6fe22f2ca5864f6b88a9477de0df7a6f'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'

#Michael's ID just to run locally
# SPOTIPY_CLIENT_ID = "6f8bacd4931e41839442e43813d4fcfb"
# SPOTIPY_CLIENT_SECRET = "bd500cdc7b674c3087c2eadbdb0ec058" 
# SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'

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

#Genre Mapping
genre_mapping = {
    "Romance": {
        'valence': 0.378617,
        'danceability': 0.52972,
        'energy': 0.45700999999999986,
    },
    "Action": {
        'valence': 0.4782686868686866,
        'danceability': 0.610616161616162,
        'energy': 0.7276262626262627,
    },
    "Comedy": {
        'valence': 0.6791019999999999,
        'danceability': 0.6025000000000003,
        'energy': 0.754392,
    },
    "Science Fiction": {
        'valence': 0.318779,
        'danceability': 0.42281799999999997,
        'energy': 0.426963,
    },
    "Horror": {
        'valence': 0.043389655172413784,
        'danceability': 0.2253931034482759,
        'energy': 0.20297327586206892,
    },
    "Family": {
        'valence': 0.39481,
        'danceability': 0.5041180000000001,
        'energy': 0.4358320000000002,
    },
    "Drama": {
        'valence': 0.27197200000000005,
        'danceability': 0.4922300000000001,
        'energy': 0.4408099999999998,
    },
    "Adventure": {
        'valence': 0.4435835164835165,
        'danceability': 0.5584285714285715,
        'energy': 0.6459472527472528,
    },
     "Thriller": {
        'valence': 0.3606849999999999,
        'danceability': 0.5131299999999999,
        'energy': 0.5883509999999998,

        },
     "Unknown": {
        'valence': 0.5983500000000002,
        'danceability': 0.60787,
        'energy': 0.7006800000000003,
        },
     "Crime": {
        'valence': 0.5080319999999997,
        'danceability': 0.64384,
        'energy': 0.6495099999999999,
        },
     "Fantasy": {
        'valence': 0.307479,
        'danceability': 0.45702000000000015,
        'energy': 0.4734160000000001,
        }
    }

#Function to pick movie with all genres
def same_genres(genre_choices, genre_csv):
    for x in range(len(genre_csv)):
        for y in genre_choices:
            if y not in genre_csv[x]:
                return False
    return True

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
    code = request.args.get('code')
    if not code:
        # Handle the case where the code is missing
        return "Error: No code provided.", 400

    try:
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        session['token'] = token_info['access_token']
    except Exception as e:
        # Log the exception for debugging
        print(f"Error retrieving access token: {e}")
        return "Error in token retrieval.", 500

    # Initialize the Spotipy client with the access token
    global sp
    sp = spotipy.Spotify(auth=session['token'])
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

    #User picks which media they want and we find the reccomended movie
    if request.method == 'POST':

        choice = request.form.get('choice')
        print("choice", choice) 
        #Getting the avergage metrics for the user
        user_metrics = {"valence": 0, "danceability": 0, "energy": 0, "tempo": 0}
        count = 0
        tracks = sp.current_user_top_tracks(time_range='short_term', limit=30)['items']
        for track in tracks:
            song_id = track['id']
            song_metrics = sp.audio_features(song_id)[0]
            if song_metrics is not None:
                user_metrics["valence"] += song_metrics['valence']
                user_metrics["danceability"] += song_metrics['danceability']
                user_metrics["energy"] += song_metrics['energy']
                count += 1
        if count > 0:
            user_metrics["valence"] = user_metrics["valence"] / count
            user_metrics["danceability"] = user_metrics["danceability"] / count
            user_metrics["energy"] = user_metrics["energy"] / count

    #Now finds which genre is closest to the users metrics 
        genre_td = {
    "Romance": {},
    "Action": {},
    "Comedy": {},
    "Science Fiction": {},
    "Horror": {},
    "Family": {},
    "Drama": {},
    "Adventure": {},
    "Thriller": {},
    "Unknown": {},
    "Crime": {},
    "Fantasy": {}
}

        Genre_choice = []
        best_genre = None
        best_diff = float('inf')
        for genre, genre_metrics in genre_mapping.items():
            valence_diff = abs(user_metrics["valence"] - genre_metrics["valence"])
            danceability_diff = abs(user_metrics["danceability"] - genre_metrics["danceability"])
            energy_diff = abs(user_metrics["energy"] - genre_metrics["energy"])
            
            total_diff = valence_diff + danceability_diff + energy_diff
            genre_td[genre] = total_diff

            if total_diff <= best_diff:
                print("total_diff: ", total_diff)
                best_genre = genre
                best_diff = total_diff    
                
        if best_genre not in Genre_choice:
            Genre_choice.append(best_genre)

        print(genre_td)
        for genre in genre_td:
            if abs(genre_td[genre] - best_diff) <= 0.09:
                if genre not in Genre_choice:
                    Genre_choice.append(genre)
                            
        print("Final Genre Choice:", Genre_choice)
        df = pd.read_csv('entertainment.csv')
        df_filtered = ""
        if choice == "movie":
            if len(Genre_choice) > 1:
                df_filtered = df[df['genres'].notna() & (df['media'] == "movie")]
                for gen in Genre_choice:
                    df_filtered = df_filtered[(df_filtered['genres'].str.contains(gen))]
            if len(df_filtered) == 0 or len(Genre_choice) == 1:
                df_filtered = df[df['genres'].notna() & (df['media'] == "movie") & df['genres'].str.contains(Genre_choice[0])]
            recommended_movie = df_filtered.sample().iloc[0]
            return render_template('displayrecommendation.html', recommended_movie=recommended_movie, choice=choice, genre_choice=Genre_choice[0])
        elif choice == "tvshow":
            if len(Genre_choice) > 1:
                df_filtered = df[df['genres'].notna() & (df['media'] == "tv")]
                for gen in Genre_choice:
                    df_filtered = df_filtered[(df_filtered['genres'].str.contains(gen))]
            if len(df_filtered) == 0 or len(Genre_choice) == 1:
                df_filtered = df[df['genres'].notna() & (df['media'] == "tv") & df['genres'].str.contains(Genre_choice[0])]
            recommended_show = df_filtered.sample().iloc[0]
            return render_template('displayrecommendation.html', recommended_show=recommended_show, choice=choice)
    
    return render_template('displayrecommendation.html', choice=choice)
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