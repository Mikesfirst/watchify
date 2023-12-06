from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from io import BytesIO
import time
import os

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'
app.config['UPLOAD_FOLDER'] = 'static'


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


def generate_personalized_statement(valence, danceability, energy):
    # Define custom ranges with two decimal places
    valence_ranges = [(0.00, 0.20), (0.20, 0.40), (0.40, 0.60), (0.60, 0.80), (0.80, 1.00)]
    danceability_ranges = [(0.00, 0.20), (0.20, 0.40), (0.40, 0.60), (0.60, 0.80), (0.80, 1.00)]
    energy_ranges = [(0.00, 0.20), (0.20, 0.40), (0.40, 0.60), (0.60, 0.80), (0.80, 1.00)]

    # Initialize statements
    valence_statement = ""
    danceability_statement = ""
    energy_statement = ""

    # Check Valence
    for lower, upper in valence_ranges:
        if lower <= valence <= upper:
            if valence < 0.20:
                valence_statement = f"Your valence suggests you've been diving deep into the world of sad music. It's time for some virtual hugs!"
            elif valence < 0.40:
                valence_statement = f"Your valence shows a touch of melancholy. Maybe you're composing the soundtrack of a rainy day?"
            elif valence < 0.60:
                valence_statement = f"Your music falls in the 'not too happy, not too sad' range. A well-balanced playlist for life's adventures!"
            elif valence < 0.80:
                valence_statement = f"Your valence indicates a cheerful and positive music taste. Keep rocking those good vibes!"
            else:
                valence_statement = f"Wow, your valence is off the charts! You must be the life of the party with such happy music!"

    # Check Danceability
    for lower, upper in danceability_ranges:
        if lower <= danceability <= upper:
            if danceability < 0.20:
                danceability_statement = f"Your music is not too dance-friendly. Perhaps it's time to join a dance class online?"
            elif danceability < 0.40:
                danceability_statement = f"Your music is moderately danceable. Time to practice your dance moves!"
            elif danceability < 0.60:
                danceability_statement = f"Your music taste is groovy and dance-friendly. Get ready to dance like nobody's watching!"
            elif danceability < 0.80:
                danceability_statement = f"Your music is super danceable! You're a dance floor legend in the making!"
            else:
                danceability_statement = f"Your music is dance-tastic! You're the life of every dance party!"

    # Check Energy
    for lower, upper in energy_ranges:
        if lower <= energy <= upper:
            if energy < 0.20:
                energy_statement = f"Your music is super calm and passive. Are you in relaxation mode or just taking it easy?"
            elif energy < 0.40:
                energy_statement = f"Your music falls within the range of tranquility. Perfect for peaceful moments!"
            elif energy < 0.60:
                energy_statement = f"Your music is moderately energetic. You're keeping it balanced!"
            elif energy < 0.80:
                energy_statement = f"Your music has a good amount of energy. Ready to tackle the day with enthusiasm!"
            else:
                energy_statement = f"Your music is high-energy and intense! It's like a musical energy drink!"

    # Combine the statements
    personalized_statement = valence_statement + "\n" + danceability_statement + "\n" + energy_statement

    return personalized_statement


