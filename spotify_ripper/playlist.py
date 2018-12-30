import spotipy.util as util
import spotipy.client
import os

import json

client_id = ''
client_secret = ''
redirect_uri = 'http://www.purple.com'

scope = 'playlist-modify-public playlist-modify-private playlist-read-collaborative'

# client_id = os.environ["SPOTIPY_CLIENT_ID"] 
# client_secret = os.environ["SPOTIPY_CLIENT_SECRET"]
# redirect_uri = os.environ["SPOTIPY_REDIRECT_URI"]


import abc

class Playlist(abc.ABC):

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

        self.__sp = spotify_object()

        self.__playlist = self.__populate()
        self.name = self.__playlist['name']
        self.tracks = self.__get_tracks()


    def owner_display_name(self):
        owner = self.__playlist['owner']
        if owner['display_name'] == None:
            return str(owner['id'])
        return str(owner['display_name'])

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
        self.__playlist = self._Playlist__sp.playlist(self.id)

    def _Playlist__populate(self):
        return self._Playlist__sp.playlist(self.id)

    def owner_display_name(self):
        return Playlist.owner_display_name(self)

    def _Playlist__get_tracks(self):
        print('Getting Results')
        results = self._Playlist__sp.playlist(self.id, fields="tracks")
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
        #self.owner = playlist_uri.split(':')[2]
        if self.owner_display_name() == \
                        self.session.user.canonical_name:
            return True
        return False

    def remove_tracks(self,track_ids): #testear
        results = self._Playlist__sp.user_playlist_remove_all_occurrences_of_tracks(self.id, track_ids)


class Album(Playlist): # an_album_playlist

    def __init__(self,s,playlist_uri):
        super().__init__(s,playlist_uri)
        self.__playlist = self._Playlist__sp.album(self.id)

    def _Playlist__populate(self):
        return self._Playlist__sp.album(self.id)

    def can_remove_tracks(self):
        return False

    def _Playlist__get_tracks(self):
        print('Getting Results')
        print(self.name)
        results = self._Playlist__sp.album_tracks(self.id)

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

