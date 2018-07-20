radio.net-spotify
=================

Ever wanted to listen to music but don't wanna play the same music as you always do? Enjoy the music from radio stations with higher bitrate and without ads!
radio.net-spotify is a server written in Python that transforms a radio.net station to a playlist storing the most recent tracks. It will sync every three minutes.

## Playlist request
Not having the option to host an instance yourself? Open an issue and I can add the station to my server and share the playlist. I do not guarantee 100 % uptime.

## Hosting yourself

### Configure radio.net station(s)
1. Browse the [radio.net](https://radio.net) for your favorite radio station.
2. Right click and select `Inspect Element`. Tap on the `Network` tab.
3. Refresh and look for the `nowplaying?` call. Select `Params`.
4. Copy the `station` value to the station's dictionary in `config.py`. The `apikey` seems to be the same for every radio station and is thus hardcoded into the saver.
5. For each radio station you would like to save, create a new Spotify playlist. Copy its Spotify URI within Spotify and store it into the `playlist_id` field.
6. Also enter the `station_name` of the station and the `limit` of how many tracks to save in the playlist. Some radio stations, such as Antenne Bayern Classic Rock, have their ads as the track name. Entering the exact name will thus filter these out.

### Create a Spotify application (required for API access)
1. Create a Spotify application at https://developer.spotify.com/my-applications/
2. Add `http://localhost:8080/callback` as a redirect URL for your app.
3. Add the `Client ID` and `Client Secret` keys to the `config.py` file.
4. Once the server has started, you will be redirected to a page. Copy the URL and paste it into the terminal once it asks for it.