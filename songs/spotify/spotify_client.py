import os

import requests

from songs.spotify.spotify_client_constants import *
from songs.spotify.spotify_serializer import SpotifyAlbum, SpotifyTrack


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

    def _get_request(
        self, endpoint: str, page: int, extra_request_params: dict = {}
    ) -> requests.Response:
        params = {
            "market": US_MARKET,
            "limit": MAX_LIMIT,
            "offset": page * MAX_LIMIT,
        }.update(extra_request_params)
        response = requests.get(url=endpoint, headers=self._get_header(), params=params)
        return response

    def _parse_response(self, response: requests.Response) -> dict[str, str]:
        response_json = response.json()
        if error := response_json.get("error"):
            return raise_correct_error(error.get("status"), error.get("message"))
        return response_json

    def get_parse_and_error_handle_request(
        self, endpoint: str, retries: int = 0, page: int = 0, **extra_request_params
    ):
        response = self._get_request(
            endpoint=endpoint, extra_request_params=extra_request_params, page=page
        )
        try:
            response_json = self._parse_response(response)
        except BadTokenError:
            self.token = self._get_token()
            return self.get_parse_and_error_handle_request(
                endpoint=endpoint,
                retries=retries + 1,
                page=page,
                **extra_request_params,
            )
        return response_json

    def get_artist_albums(
        self,
        artist_id: str,
        page: int = 0,
        retries: int = 0,
        include_groups: list[SpotifyAlbumType] = [SpotifyAlbumType.ALBUM],
    ) -> tuple[list[SpotifyAlbum], bool]:

        albums_endpoint = f"{BASE_URL}/artists/{artist_id}/albums/"
        include_groups_string = (
            ",".join(album_type.value for album_type in include_groups),
        )
        response_json = self.get_parse_and_error_handle_request(
            endpoint=albums_endpoint,
            retries=retries,
            page=page,
            include_groups=include_groups_string,
        )

        album_data = response_json["items"]
        albums = [SpotifyAlbum.from_dict(album_dict) for album_dict in album_data]

        return albums, bool(response_json.get("next", None))

    def get_all_artist_albums(self, artist_id: str, page: int = 0):
        albums, next = self.get_artist_albums(artist_id=artist_id, page=page)
        if not next:
            return albums
        return albums + self.get_all_artist_albums(artist_id=artist_id, page=page + 1)

    def get_album_tracks(
        self, album_id: str, counter: int = 0, retries: int = 0
    ) -> tuple[list[SpotifyTrack], bool]:
        def get_request():
            album_tracks_endpoint = f"{BASE_URL}/albums/{album_id}/tracks"
            params = {
                "market": US_MARKET,
                "limit": MAX_LIMIT,
                "offset": counter * MAX_LIMIT,
            }
            response = requests.get(
                url=album_tracks_endpoint, headers=self._get_header(), params=params
            )
            return response

        def check_response_for_errors(response_json):
            if error := response_json.get("error"):
                if error["status"] == 401 and retries == 0:
                    self.token = self._get_token()
                    return self.get_album_tracks(
                        album_id=album_id, counter=counter, retries=retries + 1
                    )
                else:
                    error_string = (
                        "Get albums error. Status: {status}, Message: {message}".format(
                            status=error["status"],
                            message=error["message"],
                        )
                    )
                    raise RuntimeError(error_string)

        response_json = get_request().json()
        check_response_for_errors(response_json)
        tracks = [
            SpotifyTrack.from_dict(track_dict) for track_dict in response_json["items"]
        ]
        return tracks, bool(response_json.get("next", None))

    def get_all_album_tracks(self, album_id, counter: int = 0) -> list[SpotifyTrack]:
        tracks, next = self.get_album_tracks(album_id=album_id, counter=counter)
        if not next:
            return tracks
        return tracks + self.get_all_album_tracks(
            album_id=album_id, counter=counter + 1
        )

    # def get_track_features(self, track_id):
    #     def get_request():
    #         album_tracks_endpoint = f"{BASE_URL}/albums/{album_id}/tracks"
    #         params = {
    #             "market": US_MARKET,
    #             "include_groups": "album",
    #             "limit": MAX_LIMIT,
    #             "offset": counter * MAX_LIMIT,
    #         }
    #         response = requests.get(
    #             url=album_tracks_endpoint, headers=self.get_header(), params=params
    #         )
    #         return response

    #     def check_response_for_errors(response_json):
    #         if error := response_json.get("error"):
    #             if error["status"] == 401 and retries == 0:
    #                 self.token = self.get_token()
    #                 return self.get_album_tracks(
    #                     album_id=album_id, counter=counter, retries=retries + 1
    #                 )
    #             else:
    #                 error_string = (
    #                     "Get albums error. Status: {status}, Message: {message}".format(
    #                         status=error["status"],
    #                         message=error["message"],
    #                     )
    #                 )
    #                 raise RuntimeError(error_string)
