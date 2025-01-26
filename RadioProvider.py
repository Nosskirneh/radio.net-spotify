class RadioProvider:
    def __init__(self, stations, logger):
        self.stations = stations
        self.logger = logger

    def titles_for_station(self, response_station, station, processed_tracks):
        raise NotImplementedError("Subclasses should implement this method")

    def fetch_stations_recently_played(self):
        raise NotImplementedError("Subclasses should implement this method")
