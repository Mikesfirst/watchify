# import spotipy
# from spotipy.oauth2 import SpotifyOAuth
# import requests

# client_id = '6f8bacd4931e41839442e43813d4fcfb'
# client_secret = 'bd500cdc7b674c3087c2eadbdb0ec058'

# auth_url = url: 'https://accounts.spotify.com/api/token',


# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri='http://localhost:8888/', scope='user-top-read'))

# time_range = 'short_term'

# limit = 10

# top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=limit)
# top_artists = sp.current_user_top_artists(time_range='short_term', limit=50)
# #--------------------------------------------------------------------------
# #                              Top genre 
# genre_count = {}
# for artist in top_artists['items']:
#     for genre in artist['genres']:
#         genre_count[genre] = genre_count.get(genre, 0) + 1

# most_listened_genre = max(genre_count.keys(), key=lambda genre: genre_count[genre])

# print(f"The most listened genre over the past 30 days is: {most_listened_genre}")


# #--------------------------------------------------------------------------
# #                        Dictionary wth scores using Spotify metrics
# audio_features = {
#     'danceability': 0,
#     'energy': 0,
#     'key': 0,
#     'loudness': 0,
#     'mode': 0,
#     'speechiness': 0,
#     'acousticness': 0,
#     'instrumentalness': 0,
#     'liveness': 0,
#     'valence': 0,
#     'tempo': 0,}

# for song in top_tracks['items']:
#     track_id = song['id']
#     features = sp.audio_features(track_id)[0]
#     for metric in features:
#         if metric in audio_features:
#             audio_features[metric] = audio_features[metric] + features[metric]
            
# print(audio_features)
