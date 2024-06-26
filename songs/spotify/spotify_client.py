import os
from itertools import batched
from typing import Optional

import requests

from songs.spotify.spotify_client_constants import (
    BASE_URL,
    GET_TOKEN_ENDPOINT,
    GET_TOKEN_HEADER,
    MAX_LIMIT,
    US_MARKET,
    BadTokenError,
    SpotifyAlbumType,
    print_request_and_response,
    raise_correct_error,
)
from songs.spotify.spotify_serializer import (
    SpotifyAlbum,
    SpotifyAlbumBase,
    SpotifyAlbumPartial,
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
        except requests.JSONDecodeError:
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

    # This endpoint does not return tracks
    # https://developer.spotify.com/documentation/web-api/reference/get-an-artists-albums
    # If we want these to have tracks we have to get them later
    # It makes sense for us to "initialize" these albums
    def get_artist_albums(
        self,
        artist_id: str,
        page: int = 0,
        retries: int = 0,
        include_groups: list[SpotifyAlbumType] = [SpotifyAlbumType.ALBUM],
    ) -> tuple[list[SpotifyAlbumBase], bool]:
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
        albums = [SpotifyAlbumBase.from_dict(album_dict) for album_dict in album_data]
        has_next = bool(response_json.get("next", None))

        return albums, has_next

    def get_all_artist_albums(
        self,
        artist_id: str,
        page: int = 0,
        include_groups: list[SpotifyAlbumType] = [SpotifyAlbumType.ALBUM],
    ) -> list[SpotifyAlbumBase]:
        albums, next = self.get_artist_albums(
            artist_id=artist_id, page=page, include_groups=include_groups
        )
        if not next:
            return albums
        return albums + self.get_all_artist_albums(
            artist_id=artist_id, page=page + 1, include_groups=include_groups
        )

    def __get_album_partials(
        self, albums_tuple: tuple[SpotifyAlbumBase, ...]
    ) -> list[SpotifyAlbumPartial]:
        album_ids_string = ",".join([album.id for album in albums_tuple])
        albums_endpoint = f"{BASE_URL}/albums?ids={album_ids_string}"
        params = {"market": US_MARKET}
        response_json: dict = self.get_parse_and_error_handle_request(
            endpoint=albums_endpoint, params=params
        )
        album_objects_list: list[dict] = response_json["albums"]
        albums = [
            SpotifyAlbumPartial(
                base=spotify_album,
                tracks=[
                    SpotifyTrack.from_dict(track_dict)
                    for track_dict in album_object["tracks"]["items"]
                ],
                next_page=album_object["tracks"]["next"] or None,
                total_tracks=album_object["total_tracks"],
            )
            for spotify_album, album_object in zip(albums_tuple, album_objects_list)
        ]
        return albums

    def get_album_partials(
        self, albums_list: list[SpotifyAlbumBase]
    ) -> list[SpotifyAlbumPartial]:
        batched_albums = batched(albums_list, 20)
        ret = []
        for albums_batch in batched_albums:
            ret += self.__get_album_partials(albums_tuple=albums_batch)
        return ret

    # https://developer.spotify.com/documentation/web-api/reference/get-an-albums-tracks
    def get_album_tracks(
        self, album_id: str, page: int = 0, retries: int = 0
    ) -> tuple[list[SpotifyTrack], Optional[str]]:
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
        has_next = response_json.get("next", None)

        return tracks, has_next

    def get_all_album_tracks(self, album_id: str, page: int = 0) -> list[SpotifyTrack]:
        tracks, has_next = self.get_album_tracks(album_id=album_id, page=page)
        if not has_next:
            return tracks
        return tracks + self.get_all_album_tracks(album_id=album_id, page=page + 1)

    def get_multiple_albums_tracks(
        self, album_ids: list[str]
    ) -> dict[str, list[SpotifyTrack]]:
        return {album_id: self.get_all_album_tracks(album_id) for album_id in album_ids}

    def _get_track_features(self, track_id: str):
        track_features_endpoint = f"{BASE_URL}/audio-features/{track_id}"

        response_json = self.get_parse_and_error_handle_request(
            endpoint=track_features_endpoint, retries=0, params={}
        )

        return SpotifyTrackFeatures.from_dict(features_dict=response_json)

    def get_up_to_one_hundred_tracks_features(
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
        num_pages = max(len(track_ids) // 100, 1)
        ret = []
        for page_number in range(num_pages):
            tracks_ids_subset = track_ids[100 * page_number : 100 * (page_number + 1)]
            ret += self.get_up_to_one_hundred_tracks_features(tracks_ids_subset)
        return ret

    def get_complete_album_from_partial(
        self, album_partial: SpotifyAlbumPartial
    ) -> SpotifyAlbum:
        while (next_page := album_partial.next_page) is not None:
            response_json = self.get_parse_and_error_handle_request(
                endpoint=next_page, retries=0, params={"limit": MAX_LIMIT}
            )
            tracks = [
                SpotifyTrack.from_dict(track_dict)
                for track_dict in response_json["items"]
            ]
            album_partial.tracks += tracks
            album_partial.next_page = response_json.get("next", None)

        return SpotifyAlbum(album=album_partial.base, tracks=album_partial.tracks)
