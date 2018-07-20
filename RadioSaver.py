#!/usr/bin/env python3

from config import *
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
import json
import schedule, time
import sys

from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from collections import deque
from os.path import exists

HISTORY_FILE = 'history.json'

class RadioSaver:
    # Store the last ten tracks for each station, to prevent adding the same track over and over
    allAddedTracks = {}
    if exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as file:
            allAddedTracks = json.load(file)
            for station in stations: # Transfer the JSON data to deques
                station_id = station["station_id"]
                allAddedTracks[station_id] = deque(allAddedTracks[str(station_id)], maxlen=10)
    else:
        for station in stations:
            allAddedTracks[station["station_id"]] = deque(maxlen=10)

    def initSpotify(self):
        scope = 'playlist-modify-public'
        redirect_uri = 'http://localhost:8888/callback/'
        client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID,
                                                              client_secret=CLIENT_SECRET)
        self.token = util.prompt_for_user_token(USERNAME, scope, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=redirect_uri)
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=self.token)

    def processMusic(self):
        allAddedTracksArray = {}

        for station in stations:
            self.saveForStation(station)

            # Save the history in case the server is restarted
            # Has to be transformed to a normal array since deque isn't JSON serializable
            station_id = station["station_id"]
            allAddedTracksArray[station_id] = list(self.allAddedTracks[station_id])

        with open(HISTORY_FILE, 'w') as file:
            json.dump(allAddedTracksArray, file)


    def saveForStation(self, station):
        print("Will sync for station: {}\n".format(station["name"]))

        # Station specific variables
        station_id = station["station_id"]
        playlist_id = station["playlist_id"]
        name = station["name"]
        limit = station["limit"]
        addedTracks = self.allAddedTracks[station_id]

        url = 'https://api.radio.net/info/v2/search/nowplaying'
        post_fields = {'apikey': 'df5cadfe49eeaff53727bad8c69b47bdf4519123',
                       'numberoftitles': 10,
                       'station': station_id}

        request = Request(url, urlencode(post_fields).encode())
        resp = urlopen(request).read().decode()
        tracks = json.loads(resp)

        tracksToAdd = []
        for track in reversed(tracks):
            trackName = track["streamTitle"];
            # Some radio stations, such as Antenne Bayern Classic Rock, have their ads as the track name
            if trackName and name != trackName:
                if trackName not in addedTracks:
                    tracksToAdd.append(trackName)

        # Get Spotify track URIs
        trackURIs = []
        for track in tracksToAdd:
            print("Will search for track: ", track)
            res = self.spotify.search(q=track, type='track')
            tracks = res["tracks"]

            if len(tracks["items"]) < 1:
                continue

            item = tracks["items"][0]
            print("Will add track: {} ({})\n".format(item["name"], item["uri"]))

            trackURIs.append(item["uri"])
            addedTracks.append(track)

        if trackURIs:
            # Add tracks to playlist
            self.spotify.user_playlist_add_tracks(USERNAME, playlist_id, trackURIs)

            # Remove any tracks overflowing the total 400 count
            tracks = self.get_playlist_tracks(playlist_id)
            tracksToRemove = []
            if len(tracks) > limit:
                for i in range(len(tracks) - limit):
                    # Add the trackURIs for the tracks to be removed, along with their positions
                    tr = {"uri": tracks[i]["track"]["uri"],
                          "positions": [i]}
                    tracksToRemove.append(tr)

                self.spotify.user_playlist_remove_specific_occurrences_of_tracks(USERNAME, playlist_id, tracksToRemove)


    # Help method to retrieve all tracks of a playlist, as the API only gives 100 at a time
    def get_playlist_tracks(self, playlist_id):
        results = self.spotify.user_playlist_tracks(USERNAME, playlist_id)
        tracks = results['items']
        while results['next']:
            results = self.spotify.next(results)
            tracks.extend(results['items'])
        return tracks

## Main
saver = RadioSaver()
saver.initSpotify()
saver.processMusic()

schedule.every(3).minutes.do(saver.processMusic)

while True:
    schedule.run_pending()
    time.sleep(1)
