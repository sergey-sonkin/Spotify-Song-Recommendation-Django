from django.test import TestCase

from songs.spotify.spotify import filter_duplicate_albums, import_artist_albums_songs, parse_album_name
from songs.spotify.spotify_client import SpotifyClient


class SpotifyClientTestCase(TestCase):
    def test_get_all_albums_calls(self):
        client = SpotifyClient()

        with self.subTest(msg="Filter Eminem albums"):
            eminem_albums = client.get_all_artist_albums("7dGJo4pcD2V6oG8kP0tJRR")
            filtered = filter_duplicate_albums(eminem_albums)
            self.assertEqual(
                len(eminem_albums),
                len(filtered) + 3,
                msg="2024/05/04 - 3 albums should get filtered",
            )

    def test_import_artists_albums(self):
        albums = import_artist_albums_songs(artist_id="7dGJo4pcD2V6oG8kP0tJRR")

    def test_parse_album_name(self):
        tests = {
            "Album name": "album name",
            "very long album (DeLuXE)": "very long album",
        }
        for input, output in tests.items():
            self.assertEqual(parse_album_name(input), output)
