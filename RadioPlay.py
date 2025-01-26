from urllib.parse import quote
from urllib.request import Request, urlopen
from tenacity import *
import json
from datetime import datetime
from RadioProvider import RadioProvider

class RadioPlay(RadioProvider):
    def __init__(self, stations, logger):
        super().__init__(stations, logger)
        self.recently_played_url = 'https://listenapi.planetradio.co.uk/api9.2/events/{}/{}/{}'

    def titles_for_station(self, response_station, station, processed_tracks):
        # Station specific variables
        search_titles = []
        for track in reversed(response_station):
            stream_title = "{} - {}".format(track["nowPlayingArtist"], track["nowPlayingTrack"])
            # Some radio stations, such as Antenne Bayern Classic Rock, have their ads as the track name
            if stream_title not in processed_tracks:
                search_titles.append(stream_title)
        
        return search_titles

    def fetch_stations_recently_played(self):
        responses = {}
        for station_id in self.stations:
            responses[station_id] = self.recently_played_for_station(station_id)
        return responses

    @retry(stop=stop_after_delay(4), wait=wait_fixed(15))
    def recently_played_for_station(self, station_id):
        # Fetch recently played tracks
        now = quote(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        url = self.recently_played_url.format(station_id, now, 3)
        self.logger.debug("Will query URL: {}".format(url))

        request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(request).read().decode()
        return json.loads(resp)
