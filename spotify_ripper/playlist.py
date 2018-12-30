import spotipy.util as util
import spotipy.client
import os
from colorama import Fore, Style
from spotify_ripper.utils import *
import requests
import json

from itertools import islice
import csv
import re

from spotify_ripper.web import WebAPI

client_id = ''
client_secret = ''
redirect_uri = 'http://www.purple.com'

scope = 'playlist-modify-public playlist-modify-private playlist-read-collaborative'

# client_id = os.environ["SPOTIPY_CLIENT_ID"] 
# client_secret = os.environ["SPOTIPY_CLIENT_SECRET"]
# redirect_uri = os.environ["SPOTIPY_REDIRECT_URI"]


import abc

class Playlist(abc.ABC): # Needs refactoring

    def __init__(self,s,playlist_uri):
        self.session = s
        self.uri = playlist_uri
        self.username = self.session.user.canonical_name
        self.id = self.uri.split(':')[-1]

        def spotify_object():
            token = util.prompt_for_user_token(self.username, scope,client_id, client_secret, redirect_uri)
            spotify_object = spotipy.Spotify(auth=token)
            spotify_object.trace = False
            return spotify_object

        self._sp = spotify_object()

        self._playlist = self.__populate()
        self.name = self._playlist['name']
        self.tracks = self.__get_tracks()

    @abc.abstractmethod
    def __populate(self): #cambiar nombre
        pass

    @abc.abstractmethod
    def __get_tracks(self):
        pass

    @abc.abstractmethod
    def can_remove_tracks(self):
        pass

class Current_playlist(Playlist): # cambiar nombre, Mixed_playlist tal vez?

    def __init__(self,s,playlist_uri):
        super().__init__(s,playlist_uri)
        self._playlist = self._sp.playlist(self.id)

    def _Playlist__populate(self):
        return self._sp.playlist(self.id)

    def _Playlist__get_tracks(self):
        print('Getting Results')
        results = self._sp.playlist(self.id, fields="tracks")
        "usar playlist_tracks"

        tracks = results['tracks'].get('items')

        track_objects = []

        for n in tracks:
            this_track_uri = n['track'].get('uri')
            this_track_object = self.session.get_link(this_track_uri).as_track()
            track_objects.append(this_track_object)

        print('Loading playlist...')
        return track_objects

    def can_remove_tracks(self):

        def owner_display_name():
            owner = self._playlist['owner']
            if owner['display_name'] == None:
                return str(owner['id'])
            return str(owner['display_name'])

        if owner_display_name() == self.session.user.canonical_name:
            return True
        return False

    def remove_tracks(self,track_ids):
        results = self._sp.user_playlist_remove_all_occurrences_of_tracks(self.id, track_ids)


class Album(Playlist): # an_album_playlist

    def __init__(self,s,playlist_uri):
        super().__init__(s,playlist_uri)
        self._playlist = self._sp.album(self.id)

    def _Playlist__populate(self):
        return self._sp.album(self.id)

    def can_remove_tracks(self):
        return False

    def _Playlist__get_tracks(self):
        print('Getting Results')
        print(self.name)
        results = self._sp.album_tracks(self.id)

        tracks = results['items']

        track_objects = []

        for n in tracks:
            this_track_uri = n['external_urls']['spotify']
            this_track_object = self.session.get_link(this_track_uri).as_track()
            track_objects.append(this_track_object)
        print('Loading album...')
        return track_objects

    def remove_tracks(self,tracks_to_remove):
        print('You cannot remove tracks from an album.')

    """def name_for_m3u(self)
        return artist + album """

