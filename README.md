radio.net-spotify
=================

Ever wanted to listen to music but don't wanna play the same music as you always do? Enjoy the music from radio stations but with higher bitrate and without ads!
radio.net-spotify is an application written in Python that transforms a radio.net, ilikeradio.se or radioplay.se station to a playlist storing the most recent tracks. It will sync every three minutes.

## Examples
Down below are some playlists created with radio.net-spotify.

#### Sweden
[Star FM](https://open.spotify.com/user/aspen71449/playlist/4Jr3WeBQNvoikBgrYULwDS?si=5eb1kRf0QimAT9J8uiVHtw)

#### Germany
[Antenne Bayern Classic Rock Live](https://open.spotify.com/user/aspen71449/playlist/6IMRUAc8RBz0sLLvyJDy2j?si=E4kg2FOiRtavuqcSH-ytvw)

## Playlist request
Not having the option to host an instance yourself? Open an issue and I can add the station to my instance and share the playlist. I do not guarantee 100 % uptime.

## Hosting yourself

Create the following file `.env`:
```
CLIENT_ID=<client ID>
CLIENT_SECRET=<client secret>
```

Add a `STORAGE_DIRECTORY` to specify a directory to store the state, Spotify auth info and log files if running with Docker.

Build the docker container: `docker build -t radionet-spotify .`
Run the docker container: `docker run -it --rm --env-file .env -p 8888:8888 radionet-spotify`

### Configure radio.net station(s)
1. Browse [radio.net](https://radio.net) for your favorite radio station.
2. Right click and select `Inspect Element`. Tap on the `Network` tab.
3. Refresh and look for the first GET request. The ID of the station is the name you see. Copy the station ID to the key of the station's dictionary in `config.py`.
4. For each radio station you would like to save, create a new Spotify playlist. Copy its Spotify URI within Spotify and store it into the `playlist_uri` field.
5. Also enter the `station_name` of the station and the `limit` of how many tracks to save in the playlist. Some radio stations, such as [Antenne Bayern Classic Rock](http://antenneclassicrock.radio.net/), have their ads as the track name. Entering the exact name will thus filter these out.

### Other endpoints
RadioPlay and ILikeRadio are also supported. Finding the respective station ID can be done in similar fashion as for radio.net.

### Create a Spotify application (required for API access)
1. Create a Spotify application at https://developer.spotify.com/my-applications/
2. Add `http://localhost:8888/callback` as a redirect URL for your app.
3. Add the `Client ID` and `Client Secret` keys to the `config.py` file.
4. Once it has started, you will be redirected to a page. Copy the URL and paste it into the browser once it asks for it.
