from argparse import ArgumentParser
import json
from spotipy import Spotify, SpotifyClientCredentials
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic
import os
import colorama
from halo import Halo

URL_TYPE_SPOTIFY_TRACK = 0
URL_TYPE_SPOTIFY_PLAYLIST = 1
URL_TYPE_YOUTUBE_TRACK = 2
URL_TYPE_YOUTUBE_PLAYLIST = 3
URL_TYPE_NAMES = ['Spotify Track', 'Spotify Playlist', 'Youtube Track', 'Youtube Playlist']

arg_parser = ArgumentParser(prog = 'MusicDownloader',
                            description= 'Downloader for music from Youtube or Spotify')

arg_parser.add_argument('url', help="Track or Playlist URL")
arg_parser.add_argument('--gui', action='store_true', help='Opens up a GUI')
args = arg_parser.parse_args()

# Spotify API Config
config = {}
try:
    config_fp = open("config.json", "r")
    config = json.load(config_fp)
except:
    # Create new config
    client_id_input = input("Spotify Client ID: ")
    client_secret_input = input("Spotify Client Secret: ")
    config = {
        "client_id": client_id_input,
        "client_secret": client_secret_input
    }
    config_fp = open("config.json", "w+")
    config_fp.write(json.dumps(config))

ytmusic = YTMusic()
sp = Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=config["client_id"], client_secret=config["client_secret"]))

def download_youtube_audio(url, folder):
    path = 'downloads/' + folder

    yt = YoutubeDL({'quiet': True, 'paths': {'home': path}, 'format': 'm3a/bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',}]})
    info = yt.extract_info(url, download=False)

    if not os.path.exists(path):
        os.makedirs(path)

    yt.download(url)

def download_youtube_single_track(url):
    spinner = Halo(text='Downloading', spinner='dots')
    spinner.start()
    download_youtube_audio(url, '')
    spinner.stop()

def find_youtube_track(url):
    track = sp.track(url)
    query = track["name"] + " " + track["artists"][0]["name"]

    results = ytmusic.search(query, filter="songs")
    result_id = ""

    for i in range(len(results)):
        category = results[i]["category"]
        result_type = results[i]["resultType"]

        if category == "Songs" and result_type == "song":
            result_id = results[i]["videoId"]
            return "https://youtube.com/watch?v=%s" % (result_id)
        else:
            pass

    return "https://youtube.com/watch?v=%s" % (result_id)

def download_spotify_track(url, folder):
    spinner = Halo(text='Searching', spinner='dots')
    spinner.start()
    youtube_url = find_youtube_track(url)
    spinner.stop()

    spinner = Halo(text='Downloading', spinner='dots')
    spinner.start()
    download_youtube_audio(youtube_url, folder)
    spinner.stop()

def fetch_spotify_playlist_tracks(id):
    playlist = sp.playlist(id)
    tracks = playlist['tracks']['items']

    if playlist['tracks']['total'] > 100:
        offset = 0
        total = playlist['tracks']['total']

        while offset < total:
            tracks.extend(sp.playlist_items(id, None, 100, offset))

            offset += 100

    return tracks

def download_spotify_playlist(url):
    spinner = Halo(text='Fetching Playlist', spinner='dots')
    spinner.start()

    playlist = sp.playlist(url)
    tracks = fetch_spotify_playlist_tracks(playlist['id'])

    spinner.stop()
    print("Playlist: %s\n%d tracks\n" % (playlist["name"], len(tracks)))

    for i in range(len(tracks)):
        track_id = tracks[i]["track"]["id"]

        track = sp.track(track_id)
        folder = playlist["name"]

        download_spotify_track(track_id, folder)
        spinner.succeed("%s - %s" % (track["artists"][0]["name"], track["name"]))

colorama.init()
spinner = Halo(text='Please wait', spinner='dots')
spinner.start()

# Analyze url type
url_type = 0
if "spotify.com" in args.url:
    if "track" in args.url:
        url_type = URL_TYPE_SPOTIFY_TRACK
    elif "playlist" in args.url:
        url_type = URL_TYPE_SPOTIFY_PLAYLIST
elif "youtube" in args.url:
    if "watch" in args.url and not "list" in args.url:
        url_type = URL_TYPE_YOUTUBE_TRACK
    elif "list" in args.url:
        url_type = URL_TYPE_YOUTUBE_PLAYLIST
else:
    print("Unsupported URL type!")
    exit(-1)

spinner.stop()

if url_type is URL_TYPE_SPOTIFY_TRACK:
    download_spotify_track(args.url)
    track = sp.track(args.url)
    spinner.succeed("%s - %s" % (track["artists"][0]["name"], track["name"]))
elif url_type is URL_TYPE_YOUTUBE_TRACK:
    download_youtube_single_track(args.url)
elif url_type is URL_TYPE_SPOTIFY_PLAYLIST:
    download_spotify_playlist(args.url)