# DB Configuration
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@YOUR_RDS_ENDPOINT:5432/watchify' # change
db = SQLAlchemy()
#class Recommendation(db.Model):
   # id = db.Column(db.Integer, primary_key=True)
   # spotify_genres = db.Column(db.String)
   # recommendation_type = db.Column(db.String)
   # title = db.Column(db.String)
   # genre = db.Column(db.String)
   # rating = db.Column(db.Float)
    
    #def __init__(self, spotify_genres, recommendation_type, title, genre, rating):
     #   self.spotify_genres = spotify_genres
      #  self.recommendation_type = recommendation_type
       # self.title = title
        #self.genre = genre
       # self.rating = rating

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
     "Biography": {
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
        return "Error: No code provided.", 400

    try:
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        session['token'] = token_info['access_token']
        return redirect(url_for('display_history'))
    
    except Exception as e:
        print(f"Error retrieving access token: {e}")
        return "Error in token retrieval.", 500

@app.route('/history')
def display_history():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    sp = spotipy.Spotify(auth=session['token'])
    
    # This function or variable definition should be before its usage.
    top_5_genres = sorted(genre_count, key=genre_count.get, reverse=True)[:5]

    genre_features = {genre: {"valence": 0, "danceability": 0, "energy": 0, "count": 0} for genre in top_5_genres}

    try:
        current_user = sp.current_user()
        username = current_user['display_name']
        top_tracks = sp.current_user_top_tracks(limit=30, time_range='short_term')['items']

        # Initialize user_metrics
        user_metrics = {"valence": 0, "danceability": 0, "energy": 0}
        count = 0

        # Loop through the tracks and calculate user_metrics
        for track in top_tracks:
            song_id = track['id']
            song_metrics = sp.audio_features(song_id)[0]
        if song_metrics:
            artist_ids = [artist['id'] for artist in track['album']['artists']]
            artists = sp.artists(artist_ids)['artists']
        for artist in artists:
            for genre in artist['genres']:
                genre_lower = genre.lower()
                if genre_lower in genre_features:
                    genre_features[genre_lower]["valence"] += song_metrics['valence']
                    genre_features[genre_lower]["danceability"] += song_metrics['danceability']
                    genre_features[genre_lower]["energy"] += song_metrics['energy']
                    genre_features[genre_lower]["tempo"] += song_metrics['tempo']
                    genre_features[genre_lower]["count"] += 1

        # Calculate the average of each audio feature for each genre
        # Prepare the data for plotting
        data = {'Genre': [], 'Valence': [], 'Danceability': [], 'Energy': [], 'Count': []}
        for genre, metrics in genre_features.items():
            data['Genre'].append(genre.capitalize())
            data['Valence'].append(metrics['valence'])
            data['Danceability'].append(metrics['danceability'])
            data['Energy'].append(metrics['energy'])
            data['Count'].append(metrics['count'])
    
        df = pd.DataFrame(data)
    
        # Melting the DataFrame for better visualization
        melted_df = df.melt(id_vars=['Genre', 'Count'], value_vars=['Valence', 'Danceability', 'Energy'],
                        var_name='Feature', value_name='Average')
    
        # Plotting the graph
        plt.figure(figsize=(16, 9))
        sns.barplot(x='Genre', y='Average', hue='Feature', data=melted_df, palette=['#1db954', '#191414', '#ababab'])
    
        # Customize the plot
        plt.title('Spotify Top 5 Genres and Audio Features (Last 30 Days)', fontsize=16)
        plt.ylabel('Average Feature Value', fontsize=12)
        plt.xlabel('Genre', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(title='Feature')
    
        # Save the plot as a PNG file in a BytesIO object
        img = BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)  # Rewind the file
        plt.clf()  # Clear the figure to free memory
    
        # Save the plot to the 'static' directory
        img_path = os.path.join('static', 'user_plot.png')
        with open(img_path, 'wb') as f:
            f.write(img.getvalue())
    
        # Pass the image path to the template for display
        return render_template('displayhistory.html', img_path=img_path, username=current_user['display_name'], personalized_statement=generate_personalized_statement)

    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API Error: {e}")
        return "Error fetching data from Spotify.", 500

@app.route('/download_plot')
def download_plot():
    # Provide a route to download the plot
    img_path = os.path.join('static', 'user_plot.png')
    return send_from_directory(directory='static', path='user_plot.png', as_attachment=True, download_name='YourSpotifyJourney.png')


@app.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    token = session.get('token')
    if not token:
        return redirect(url_for('login'))

    # Initialize the Spotify client with the access token from the session
    sp = spotipy.Spotify(auth=token)

    if request.method == 'POST':
        choice = request.form.get('choice')
        print("User's choice:", choice) 

        # Getting the average metrics for the user
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
            user_metrics = {key: val / count for key, val in user_metrics.items()}

        # Now find which genre is closest to the user's metrics
        genre_td = {genre: {} for genre in genre_mapping}
        best_genre = None
        best_diff = float('inf')
        for genre, genre_metrics in genre_mapping.items():
            valence_diff = abs(user_metrics["valence"] - genre_metrics["valence"])
            danceability_diff = abs(user_metrics["danceability"] - genre_metrics["danceability"])
            energy_diff = abs(user_metrics["energy"] - genre_metrics["energy"])
            
            total_diff = valence_diff + danceability_diff + energy_diff
            genre_td[genre] = total_diff

            if total_diff < best_diff:
                best_genre = genre
                best_diff = total_diff

        Genre_choice = [best_genre]
        
        # For debugging
        print("Genre distances:", genre_td)
        print("Best genre match:", best_genre)

        # Read the CSV file containing entertainment data
        df = pd.read_csv('entertainment.csv')

        if choice == "movie":
            df_filtered = df[(df['media'] == "movie") & df['genres'].str.contains(best_genre, case=False, na=False)]
            recommended_movie = df_filtered.sample(n=1).iloc[0] if not df_filtered.empty else None
            return render_template('displayrecommendation.html', recommended=recommended_movie, choice=choice)
        elif choice == "tvshow":
            df_filtered = df[(df['media'] == "tv") & df['genres'].str.contains(best_genre, case=False, na=False)]
            recommended_show = df_filtered.sample(n=1).iloc[0] if not df_filtered.empty else None
            return render_template('displayrecommendation.html', recommended=recommended_show, choice=choice)

    # Render the form page to get the user's choice if method is GET or no choice was made
    return render_template('displayrecommendation.html', choice=choice)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
