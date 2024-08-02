from config import *
import json
import sys
from RadioNet import RadioNet
from RadioPlay import RadioPlay
from ILikeRadio import ILikeRadio
from SpotifyHandler import SpotifyHandler

from collections import deque
from os.path import exists
import difflib

import logging
from logging.handlers import RotatingFileHandler

HISTORY_FILE = 'history.json'

class RadioSaver:
    # Store the last ten tracks for each station, to prevent adding the same track over and over
    all_added_tracks = {}
    all_added_tracks_array = {}
    stations = {}
    for stations_list in [radio_net_stations, radio_play_stations, ilikeradio_stations]:
        stations.update(stations_list)

    if exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as file:
            all_added_tracks_temp = json.load(file)
            for station_id, station in stations.items(): # Convert the JSON data to deques
                if (str(station_id) not in all_added_tracks_temp):
                    all_added_tracks[station_id] = deque(maxlen=10)
                    continue

                all_added_tracks[station_id] = deque(all_added_tracks_temp[station_id], maxlen=10)
    else:
        for station_id in stations.keys():
            all_added_tracks[station_id] = deque(maxlen=10)

    def __init__(self):
        self.init_logging()
        self.spotify_handler = SpotifyHandler(CLIENT_ID, CLIENT_SECRET, len(self.stations), self.logger)
        self.radio_net = RadioNet(self.logger)
        self.radio_play = RadioPlay(self.logger)
        self.ilikeradio = ILikeRadio(self.logger)

    def init_logging(self):
        log_level = logging.INFO
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

    def process_music(self):
        self.fetch_stations_history()

        with open(HISTORY_FILE, 'w') as file:
            json.dump(self.all_added_tracks_array, file)
        self.logger.info("Done processing history for now...")

    def fetch_stations_history(self):
        self.logger.info("Will fetch history...")
        self.fetch_history_for_endpoint(self.radio_net, radio_net_stations)
        self.fetch_history_for_endpoint(self.radio_play, radio_play_stations)
        self.fetch_history_for_endpoint(self.ilikeradio, ilikeradio_stations)

    def fetch_history_for_endpoint(self, radio_endpoint, stations):
        station_ids = []
        for station_id in stations.keys():
            station_ids.append(station_id)

        response_by_station = radio_endpoint.fetch_stations_recently_played(station_ids)
        self.logger.debug("Received data: {}".format(json.dumps(response_by_station, indent=4, sort_keys=False)))
        for station_id, response_station in response_by_station.items():
            station = stations[station_id]
            station_name = station["station_name"]
            processed_tracks = self.all_added_tracks[station_id]
            self.logger.info("Will sync for station: {}\n".format(station_name))
            search_titles = radio_endpoint.titles_for_station(response_station, stations[station_id], processed_tracks)

            if len(search_titles) == 0:
                self.logger.info("Found no tracks for station: {}\n".format(station_name))
                continue

            # Get Spotify track URIs
            self.search_and_add_tracks(search_titles, processed_tracks, station["playlist_uri"], station["limit"])

            # Save the history in case the server is restarted
            # Has to be transformed to a normal array since deque isn't JSON serializable
            self.all_added_tracks_array[station_id] = list(self.all_added_tracks[station_id])

    def search_and_add_tracks(self, search_titles, processed_tracks, playlist_uri, limit):
        track_uris = []
        for stream_title in search_titles:
            self.logger.info("Will search for: {}".format(stream_title))
            res = self.spotify_handler.search_spotify_track(stream_title)
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

            self.logger.info("Will add track: {} by {} ({})\n".format(found_track["name"],
                                                                      found_track["artists"][0]["name"],
                                                                      found_track["uri"]))
            track_uris.append(found_track["uri"])

        if track_uris:
            # Add tracks to playlist
            self.spotify_handler.add_tracks_to_playlist(playlist_uri, track_uris)

            # Remove any tracks overflowing the total 400 count
            tracks = self.spotify_handler.get_overflowing_playlist_track_uris(playlist_uri, limit)
            if len(tracks) == 0:
                return

            tracks_to_remove = []
            for i, track in enumerate(tracks):
                # Add the track_uris for the tracks to be removed, along with their positions
                tracks_to_remove.append({
                    "uri": track["track"]["uri"],
                    "positions": [i]
                })

            self.spotify_handler.remove_tracks_from_playlist(playlist_uri, tracks_to_remove)
