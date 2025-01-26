import spotipy
from spotipy import SpotifyOAuth
from spotipy.client import SpotifyException
from spotipy.cache_handler import CacheFileHandler
from tenacity import retry, stop_after_delay, wait_fixed
from SetTTLOnceCache import SetTTLOnceCache


class SpotifyHandler:

    def __init__(self, client_id, client_secret, num_playlists, storage_directory, logger):
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger
        # Only check the number of overflowing tracks once every 12 hours
        self.overflow_cache = SetTTLOnceCache(maxsize=num_playlists, ttl=3600 * 12)
        self.init_connection(storage_directory)

    def init_connection(self, storage_directory):
        self.scope = 'playlist-modify-public'
        self.redirect_uri = 'http://localhost:8888/callback/'
        cache_path = f"{storage_directory}/.cachedauth" if storage_directory else ".cachedauth"
        self.auth_manager = SpotifyOAuth(scope=self.scope,
                                         client_id=self.client_id,
                                         client_secret=self.client_secret,
                                         redirect_uri=self.redirect_uri,
                                         open_browser=False,
                                         cache_handler=CacheFileHandler(cache_path=cache_path))
        self.connection = spotipy.Spotify(auth_manager=self.auth_manager)


    # Methods that once fail, will refresh the Spotify token and retry the action
    @retry(reraise=True, stop=stop_after_delay(4), wait=wait_fixed(15))
    def search_spotify_track(self, track):
        try:
            return self.connection.search(q=track, type='track', limit=5)
        except SpotifyException:
            self.refresh_connection()
            pass

    @retry(reraise=True, stop=stop_after_delay(4), wait=wait_fixed(15))
    def add_tracks_to_playlist(self, playlist_uri, track_uris):
        try:
            self.connection.playlist_add_items(playlist_uri, track_uris)
            self.try_change_overflow_cache(playlist_uri, len(track_uris))
        except SpotifyException:
            self.refresh_connection()
            pass

    @retry(reraise=True, stop=stop_after_delay(4), wait=wait_fixed(15))
    def remove_tracks_from_playlist(self, playlist_uri, track_uris):
        try:
            self.connection.playlist_remove_specific_occurrences_of_items(playlist_uri, track_uris)
            self.try_change_overflow_cache(playlist_uri, -len(track_uris))
        except SpotifyException:
            self.refresh_connection()
            pass

    def get_overflowing_playlist_track_uris(self, playlist_uri, limit):
        def query_tracks(offset, amount=10, fields=["items.track.uri"]):
            return self.connection.playlist_tracks(playlist_uri,
                                                   offset=offset,
                                                   limit=amount,
                                                   fields=fields)
        # First we need to query the end of the playlist to see if there's anything overflowing
        try:
            num_overflowing = self.overflow_cache[playlist_uri]
        except KeyError:
            num_overflowing = query_tracks(limit, fields=["total"])["total"] - limit

        if (num_overflowing <= 0):
            return []
        # Then we need to query the beginning of the playlist
        uris = []
        page_limit = 100
        offset = 0
        remaining = num_overflowing
        while remaining > 0:
            next_limit = min(page_limit, remaining)
            uris.extend(query_tracks(offset, next_limit)['items'])
            offset += next_limit
            remaining -= next_limit
        self.overflow_cache[playlist_uri] = num_overflowing
        return uris

    # Method to refresh Spotify token
    def refresh_connection(self):
        self.logger.info("Refreshing token")
        self.connection = spotipy.Spotify(auth_manager=self.auth_manager)

    def try_change_overflow_cache(self, playlist_uri, diff):
        if playlist_uri in self.overflow_cache:
            self.overflow_cache[playlist_uri] += diff
