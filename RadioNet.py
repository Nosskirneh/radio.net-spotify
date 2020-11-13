from urllib.parse import urlencode
from urllib.request import Request, urlopen
from tenacity import *
import json

from bs4 import BeautifulSoup

class RadioNet:
    def __init__(self, logger):
        self.logger = logger
        self.recently_played_url = 'https://api.radio.net/info/v2/search/nowplayingbystations'
        self.fetch_radio_api_key()

    def fetch_radio_api_key(self):
        url = "https://radio.net"
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        soup = BeautifulSoup(page, 'lxml')
        scripts = soup.findAll("script")

        for script in scripts:
            if (len(script.contents) <= 0):
                continue

            content = script.contents[0];
            if "https://api.radio.net" in content:
                search_term = "apiKey: '"
                pos = content.rfind(search_term)
                start_pos = pos + len(search_term)
                self.radio_api_key = content[start_pos:start_pos + 40]
                return

        sys.exit("Could not find an API key to radio.net")

    def titles_for_station(self, response_station, station, processed_tracks):
        # Station specific variables
        search_titles = []
        for track in reversed(response_station):
            stream_title = track["streamTitle"]
            # Some radio stations, such as Antenne Bayern Classic Rock, have their ads as the track name
            if stream_title and station["station_name"] != stream_title and stream_title not in processed_tracks:
                search_titles.append(stream_title)
        
        return search_titles


    @retry(stop=stop_after_delay(4), wait=wait_fixed(15))
    def fetch_stations_recently_played(self, station_ids):
        # Fetch recently played tracks
        url = self.recently_played_url
        post_fields = {'apikey': self.radio_api_key,
                       'numberoftitles': 3,
                       'stations': ','.join([str(i) for i in station_ids])}
        self.logger.debug("Will query URL: {}, fields: {}".format(url, post_fields))

        request = Request(url, urlencode(post_fields).encode())
        resp = urlopen(request).read().decode()
        return json.loads(resp)
