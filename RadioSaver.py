#!/usr/bin/env python3

from config import *
import spotipy
import spotipy.util as util
from spotipy.client import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
import json
import time
import sys

from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from collections import deque
from os.path import exists
from tenacity import *

HISTORY_FILE = 'history.json'

class RadioSaver:
    # Store the last ten tracks for each station, to prevent adding the same track over and over
    all_added_tracks = {}
    if exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as file:
            all_added_tracks = json.load(file)
            for station in stations: # Transfer the JSON data to deques
                station_id = station["station_id"]
                all_added_tracks[station_id] = deque(all_added_tracks[str(station_id)], maxlen=10)
    else:
        for station in stations:
            all_added_tracks[station["station_id"]] = deque(maxlen=10)

    def init_spotify(self):
        self.redirect_uri = 'http://localhost:8888/callback/'
        self.scope = 'playlist-modify-public'
        client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID,
                                                              client_secret=CLIENT_SECRET)
        token = util.prompt_for_user_token(USERNAME, self.scope, client_id=CLIENT_ID,
                                           client_secret=CLIENT_SECRET, redirect_uri=self.redirect_uri)
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=token)

    def process_music(self):
        all_added_tracks_array = {}

        for station in stations:
            self.save_for_station(station)

            # Save the history in case the server is restarted
            # Has to be transformed to a normal array since deque isn't JSON serializable
            station_id = station["station_id"]
            all_added_tracks_array[station_id] = list(self.all_added_tracks[station_id])

        with open(HISTORY_FILE, 'w') as file:
            json.dump(all_added_tracks_array, file)


    def save_for_station(self, station):
        # Station specific variables
        station_name = station["station_name"]
        print("Will sync for station: {}\n".format(station_name))

        station_id = station["station_id"]
        playlist_id = station["playlist_id"]
        limit = station["limit"]
        processed_tracks = self.all_added_tracks[station_id]

        # Fetch recently played tracks
        url = 'https://api.radio.net/info/v2/search/nowplaying'
        post_fields = {'apikey': 'df5cadfe49eeaff53727bad8c69b47bdf4519123',
                       'numberoftitles': 10,
                       'station': station_id}

        request = Request(url, urlencode(post_fields).encode())
        resp = urlopen(request).read().decode()
        tracks = json.loads(resp)

        tracks_to_add = []
        for track in reversed(tracks):
            track_name = track["streamTitle"];
            # Some radio stations, such as Antenne Bayern Classic Rock, have their ads as the track name
            if track_name and station_name != track_name:
                if track_name not in processed_tracks:
                    tracks_to_add.append(track_name)

        # Get Spotify track URIs
        track_uris = []
        for track in tracks_to_add:
            print("Will search for track: ", track)
            res = self.search_spotify_track(track)
            tracks = res["tracks"]

            processed_tracks.append(track)
            if len(tracks["items"]) < 1:
                print("No tracks found\n")
                continue

            item = tracks["items"][0]
            print("Will add track: {} ({})\n".format(item["name"], item["uri"]))

            track_uris.append(item["uri"])

        if track_uris:
            # Add tracks to playlist
            self.add_tracks_to_playlist(playlist_id, track_uris)

            # Remove any tracks overflowing the total 400 count
            tracks = self.get_playlist_tracks(playlist_id)
            tracks_to_remove = []
            if len(tracks) > limit:
                for i in range(len(tracks) - limit):
                    # Add the track_uris for the tracks to be removed, along with their positions
                    tr = {"uri": tracks[i]["track"]["uri"],
                          "positions": [i]}
                    tracks_to_remove.append(tr)

                self.remove_tracks_from_playlist(playlist_id, tracks_to_remove)

    @retry(stop=stop_after_attempt(5))
    def fetch_station_recently_played(self, station_id):
        # Fetch recently played tracks
        url = 'https://api.radio.net/info/v2/search/nowplaying'
        post_fields = {'apikey': 'df5cadfe49eeaff53727bad8c69b47bdf4519123',
                       'numberoftitles': 10,
                       'station': station_id}

        request = Request(url, urlencode(post_fields).encode())
        resp = urlopen(request).read().decode()
        return json.loads(resp)

    # Methods that once fail, will refresh the Spotify token and retry the action
    @retry(reraise=True, stop=stop_after_delay(5))
    def search_spotify_track(self, track):
        try:
            return self.spotify.search(q=track, type='track', limit=5)
        except SpotifyException:
            self.refresh_token()
            pass

    @retry(reraise=True, stop=stop_after_delay(5))
    def add_tracks_to_playlist(self, playlist_id, track_uris):
        try:
            self.spotify.user_playlist_add_tracks(USERNAME, playlist_id, track_uris)
        except SpotifyException:
            self.refresh_token()
            pass

    @retry(reraise=True, stop=stop_after_delay(5))
    def remove_tracks_from_playlist(self, playlist_id, track_uris):
        try:
            self.spotify.user_playlist_remove_specific_occurrences_of_tracks(USERNAME, playlist_id, track_uris)
        except SpotifyException:
            self.refresh_token()
            pass


    # Help method to retrieve all tracks of a playlist, as the API only gives 100 at a time
    def get_playlist_tracks(self, playlist_id):
        results = self.spotify.user_playlist_tracks(USERNAME, playlist_id)
        tracks = results['items']
        while results['next']:
            results = self.spotify.next(results)
            tracks.extend(results['items'])
        return tracks

    # Method to refresh Spotify token
    def refresh_token(self):
        token = util.prompt_for_user_token(USERNAME, self.scope, client_id=CLIENT_ID,
                                           client_secret=CLIENT_SECRET, redirect_uri=self.redirect_uri)
        self.spotify = spotipy.Spotify(auth=token)

## Main
saver = RadioSaver()
saver.init_spotify()

while True:
    saver.process_music()
    time.sleep(180)
