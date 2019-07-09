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
import difflib

import logging
from logging.handlers import RotatingFileHandler

from bs4 import BeautifulSoup

HISTORY_FILE = 'history.json'

class RadioSaver:
    # Store the last ten tracks for each station, to prevent adding the same track over and over
    all_added_tracks = {}
    all_added_tracks_array = {}

    if exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as file:
            all_added_tracks_temp = json.load(file)
            for station_id, station in stations.items(): # Convert the JSON data to deques
                if (str(station_id) not in all_added_tracks_temp):
                    all_added_tracks[station_id] = deque(maxlen=10)
                    continue

                all_added_tracks[station_id] = deque(all_added_tracks_temp[str(station_id)], maxlen=10)
    else:
        for station_id in stations.keys():
            all_added_tracks[station_id] = deque(maxlen=10)

    def __init__(self):
        self.init_logging()
        self.fetch_radio_api_key()
        self.init_spotify()

    def init_logging(self):
        log_level = logging.DEBUG
        log_filename = 'log.txt'
        self.logger = logging.getLogger('root')
        self.logger.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

        file_handler = RotatingFileHandler(log_filename, mode='a', maxBytes=50 * 1024, backupCount=2, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler) 

    def init_spotify(self):
        self.redirect_uri = 'http://localhost:8888/callback/'
        self.scope = 'playlist-modify-public'
        client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID,
                                                              client_secret=CLIENT_SECRET)
        token = util.prompt_for_user_token(USERNAME, self.scope, client_id=CLIENT_ID,
                                           client_secret=CLIENT_SECRET, redirect_uri=self.redirect_uri)
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=token)

    def fetch_radio_api_key(self):
        html = urlopen("https://radio.net")
        soup = BeautifulSoup(html.read(), 'lxml');
        css_url = soup.find("link", rel="stylesheet", type="text/css")['href']
        self.radio_api_key = css_url.split('=')[1];

    def process_music(self):
        station_ids = []
        for station_id in stations.keys():
            station_ids.append(station_id)

        self.fetch_stations_history(station_ids)

        with open(HISTORY_FILE, 'w') as file:
            json.dump(self.all_added_tracks_array, file)
        self.logger.info("Done processing history for now...")

    def fetch_stations_history(self, station_ids):
        self.logger.info("Will fetch history...")

        tracks_by_station = self.fetch_stations_recently_played(station_ids)
        self.logger.debug("Received data: {}".format(json.dumps(tracks_by_station, indent=4, sort_keys=False)))
        for station_id, response_station in tracks_by_station.items():
            int_station_id = int(station_id)
            self.save_for_station(response_station, stations[int_station_id], self.all_added_tracks[int_station_id])

            # Save the history in case the server is restarted
            # Has to be transformed to a normal array since deque isn't JSON serializable
            self.all_added_tracks_array[station_id] = list(self.all_added_tracks[int_station_id])


    def save_for_station(self, response_station, station, processed_tracks):
        # Station specific variables
        station_name = station["station_name"]
        self.logger.info("Will sync for station: {}\n".format(station_name))

        playlist_uri = station["playlist_uri"]
        limit = station["limit"]

        tracks_to_add = []
        for track in reversed(response_station):
            stream_title = track["streamTitle"];
            # Some radio stations, such as Antenne Bayern Classic Rock, have their ads as the track name
            if stream_title and station_name != stream_title:
                if stream_title not in processed_tracks:
                    tracks_to_add.append(stream_title)

        if len(tracks_to_add) == 0:
            self.logger.info("Found no tracks for station: {}\n".format(station_name))
            return;

        # Get Spotify track URIs
        track_uris = []
        for stream_title in tracks_to_add:
            self.logger.info("Will search for: {}".format(stream_title))
            res = self.search_spotify_track(stream_title)
            if res == None or "tracks" not in res:
                continue # If response was malformed, try again next search
            searched_tracks = res["tracks"]

            processed_tracks.append(stream_title)
            if len(searched_tracks["items"]) < 1:
                self.logger.info("No tracks found\n")
                continue

            # Get the most similar title
            # This has to be done as it otherwise would have choosen the song "Billie Jean" from the album
            # "Thriller 25 Super Deluxe Edition" from the search query "Michael Jackson - Thriller"
            track_names = []
            for item in searched_tracks["items"]:
                track_names.append(item["name"])

            self.logger.info("Spotify API returned these tracks: {}".format(track_names))
            track_tile = ' - '.join(stream_title.split(' - ')[1:])

            matches = difflib.get_close_matches(track_tile, track_names, n=1)
            index = 0 # If no better match is found, use the first track
            if len(matches) > 0:
                closest = matches[0]
                index = track_names.index(closest)
                self.logger.info("Picked index: {} ({}): ".format(index, closest))
            found_track = searched_tracks["items"][index]

            self.logger.info("Will add track: {} by {} ({})\n".format(found_track["name"], found_track["artists"][0]["name"], found_track["uri"]))
            track_uris.append(found_track["uri"])

        if track_uris:
            # Add tracks to playlist
            self.add_tracks_to_playlist(playlist_uri, track_uris)

            # Remove any tracks overflowing the total 400 count
            tracks = self.get_playlist_tracks(playlist_uri)
            tracks_to_remove = []
            if len(tracks) > limit:
                for i in range(len(tracks) - limit):
                    # Add the track_uris for the tracks to be removed, along with their positions
                    tr = {"uri": tracks[i]["track"]["uri"],
                          "positions": [i]}
                    tracks_to_remove.append(tr)

                self.remove_tracks_from_playlist(playlist_uri, tracks_to_remove)

    @retry(stop=stop_after_delay(4), wait=wait_fixed(15))
    def fetch_stations_recently_played(self, station_ids):
        # Fetch recently played tracks
        url = 'https://api.radio.net/info/v2/search/nowplayingbystations'
        post_fields = {'apikey': self.radio_api_key,
                       'numberoftitles': 3,
                       'stations': ','.join([str(i) for i in station_ids])}
        self.logger.debug("Will query URL: {}, fields: {}".format(url, post_fields))

        request = Request(url, urlencode(post_fields).encode())
        resp = urlopen(request).read().decode()
        return json.loads(resp)

    # Methods that once fail, will refresh the Spotify token and retry the action
    @retry(reraise=True, stop=stop_after_delay(4), wait=wait_fixed(15))
    def search_spotify_track(self, track):
        try:
            return self.spotify.search(q=track, type='track', limit=5)
        except SpotifyException:
            self.refresh_token()
            pass

    @retry(reraise=True, stop=stop_after_delay(4), wait=wait_fixed(15))
    def add_tracks_to_playlist(self, playlist_uri, track_uris):
        try:
            self.spotify.user_playlist_add_tracks(USERNAME, playlist_uri, track_uris)
        except SpotifyException:
            self.refresh_token()
            pass

    @retry(reraise=True, stop=stop_after_delay(4), wait=wait_fixed(15))
    def remove_tracks_from_playlist(self, playlist_uri, track_uris):
        try:
            self.spotify.user_playlist_remove_specific_occurrences_of_tracks(USERNAME, playlist_uri, track_uris)
        except SpotifyException:
            self.refresh_token()
            pass

    # Help method to retrieve all tracks of a playlist, as the API only gives 100 at a time
    def get_playlist_tracks(self, playlist_uri):
        results = self.spotify.user_playlist_tracks(USERNAME, playlist_uri)
        tracks = results['items']
        while results['next']:
            results = self.spotify.next(results)
            tracks.extend(results['items'])
        return tracks

    # Method to refresh Spotify token
    def refresh_token(self):
        self.logger.info("Refreshing token")
        token = util.prompt_for_user_token(USERNAME, self.scope, client_id=CLIENT_ID,
                                           client_secret=CLIENT_SECRET, redirect_uri=self.redirect_uri)
        self.spotify = spotipy.Spotify(auth=token)


## Main
saver = RadioSaver()

while True:
    saver.process_music()
    time.sleep(180)
