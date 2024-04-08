from datetime import date


class SpotifyArtist:
    spotify_id: str
    name: str

    def __init__(self, spotify_id: str, name: str):
        self.spotify_id = spotify_id
        self.name = name

    @classmethod
    def from_dict(cls, artist_dict):
        return SpotifyArtist(spotify_id=artist_dict["id"], name=artist_dict["name"])


class SpotifyTrack:
    spotify_id: str
    name: str
    artists: list[SpotifyArtist]
    duration_ms: int
    popularity: int
    is_explicit: bool

    def __init__(
        self,
        spotify_id: str,
        name: str,
        artists: list[SpotifyArtist],
        duration_ms: int,
        is_explicit: bool,
    ):
        self.spotify_id = spotify_id
        self.name = name
        self.artists = artists
        self.duration_ms = duration_ms
        self.is_explicit = is_explicit

    @classmethod
    def from_dict(cls, track_dict):
        return SpotifyTrack(
            spotify_id=track_dict["id"],
            name=track_dict["name"],
            artists=[
                SpotifyArtist.from_dict(artist_dict)
                for artist_dict in track_dict["artists"]
            ],
            duration_ms=track_dict["duration_ms"],
            is_explicit=track_dict.get("is_explicit", False),
        )


class SpotifyTrackFeatures:
    spotify_id: str


class SpotifyAlbum:
    spotify_id: str
    name: str
    artists: list[SpotifyArtist]
    release_date: date

    def __init__(
        self,
        spotify_id: str,
        name: str,
        artists: list[SpotifyArtist],
        release_date: date,
    ):
        self.spotify_id = spotify_id
        self.name = name
        self.artists = artists
        self.release_date = release_date

    @classmethod
    def from_dict(cls, album_dict):
        return SpotifyAlbum(
            spotify_id=album_dict["id"],
            name=album_dict["name"],
            release_date=date.fromisoformat(album_dict["release_date"]),
            artists=[
                SpotifyArtist.from_dict(artist_dict)
                for artist_dict in album_dict["artists"]
            ],
        )
