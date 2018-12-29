# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from colorama import Fore, Style
from spotify_ripper.utils import *
import os
import json
import codecs
import copy
import spotify


class Sync(object):

    def __init__(self, args, ripper):
        self.args = args
        self.ripper = ripper

    def sync_lib_path(self, playlist):
        args = self.args

        # get playlist_id

        uri_tokens = playlist.uri.split(':')
        if len(uri_tokens) != 5:
            #return None
            pass

        # lib path
        if args.settings is not None:
            lib_path = os.path.join(norm_path(args.settings), "Sync")
        else:
            lib_path = os.path.join(default_settings_dir(), "Sync")

        if not path_exists(lib_path):
            os.makedirs(enc_str(lib_path))

        #return os.path.join(lib_path, uri_tokens[4] + ".json")
        return os.path.join(lib_path, uri_tokens[-1] + ".json")

    def save_sync_library(self, playlist, lib):
        args = self.args
        lib_path = self.sync_lib_path(playlist)

        encoding = "ascii" if args.ascii else "utf-8"
        with codecs.open(enc_str(lib_path), 'w', encoding) as lib_file:
            lib_file.write(
                json.dumps(lib, ensure_ascii=args.ascii,
                           indent=4, separators=(',', ': ')))

    def load_sync_library(self, playlist):
        args = self.args
        lib_path = self.sync_lib_path(playlist)

        if path_exists(lib_path):
            encoding = "ascii" if args.ascii else "utf-8"
            with codecs.open(enc_str(lib_path), 'r', encoding) as lib_file:
                return json.loads(lib_file.read())
        else:
            return {}

    def sync_playlist(self, playlist):
        args = self.args
        #playlist.load(args.timeout)
        lib = self.load_sync_library(playlist)
        new_lib = {}

        print("Syncing playlist " + to_ascii(playlist.name))

        # TODO, que funcione con:
        # tracks = list(self.ripper.playlist.get_playlist_tracks())
        tracks = list(self.ripper.get_tracks_from_uri(playlist.uri))

        # create new lib
        #for idx, track in enumerate(playlist.tracks):
        for idx, track in enumerate(tracks):

            # ignore local tracks
            if track.is_local:
                continue

        # check what items are missing or renamed in the new_lib vs lib
        for uri, file_path in lib.items():
            enc_file_path = enc_str(file_path)

            if os.path.exists(enc_file_path):
                if uri in new_lib:
                    new_file_path = new_lib[uri]
                    if file_path != new_file_path:
                        print(Fore.YELLOW  + "Renaming file:" + Fore.RESET +
                              "\n  From: " + file_path + "\n  To:   " +
                              new_file_path)
                        os.rename(enc_file_path, enc_str(new_file_path))
                else:
                    print(Fore.YELLOW + "Removing file: " + Fore.RESET +
                          "\n " + file_path)
                    os.remove(enc_file_path)

        # save new lib
        self.save_sync_library(playlist, new_lib)
