from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
import pandas as pd
import subprocess
import spotipy

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id="d8a209feaa394905a8e10a4bcb7f0071",
        client_secret="a5291a7db33e4e4ba0610f7f3bcdb7db",
        redirect_uri="http://localhost:8888/callback",
        scope="user-read-playback-state,user-modify-playback-state, playlist-read-private",
    )
)


# Fetch active device
def get_active_device():
    devices = sp.devices()
    for device in devices["devices"]:
        if device["is_active"]:

            return device["id"]
    return None


# Find the track's URI on Spotify
def find_track_uri(track_name):
    results = sp.search(q=track_name, type="track", limit=1)
    if results["tracks"]["items"]:
        return results["tracks"]["items"][0]["uri"]
    else:
        return None


# me = sp.me()
# print(me["id"])


# Play a track on the active device
def play_track_on_device(track_name):
    active_device_id = get_active_device()
    if not active_device_id:
        print("No active device found.")
        return

    track_uri = find_track_uri(track_name)
    if not track_uri:
        print(f"Track '{track_name}' not found.")
        return

    # Start playing the track
    sp.start_playback(device_id=active_device_id, uris=[track_uri])
    print(f"Playing '{track_name}' on the active device.")


# # Find the latest used device
# for device in devices["devices"]:
#     if device["is_active"]:
#         active_device_id = device["id"]
#         break


# def list_playlist_tracks(playlist_name):
#     # Get the user's playlists
#     playlists = sp.current_user_playlists()
#     for playlist in playlists["items"]:
#         if playlist["name"] == playlist_name:
#             # Get the tracks in the playlist
#             tracks = sp.playlist_tracks(playlist["id"], limit=100)
#             while tracks:
#                 for id, track in enumerate(tracks["items"]):
#                     print(id, track["track"]["name"])
#                 if tracks["next"]:
#                     tracks = sp.next(tracks)
#                 else:
#                     tracks = None


# def get_followed_playlists():
#     # Initialize Spotify API client
#     # Get the current user's *only* followed playlists
#     playlists = sp.current_user_playlists()

#     print("Followed playlists not created by the user:")

#     for playlist in playlists["items"]:
#         # Check if the playlist owner is not the current user
#         if playlist["owner"]["id"] != sp.me()["id"]:
#             print(
#                 f"Playlist: {playlist['name']} by {playlist['owner']['display_name']}"
#             )


# def get_playlist_uri(playlist_name):
#     # Get the user's playlists
#     playlists = sp.current_user_playlists()
#     for playlist in playlists["items"]:
#         if playlist["name"] == playlist_name:
#             return playlist["uri"]
#     return None


# def get_all_music():
#     music_track = []
#     music_artist = []
#     music_album = []
#     music_uri = []
#     playlists = sp.current_user_playlists()

#     for playlist in playlists["items"]:
#         tracks = sp.playlist_tracks(playlist["id"])
#         while tracks:
#             for track_item in tracks["items"]:
#                 track = track_item.get("track")  # Get the 'track' key safely
#                 if track:  # Check if 'track' is not None
#                     try:
#                         music_track.append(track["name"].lower())
#                         music_artist.append(track["artists"][0]["name"].lower())
#                         music_album.append(track["album"]["name"].lower())
#                         music_uri.append(track["uri"])
#                     except (KeyError, IndexError) as e:
#                         print(f"Error processing track: {e}")
#                         print(track)
#                 else:
#                     print("Track is None, skipping this entry")

#             if tracks["next"]:
#                 tracks = sp.next(tracks)
#             else:
#                 tracks = None

#     music_dct = {
#         "name": music_track,
#         "artist": music_artist,
#         "album": music_album,
#         "uri": music_uri,
#     }
#     music_list_df = pd.DataFrame(music_dct)
#     return music_list_df


# def play_spotify_track(track_uri):
#     # AppleScript command to play a specific track on Spotify
#     apple_script = f"""
#     tell application "Spotify"
#         activate
#         play track "{track_uri}"
#     end tell
#     """
#     # Run the AppleScript command
#     subprocess.run(["osascript", "-e", apple_script])


# def play_song_on_spotify(song_name, artist_name=None):
#     # Search for the track
#     print("function called")
#     query = song_name
#     if artist_name:
#         query += f" {artist_name}"

#     results = sp.search(q=query, type="track", limit=1)

#     if len(results["tracks"]["items"]) == 0:
#         return "Song not found"

#     # Extract song information
#     song_uri = results["tracks"]["items"][0]["uri"]

#     # Fetch current active device
#     devices = sp.devices()
#     active_device_id = None
#     for device in devices["devices"]:
#         if device["is_active"]:
#             active_device_id = device["id"]
#             break

#     if active_device_id:
#         sp.start_playback(device_id=active_device_id, uris=[song_uri])
#         return f"Playing {song_name} by {artist_name or 'Unknown'} on Spotify."
#     else:
#         return "No active Spotify device found."
