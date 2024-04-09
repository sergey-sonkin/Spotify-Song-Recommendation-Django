from enum import Enum

from requests import Response

MAX_LIMIT = 50
BASE_URL = "https://api.spotify.com/v1"
US_MARKET = "US"

BAD_OR_EXPIRED_TOKEN_CODE = 401

GET_TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"
GET_TOKEN_HEADER = {"Content-Type": "application/x-www-form-urlencoded"}


class SpotifyAlbumType(Enum):
    ALBUM = "album"
    APPEARS_ON = "appears_on"
    COMPILATION = "compilation"
    SINGLE = "single"


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


def raise_correct_error(code, message):
    match code:
        case "401":
            raise BadTokenError(message)
        case "403":
            raise BadOAuthRequestError(message)
        case "429":
            raise RateLimitError(message)
        case _:
            raise GenericError(message)


def print_request_and_response(response: Response):
    print("REQUEST:")
    print("-------------------------")
    print(response.request.__dict__)
    print("RESPONSE:")
    print("-------------------------")
    print(response.json())
