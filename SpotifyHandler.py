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

    # Help method to retrieve all tracks of a playlist, as the API only gives 100 at a time
    def get_playlist_tracks(self, playlist_uri):
        results = self.connection.user_playlist_tracks(self.username, playlist_uri)
        tracks = results['items']
        while results['next']:
            results = self.connection.next(results)
            tracks.extend(results['items'])
        return tracks

    def get_token(self):
        return util.prompt_for_user_token(self.username, self.scope, client_id=self.client_id,
                                          client_secret=self.client_secret, redirect_uri=self.redirect_uri)

    # Method to refresh Spotify token
    def refresh_connection(self):
        self.logger.info("Refreshing token")
        self.connection = spotipy.Spotify(auth=self.get_token())