class Chart_playlist(Playlist):

    def __init__(self,s,playlist_uri):

        self._valid_metrics = {"regional", "viral"}
        self._valid_regions = {
            "global": "Global",
            "us": "United States",
            "gb": "United Kingdom",
            "ad": "Andorra",
            "ar": "Argentina",
            "at": "Austria",
            "au": "Australia",
            "be": "Belgium",
            "bg": "Bulgaria",
            "bo": "Bolivia",
            "br": "Brazil",
            "ca": "Canada",
            "ch": "Switzerland",
            "cl": "Chile",
            "co": "Colombia",
            "cr": "Costa Rica",
            "cy": "Cyprus",
            "cz": "Czech Republic",
            "de": "Germany",
            "dk": "Denmark",
            "do": "Dominican Republic",
            "ec": "Ecuador",
            "ee": "Estonia",
            "es": "Spain",
            "fi": "Finland",
            "fr": "France",
            "gr": "Greece",
            "gt": "Guatemala",
            "hk": "Hong Kong",
            "hn": "Honduras",
            "hu": "Hungary",
            "id": "Indonesia",
            "ie": "Ireland",
            "is": "Iceland",
            "it": "Italy",
            "lt": "Lithuania",
            "lu": "Luxembourg",
            "lv": "Latvia",
            "mt": "Malta",
            "mx": "Mexico",
            "my": "Malaysia",
            "ni": "Nicaragua",
            "nl": "Netherlands",
            "no": "Norway",
            "nz": "New Zealand",
            "pa": "Panama",
            "pe": "Peru",
            "ph": "Philippines",
            "pl": "Poland",
            "pt": "Portugal",
            "py": "Paraguay",
            "se": "Sweden",
            "sg": "Singapore",
            "sk": "Slovakia",
            "sv": "El Salvador",
            "tr": "Turkey",
            "tw": "Taiwan",
            "uy": "Uruguay"
        }
        self._valid_windows = {"daily", "weekly"}
        self.__sanity(playlist_uri)
        self.uri_tokens = playlist_uri.split(':')
        self.session = s
        self.uri = playlist_uri
        self.username = self.session.user.canonical_name
        self.id = self.uri.split(':')[-1]
        self.name = self.__get_name()
        self.tracks = self._Playlist__get_tracks()

    def __sanity(self,playlist_uri):
    # some sanity checking

        def sanity_check(val, valid_set):
            if val not in valid_set:
                print(Fore.RED +
                      "Not a valid Spotify charts URI parameter: " +
                      val + Fore.RESET)
                print("Valid parameter options are: [" +
                      ", ".join(valid_set) + "]")
                return False
            return True

        def sanity_check_date(val):
            if  re.match(r"^\d{4}-\d{2}-\d{2}$", val) is None and \
                    val != "latest":
                print(Fore.RED +
                      "Not a valid Spotify charts URI parameter: " +
                      val + Fore.RESET)
                print("Valid parameter options are: ['latest', a date "
                      "(e.g. 2016-01-21)]")
                return False
            return True

        # spotify:charts:metric:region:time_window:date
        uri_tokens = playlist_uri.split(':')

        check_results = len(uri_tokens) == 6 and \
            sanity_check(uri_tokens[2], self._valid_metrics) and \
            sanity_check(uri_tokens[3], self._valid_regions) and \
            sanity_check(uri_tokens[4], self._valid_windows) and \
            sanity_check_date(uri_tokens[5])
        if not check_results:
            raise ValueError(Fore.RED + "The chart URI doesn't follow the pattern "
                  "spotify:charts:metric:region:time_window:date" + Fore.RED)

    def __get_name(self):

        metrics,region_code,time_window,from_date = self.uri_tokens[-4:]
        l = [time_window, self._valid_regions[region_code], \
            ("Top 200" if metrics == "regional" else "Viral 50")]

        return ' '.join(l)

    def _Playlist__populate(self):
        pass

    def can_remove_tracks(self):
        return False
    
    def _Playlist__get_tracks(self):

        def get_chart_tracks(metrics, region, time_window, from_date):

            url = 'https://spotifycharts.com/' + metrics + "/" + \
                region + "/" + time_window + "/" + from_date + "/download"

            def request_url(url, msg):
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

            res = request_url(url, region + " " + metrics + " charts")
            if res is not None:
                csv_items = [to_ascii(r) for r in res.text.split("\n")] # enc_str(to_ascii(r)) doesn't work for me (python 3)

                # some charts starts with "Note that these figures are generated using a formula..."
                if not csv_items[0].startswith('Position'):
                    csv_items = islice(csv_items, 1, None) # so we skip one line
                reader = csv.DictReader(csv_items)
                return ["spotify:track:" + row["URL"].split("/")[-1]
                            for row in reader]
            else:
                return []

        track_uris = get_chart_tracks(self.uri_tokens[2], self.uri_tokens[3],
                                      self.uri_tokens[4], self.uri_tokens[5])

        track_objects = []

        for n in track_uris:
            this_track_object = self.session.get_link(n).as_track()
            track_objects.append(this_track_object)
        print('Loading chart playlist...')
        return track_objects

    def remove_tracks(self,tracks_to_remove):
        print('You cannot remove tracks from this playlist.')