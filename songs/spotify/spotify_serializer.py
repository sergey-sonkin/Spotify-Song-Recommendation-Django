from datetime import date
from typing import Optional

from songs.spotify.spotify_client_constants import SpotifyAlbumType


class SpotifyArtist:
    id: str
    name: str

    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

    @classmethod
    def from_dict(cls, artist_dict):
        return SpotifyArtist(id=artist_dict["id"], name=artist_dict["name"])


class SpotifyTrack:
    id: str
    name: str
    artists: list[SpotifyArtist]
    duration_ms: int
    popularity: int
    is_explicit: bool

    def __init__(
        self,
        id: str,
        name: str,
        artists: list[SpotifyArtist],
        duration_ms: int,
        popularity: int,
        is_explicit: bool,
    ):
        self.id = id
        self.name = name
        self.artists = artists
        self.duration_ms = duration_ms
        self.popularity = popularity
        self.is_explicit = is_explicit

    @classmethod
    def from_dict(cls, track_dict):
        return SpotifyTrack(
            id=track_dict["id"],
            name=track_dict["name"],
            artists=[
                SpotifyArtist.from_dict(artist_dict)
                for artist_dict in track_dict["artists"]
            ],
            duration_ms=track_dict["duration_ms"],
            is_explicit=track_dict.get("is_explicit", False),
            popularity=track_dict.get("popularity", -1),
        )


pitch_class_dict = {
    -1: "Unknown",
    0: "C",
    1: "C#",
    2: "D",
    3: "D#",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "G#",
    9: "A",
    10: "A#",
    11: "B",
}


class SpotifyTrackFeatures:
    id: str
    acousticness: float
    danceability: float
    energy: float
    instrumentalness: float
    key: int
    liveness: float
    loudness: float
    is_major: bool
    speechiness: float
    tempo: float
    time_signature: int
    valence: float

    def __init__(
        self,
        id: str,
        acousticness: float,
        danceability: float,
        energy: float,
        instrumentalness: float,
        key: int,
        liveness: float,
        loudness: float,
        is_major: bool,
        speechiness: float,
        tempo: float,
        time_signature: int,
        valence: float,
    ):
        self.id = id
        self.acousticness = acousticness
        self.danceability = danceability
        self.energy = energy
        self.instrumentalness = instrumentalness
        self.key = key
        self.liveness = liveness
        self.loudness = loudness
        self.is_major = is_major
        self.speechiness = speechiness
        self.tempo = tempo
        self.time_signature = time_signature
        self.valence = valence

    @classmethod
    def from_dict(cls, features_dict):
        return SpotifyTrackFeatures(
            id=features_dict["id"],
            acousticness=features_dict["acousticness"],
            danceability=features_dict["danceability"],
            energy=features_dict["energy"],
            instrumentalness=features_dict["instrumentalness"],
            key=features_dict["key"],
            liveness=features_dict["liveness"],
            loudness=features_dict["loudness"],
            is_major=features_dict["mode"],
            speechiness=features_dict["speechiness"],
            tempo=features_dict["tempo"],
            time_signature=features_dict["time_signature"],
            valence=features_dict["valence"],
        )


class SpotifyAlbum:
    id: str
    name: str
    artists: list[SpotifyArtist]
    release_date: date
    album_type: SpotifyAlbumType

    def __init__(
        self,
        id: str,
        name: str,
        artists: list[SpotifyArtist],
        release_date: date,
        album_type: SpotifyAlbumType,
    ):
        self.id = id
        self.name = name
        self.artists = artists
        self.release_date = release_date
        self.album_type = album_type

    @classmethod
    def from_dict(cls, album_dict):
        return SpotifyAlbum(
            id=album_dict["id"],
            name=album_dict["name"],
            release_date=date.fromisoformat(album_dict["release_date"]),
            artists=[
                SpotifyArtist.from_dict(artist_dict)
                for artist_dict in album_dict["artists"]
            ],
            album_type=album_dict["type"],
        )


class SpotifyAlbumWithTracks:
    album: SpotifyAlbum
    tracks: list[SpotifyTrack]
    more_tracks: bool
