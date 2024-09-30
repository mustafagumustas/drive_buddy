from spotipy.oauth2 import SpotifyClientCredentials
from langchain_core.tools import tool
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
import pandas as pd
import subprocess
import spotipy
import dotenv
import os

load_status = dotenv.load_dotenv("Neo4j-c95d3ee9-Created-2024-09-01.txt")
client_id = os.getenv("SPO_CLIENT_ID")
client_secret = os.getenv("SPO_CLIENT_SECRET")

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
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
@tool
def play_track_on_device(track_name: str):
    "start playing requested track"
    print(f"Tool triggered: Playing '{track_name}' on the active device.")

    # Step 1: Get the active device
    active_device_id = get_active_device()
    if not active_device_id:
        print("No active device found.")
        return {"message": "No active device found."}

    # Step 2: Find the track URI
    track_uri = find_track_uri(track_name)
    if not track_uri:
        print(f"Track '{track_name}' not found.")
        return {"message": f"Track '{track_name}' not found."}

    # Step 3: Start playback on the active device
    try:
        print(
            f"Attempting to start playback on device {active_device_id} for track URI {track_uri}"
        )
        sp.start_playback(device_id=active_device_id, uris=[track_uri])
        return {"message": f"Playing '{track_name}' on the active device."}
    except Exception as e:
        print(f"Error during playback: {e}")
        return {"message": f"Error during playback: {e}"}
