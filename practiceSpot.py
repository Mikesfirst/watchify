import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser


# Replace with your own Spotify API credentials
client_id = '6f8bacd4931e41839442e43813d4fcfb'
client_secret = 'bd500cdc7b674c3087c2eadbdb0ec058'
redirect_uri = 'http://localhost:8888/callback'

# Initialize Spotipy with user authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri='YOUR_REDIRECT_URI', scope='user-top-read'))

# Set the time range for the last 30 days
time_range = 'short_term'

# Number of tracks to fetch
limit = 10

# Get the user's top tracks from the last 30 days
top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=limit)

# Print the top tracks
for idx, track in enumerate(top_tracks['items'], start=1):
    print(f"{idx}. {track['name']} by {', '.join(artist['name'] for artist in track['artists'])}")
