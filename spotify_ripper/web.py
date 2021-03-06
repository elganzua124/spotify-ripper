# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from colorama import Fore
from spotify_ripper.utils import *
import os
import time
import spotify
import requests
import spotipy
import spotipy.client
from spotipy.oauth2 import SpotifyClientCredentials

client_credentials_sp = None

def init_client_credentials_sp():

    global client_credentials_sp
    if client_credentials_sp is None:
        client_credentials_manager = SpotifyClientCredentials()
        client_credentials_sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        client_credentials_sp.trace = False

    return client_credentials_sp

class WebAPI(object):

    def __init__(self, args):
        self.args = args
        self.cache = {
            "artist_albums": {},
            "artists_on_album": {},
            "genres": {},
            "charts": {},
            "large_coverart": {}
        }

    def cache_result(self, name, uri, result):
        self.cache[name][uri] = result

    def get_cached_result(self, name, uri):
        return self.cache[name].get(uri)

    def request_json(self, url, msg):
        print(Fore.GREEN + "Attempting to retrieve " + msg +
              " from Spotify's Web API" + Fore.RESET)
        print(Fore.CYAN + url + Fore.RESET)
        sp = init_client_credentials_sp()
        try:
            res = sp._get(url)
        except spotify.SpotifyException as e:
            print(Fore.YELLOW + "URL returned non-200 HTTP code: " +
                  str(e.http_status) + " message: " + e.msg + Fore.RESET)
            return None
        return res

    def request_url(self, url, msg):
        print(Fore.GREEN + "Attempting to retrieve " + msg +
              " from Spotify's Web API" + Fore.RESET)
        print(Fore.CYAN + url + Fore.RESET)
        res = requests.get(url)
        if res.status_code == 200:
            return res
        else:
            print(Fore.YELLOW + "URL returned non-200 HTTP code: " +
                  str(res.status_code) + Fore.RESET)
        return None

    def api_url(self, url_path):
        return 'https://api.spotify.com/v1/' + url_path

    def charts_url(self, url_path):
        return 'https://spotifycharts.com/' + url_path

    def get_artist_albums(self, artist_id):
        args = self.args

        sp = init_client_credentials_sp()

        albums = []
        album_uris = []
        results = sp.artist_albums(artist_id, args.artist_album_type, args.artist_album_market)
        albums.extend(results['items'])
        while results['next']:
            results = sp.next(results)
            albums.extend(results['items'])

        # check for cached result
        cached_result = self.get_cached_result("artist_albums", artist_id)
        if cached_result is not None:
            return cached_result

        album_uris += [album['uri'] for album in albums]

        print(str(len(album_uris)) + " albums found")
        self.cache_result("artist_albums", artist_id, album_uris)
        return album_uris

    def get_artists_on_album(self, uri):

        # check for cached result
        cached_result = self.get_cached_result("artists_on_album", uri)
        if cached_result is not None:
            return cached_result

        # extract album id from uri
        uri_tokens = uri.split(':')
        if len(uri_tokens) != 3:
            return None
        sp = init_client_credentials_sp()
        album = sp.album(uri_tokens[2])
        if album is None:
            return None

        result = [artist['name'] for artist in album['artists']]
        self.cache_result("artists_on_album", uri, result)
        return result

    # genre_type can be "artist" or "album"
    def get_genres(self, genre_type, track):
        def get_genre_json(spotify_id):
            url = self.api_url(genre_type + 's/' + spotify_id)
            return self.request_json(url, "genres")

        # extract album id from uri
        item = track.artists[0] if genre_type == "artist" else track.album
        uri = item.link.uri

        # check for cached result
        cached_result = self.get_cached_result("genres", uri)
        if cached_result is not None:
            return cached_result

        uri_tokens = uri.split(':')
        if len(uri_tokens) != 3:
            return None

        json_obj = get_genre_json(uri_tokens[2])
        if json_obj is None:
            return None

        result = json_obj["genres"]
        self.cache_result("genres", uri, result)
        return result

    def get_large_coverart(self, uri):
        def get_track_json(track_id):
            url = self.api_url('tracks/' + track_id)
            return self.request_json(url, "track")

        def get_image_data(url):
            response = self.request_url(url, "cover art")
            return response.content

        # check for cached result
        cached_result = self.get_cached_result("large_coverart", uri)
        if cached_result is not None:
            return get_image_data(cached_result)

        # extract album id from uri
        uri_tokens = uri.split(':')
        if len(uri_tokens) != 3:
            return None

        track = get_track_json(uri_tokens[2])
        if track is None:
            return None

        try:
            images = track['album']['images']
        except KeyError:
            return None

        for image in images:
            if image["width"] == 640:
                self.cache_result("large_coverart", uri, image["url"])
                return get_image_data(image["url"])

        return None


