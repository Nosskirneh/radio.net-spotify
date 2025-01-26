# Spotify configs
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# Station configs
configured_providers = {
    "radio.net": {
        "antenneclassicrock": {
            "station_name": "ANTENNE BAYERN - Classic Rock Live",
            "playlist_uri": 'spotify:playlist:6IMRUAc8RBz0sLLvyJDy2j',
            "limit": 400
        },
    },
    "radioplay.se": {
        "nrs": {
            "station_name": "NRJ Sweden",
            "playlist_uri": 'spotify:playlist:24TvGqDGbVkzmMZbVWsuX3',
            "limit": 400
        },
        "mmg": {
            "station_name": "Mix Megapol Göteborg",
            "playlist_uri": 'spotify:playlist:6c4YIthwwnAbQ016Iwl4W2',
            "limit": 400
        }
    },
    "ilikeradio.se": {
        "94": {
            "station_name": "STAR FM",
            "playlist_uri": 'spotify:playlist:4Jr3WeBQNvoikBgrYULwDS',
            "limit": 400
        },
        "3": {
            "station_name": "RIX FM",
            "playlist_uri": 'spotify:playlist:2pn4YrZ8uJYqXuV1PnJbDb',
            "limit": 400
        }
    }
}
