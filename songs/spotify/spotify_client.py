import os

import requests

from songs.spotify.spotify_client_constants import *
from songs.spotify.spotify_serializer import (
    SpotifyAlbum,
    SpotifyArtist,
    SpotifyTrack,
    SpotifyTrackFeatures,
)


class SpotifyClient:
    token = ""
    debug = False

    def __init__(self, debug=False):
        self.debug = debug
        self._refresh_token()

    def _refresh_token(self):
        self.token = self._get_token()

    def _get_token(self) -> str:
        client_id = str(os.getenv("SPOTIFY_CLIENT_ID"))
        client_secret = str(os.getenv("SPOTIFY_CLIENT_SECRET"))
        data = (
            "grant_type=client_credentials&client_id="
            + client_id
            + "&client_secret="
            + client_secret
        )

        response = requests.post(
            url=GET_TOKEN_ENDPOINT, headers=GET_TOKEN_HEADER, data=data
        )
        if self.debug:
            print(response.json())

        try:
            return response.json()["access_token"]
        except:
            raise RuntimeError("Unable to get token")

    def _get_header(self) -> dict[str, str]:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        else:
            raise RuntimeError("No token initialized")

    def _get_request(self, endpoint: str, params: dict) -> requests.Response:
        response = requests.get(url=endpoint, headers=self._get_header(), params=params)
        if self.debug:
            print_request_and_response(response)
        return response

    def _parse_response(self, response: requests.Response) -> dict[str, str]:
        response_json = response.json()
        if error := response_json.get("error"):
            return raise_correct_error(error.get("status"), error.get("message"))
        return response_json

    def get_parse_and_error_handle_request(
        self, endpoint: str, params: dict = {}, retries: int = 0
    ):
        response = self._get_request(endpoint=endpoint, params=params)
        try:
            return self._parse_response(response)
        except BadTokenError:
            self.token = self._get_token()
            return self.get_parse_and_error_handle_request(
                endpoint=endpoint,
                params=params,
                retries=retries + 1,
            )

    def get_artist(self, artist_id: str) -> SpotifyArtist:
        artists_endpoint = f"{BASE_URL}/artists/{artist_id}"
        response_json = self.get_parse_and_error_handle_request(
            endpoint=artists_endpoint
        )
        return SpotifyArtist.from_dict(response_json)

    def get_artist_albums(
        self,
        artist_id: str,
        page: int = 0,
        retries: int = 0,
        include_groups: list[SpotifyAlbumType] = [SpotifyAlbumType.ALBUM],
    ) -> tuple[list[SpotifyAlbum], bool]:

        albums_endpoint = f"{BASE_URL}/artists/{artist_id}/albums/"
        include_groups_string = ",".join(
            album_type.value for album_type in include_groups
        )
        params = {
            "market": US_MARKET,
            "limit": MAX_LIMIT,
            "offset": page * MAX_LIMIT,
            "include_groups": include_groups_string,
        }

        response_json = self.get_parse_and_error_handle_request(
            endpoint=albums_endpoint, retries=retries, params=params
        )

        album_data = response_json["items"]
        albums = [SpotifyAlbum.from_dict(album_dict) for album_dict in album_data]
        has_next = bool(response_json.get("next", None))

        return albums, has_next

    def get_all_artist_albums(
        self,
        artist_id: str,
        page: int = 0,
        include_groups: list[SpotifyAlbumType] = [SpotifyAlbumType.ALBUM],
    ):
        albums, next = self.get_artist_albums(
            artist_id=artist_id, page=page, include_groups=include_groups
        )
        if not next:
            return albums
        return albums + self.get_all_artist_albums(
            artist_id=artist_id, page=page + 1, include_groups=include_groups
        )

    def get_album_tracks(
        self, album_id: str, page: int = 0, retries: int = 0
    ) -> tuple[list[SpotifyTrack], bool]:
        album_tracks_endpoint = f"{BASE_URL}/albums/{album_id}/tracks"

        params = {
            "market": US_MARKET,
            "limit": MAX_LIMIT,
            "offset": page * MAX_LIMIT,
        }
        response_json = self.get_parse_and_error_handle_request(
            endpoint=album_tracks_endpoint, params=params, retries=retries
        )

        tracks = [
            SpotifyTrack.from_dict(track_dict) for track_dict in response_json["items"]
        ]
        has_next = bool(response_json.get("next", None))

        return tracks, has_next

    def get_all_album_tracks(self, album_id: str, page: int = 0) -> list[SpotifyTrack]:
        tracks, next = self.get_album_tracks(album_id=album_id, page=page)
        if not next:
            return tracks
        return tracks + self.get_all_album_tracks(album_id=album_id, page=page + 1)

    def get_multiple_albums_tracks(
        self, album_ids: list[str]
    ) -> dict[str, list[SpotifyTrack]]:
        return {album_id: self.get_all_album_tracks(album_id) for album_id in album_ids}

    def get_track_features(self, track_id: str):
        track_features_endpoint = f"{BASE_URL}/audio-features/{track_id}"

        response_json = self.get_parse_and_error_handle_request(
            endpoint=track_features_endpoint, retries=0, params={}
        )

        return SpotifyTrackFeatures.from_dict(features_dict=response_json)

    def _get_max_track_features(
        self, track_ids: list[str]
    ) -> list[SpotifyTrackFeatures]:
        track_ids_string = ",".join(track_ids)
        tracks_features_endpoint = f"{BASE_URL}/audio-features/?ids={track_ids_string}"
        response_json = self.get_parse_and_error_handle_request(
            endpoint=tracks_features_endpoint, retries=0, params={}
        )
        return [
            SpotifyTrackFeatures.from_dict(features_dict=track_feature_dict)
            for track_feature_dict in response_json["audio_features"]
        ]

    ## To test:
    ## - Assert called right number of times with 1 track_id, 100 track_ids, 501 track_ids
    ## - Assert on subsequent loops correct IDs are still being called
    def get_multiple_track_features(
        self, track_ids: list[str]
    ) -> list[SpotifyTrackFeatures]:
        MAX_TRACKS = 100
        pages = max(len(track_ids) // MAX_TRACKS, 1)
        ret = []
        for page_number in range(pages):
            tracks_ids_subset = track_ids[100 * page_number : 100 * (page_number + 1)]
            features = self._get_max_track_features(tracks_ids_subset)
            ret += features
        return ret
