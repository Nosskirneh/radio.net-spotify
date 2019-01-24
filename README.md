radio.net-spotify
=================

Ever wanted to listen to music but don't wanna play the same music as you always do? Enjoy the music from radio stations but with higher bitrate and without ads!
radio.net-spotify is an application written in Python that transforms a radio.net station to a playlist storing the most recent tracks. It will sync every three minutes.

## Examples
Down below are some playlists created with radio.net-spotify.

#### Sweden
[Star FM](https://open.spotify.com/user/aspen71449/playlist/4Jr3WeBQNvoikBgrYULwDS?si=5eb1kRf0QimAT9J8uiVHtw)

#### Germany
[Antenne Bayern Classic Rock Live](https://open.spotify.com/user/aspen71449/playlist/6IMRUAc8RBz0sLLvyJDy2j?si=E4kg2FOiRtavuqcSH-ytvw)

## Playlist request
Not having the option to host an instance yourself? Open an issue and I can add the station to my instance and share the playlist. I do not guarantee 100 % uptime.

## Hosting yourself

First install the necessary python plugins:
`pip3 install spotipy tenacity lxml BeautifulSoup4`

### Configure radio.net station(s)
1. Browse the [radio.net](https://radio.net) for your favorite radio station.
2. Right click and select `Inspect Element`. Tap on the `Network` tab.
3. Refresh and look for the `nowplaying?` call. Select `Params`.
4. Copy the `station` value to the station's dictionary in `config.py`. The `apikey` is the same for every radio station and is fetched at launch.
5. For each radio station you would like to save, create a new Spotify playlist. Copy its Spotify URI within Spotify and store it into the `playlist_id` field.
6. Also enter the `station_name` of the station and the `limit` of how many tracks to save in the playlist. Some radio stations, such as [Antenne Bayern Classic Rock](http://antenneclassicrock.radio.net/), have their ads as the track name. Entering the exact name will thus filter these out.

### Create a Spotify application (required for API access)
1. Create a Spotify application at https://developer.spotify.com/my-applications/
2. Add `http://localhost:8888/callback` as a redirect URL for your app.
3. Add the `Client ID` and `Client Secret` keys to the `config.py` file.
4. Once it has started, you will be redirected to a page. Copy the URL and paste it into the terminal once it asks for it.

### Autostart with Linux
If you're running a distro of Linux that has systemd, change the directories and users of this below to your liking

```
[Unit]
Description=radio.net-spotify
After=syslog.target network.target

[Service]
WorkingDirectory=/srv/radio.net-spotify/
ExecStart=/srv/radio.net-spotify/RadioSaver.py
Restart=always
User=radionet

[Install]
WantedBy=multi-user.target
```
