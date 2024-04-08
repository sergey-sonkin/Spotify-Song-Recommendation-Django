import os
from typing import Optional

import requests

from songs.spotify.spotify_serializer import SpotifyAlbum, SpotifyTrack

MAX_LIMIT = 50
BASE_URL = "https://api.spotify.com/v1"
US_MARKET = "US"

BAD_OR_EXPIRED_TOKEN_CODE = 401

class SpotifyAPIError(Exception):
    pass

class GenericError(SpotifyAPIError):
    pass

class BadTokenError(SpotifyAPIError):
    pass

class BadOAuthRequestError(SpotifyAPIError): 
    pass

class RateLimitError(SpotifyAPIError):
    pass

def raise_correct_error(code,message):
    match code:
        case "401":
            raise BadTokenError(message)
        case "403":
            raise BadOAuthRequestError(message)
        case "429":
            raise RateLimitError(message)
        case _:
            raise GenericError(message)

class SpotifyClient:
    token = ""

    def __init__(self):
        self.token = self.get_token()

    def get_token(self) -> str:
        GET_TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"
        GET_TOKEN_HEADER = {"Content-Type": "application/x-www-form-urlencoded"}

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

        try:
            token = response.json()["access_token"]
        except:
            raise RuntimeError("Unable to get token")

        return token

    def get_header(self) -> dict[str, str]:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        else:
            raise RuntimeError("No token initialized")

    def get_request(
        self, endpoint: str, page: int, extra_request_params: dict = {}
    ) -> requests.Response:
        params = {
            "market": US_MARKET,
            "limit": MAX_LIMIT,
            "offset": page * MAX_LIMIT,
        }.update(extra_request_params)
        response = requests.get(url=endpoint, headers=self.get_header(), params=params)
        return response

    def parse_response(
        self, response: requests.Response
    ) -> dict[str,str]:
        response_json = response.json()
        if error := response_json.get("error"):
            return raise_correct_error(error.get("status"),error.get("message"))
        return response_json

    def get_parse_and_error_check_request(
        self, endpoint: str, retries: int = 0, page: int = 0, **extra_request_params
    ):
        response = self.get_request(
            endpoint=endpoint, extra_request_params=extra_request_params, page=page
        )
        try:
            self.parse_response(response)
        except:

        response_json, error_status, error_message = self.parse_response(response)

            

    def get_artist_albums(
        self, artist_id: str, counter: int = 0, retries: int = 0
    ) -> tuple[list[SpotifyAlbum], bool]:

        def get_request():
            albums_endpoint = f"{BASE_URL}/artists/{artist_id}/albums/"
            params = {
                "market": US_MARKET,
                "include_groups": "album",
                "limit": MAX_LIMIT,
                "offset": counter * MAX_LIMIT,
            }
            response = requests.get(
                url=albums_endpoint, headers=self.get_header(), params=params
            )
            return response

        def check_response_for_errors(response_json):
            if error := response_json.get("error"):
                if error["status"] == 401 and retries == 0:
                    self.token = self.get_token()
                    return self.get_artist_albums(
                        artist_id=artist_id, counter=counter, retries=retries + 1
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

        album_data = response_json["items"]
        albums = [SpotifyAlbum.from_dict(album_dict) for album_dict in album_data]

        return albums, bool(response_json.get("next", None))

    def get_all_artist_albums(self, artist_id: str, counter: int = 0):
        albums, next = self.get_artist_albums(artist_id=artist_id, counter=counter)
        if not next:
            return albums
        return albums + self.get_all_artist_albums(
            artist_id=artist_id, counter=counter + 1
        )

    def get_album_tracks(
        self, album_id: str, counter: int = 0, retries: int = 0
    ) -> tuple[list[SpotifyTrack], bool]:
        def get_request():
            album_tracks_endpoint = f"{BASE_URL}/albums/{album_id}/tracks"
            params = {
                "market": US_MARKET,
                "include_groups": "album",
                "limit": MAX_LIMIT,
                "offset": counter * MAX_LIMIT,
            }
            response = requests.get(
                url=album_tracks_endpoint, headers=self.get_header(), params=params
            )
            return response

        def check_response_for_errors(response_json):
            if error := response_json.get("error"):
                if error["status"] == 401 and retries == 0:
                    self.token = self.get_token()
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
