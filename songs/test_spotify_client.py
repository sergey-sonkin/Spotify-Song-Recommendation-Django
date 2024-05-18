from django.test import TestCase
from mock import patch

from songs.spotify.spotify_client import SpotifyClient


class SpotifyClientTestCase(TestCase):
    @patch(
        target="songs.spotify.spotify_client.SpotifyClient.get_artist_albums",
        autospec=True,
    )
    def test_get_all_albums_calls(self, get_artist_albums_mock):
        client = SpotifyClient()

        with self.subTest(
            msg="Test get all albums called once when should be called once"
        ):
            get_artist_albums_mock.return_value = [], None
            client.get_all_artist_albums(artist_id="ARTIST_ID")
            assert get_artist_albums_mock.call_count == 1

        with self.subTest(
            msg="Test get all albums called once when should be called multiple times"
        ):
            get_artist_albums_mock.side_effect = [([], None), ([], True)]
            client.get_all_artist_albums(artist_id="ARTIST_ID")
            assert get_artist_albums_mock.call_count == 2

    # TODO: Change test to be mock patched
    def test_get_album_partials(self):
        client = SpotifyClient()
        albums = client.get_all_artist_albums("7dGJo4pcD2V6oG8kP0tJRR")
        partial_albums = client.get_album_partials(albums)
        self.assertEqual(len(partial_albums), 18)
        for partial_album in partial_albums:
            self.assertEqual(partial_album.next_page, None)

    # TODO: Change test to be mock patched
    def test_get_complete_album_from_partial(self):
        client = SpotifyClient()
        albums = client.get_all_artist_albums("2IN2VBkdXOBfoXJGrAUV1O")
        partial_albums = client.get_album_partials(albums)
        incomplete_album = partial_albums[1]
        complete_album = client.get_complete_album_from_partial(incomplete_album)

        self.assertEqual(len(complete_album.tracks), 125)
        self.assertEqual(len(partial_albums), 8)
