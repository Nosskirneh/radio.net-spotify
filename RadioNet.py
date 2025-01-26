from urllib.parse import urlencode
from urllib.request import Request, urlopen
from tenacity import *
import json

class RadioNet:
    def __init__(self, logger):
        self.logger = logger
        self.recently_played_url = 'https://prod.radio-api.net/stations/{}/songs'

    def titles_for_station(self, response_station, station, processed_tracks):
        # Station specific variables
        search_titles = []
        for track in reversed(response_station):
            stream_title = track["rawInfo"]
            # Some radio stations, such as Antenne Bayern Classic Rock, have their ads as the track name
            if stream_title and station["station_name"] != stream_title and stream_title not in processed_tracks:
                search_titles.append(stream_title)

        return search_titles

    def fetch_stations_recently_played(self, station_ids):
        responses = {}
        for station_id in station_ids:
            responses[station_id] = self.recently_played_for_station(station_id)
        return responses

    @retry(stop=stop_after_delay(4), wait=wait_fixed(15))
    def recently_played_for_station(self, station_id):
        # Fetch recently played tracks
        url = self.recently_played_url.format(station_id)
        self.logger.debug("Will query URL: {}".format(url))

        request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(request).read().decode()
        return json.loads(resp)
