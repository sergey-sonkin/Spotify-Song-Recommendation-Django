from django.test import TestCase
from mock import patch

from songs.spotify.spotify import *


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
        albums = import_artist_albums(artist_id="7dGJo4pcD2V6oG8kP0tJRR")
