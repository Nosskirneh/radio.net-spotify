import spotipy
import spotipy.util as util
from spotipy.client import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from tenacity import retry, stop_after_delay, wait_fixed


class SpotifyHandler:

    def __init__(self, username, client_id, client_secret, logger):
        self.username = username
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger
        self.init_connection()

    def init_connection(self):
        self.redirect_uri = 'http://localhost:8888/callback/'
        self.scope = 'playlist-modify-public'
        client_credentials_manager = SpotifyClientCredentials(client_id=self.client_id,
                                                              client_secret=self.client_secret)
        self.connection = spotipy.Spotify(client_credentials_manager=client_credentials_manager,
                                          auth=self.get_token())


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
            self.connection.user_playlist_add_tracks(self.username, playlist_uri, track_uris)
        except SpotifyException:
            self.refresh_connection()
            pass

    @retry(reraise=True, stop=stop_after_delay(4), wait=wait_fixed(15))
    def remove_tracks_from_playlist(self, playlist_uri, track_uris):
        try:
            self.connection.user_playlist_remove_specific_occurrences_of_tracks(self.username, playlist_uri, track_uris)
        except SpotifyException:
            self.refresh_connection()
            pass

    def get_overflowing_playlist_track_uris(self, playlist_uri, limit):
        fields = ["items.track.uri"]
        def query_tracks(offset, amount):
            return self.connection.user_playlist_tracks(self.username,
                                                        playlist_uri,
                                                        offset=offset,
                                                        limit=amount,
                                                        fields=fields)['items']
        # First we need to query the end of the playlist to see if there's anything overflowing
        first_tracks = query_tracks(limit + 1, 10)
        num_overflowing = len(first_tracks)
        if (num_overflowing == 0):
            return []
        # Then we need to query the beginning of the playlist
        return query_tracks(0, num_overflowing)

    def get_token(self):
        return util.prompt_for_user_token(self.username, self.scope, client_id=self.client_id,
                                          client_secret=self.client_secret, redirect_uri=self.redirect_uri)

    # Method to refresh Spotify token
    def refresh_connection(self):
        self.logger.info("Refreshing token")
        self.connection = spotipy.Spotify(auth=self.get_token())
