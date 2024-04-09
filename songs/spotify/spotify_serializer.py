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
    spotify_id: str
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
        spotify_id: str,
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
        self.spotify_id = spotify_id
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
            spotify_id=features_dict["id"],
            acousticness=features_dict["acousticness"],
            danceability=features_dict["danceability"],
            energy=features_dict["energy"],
            instrumentalness=features_dict["instrumentalness"],
            key=features_dict["key"],
            liveness=features_dict["liveness"],
            loudness=features_dict["loudness"],
            is_major=features_dict["is_major"],
            speechiness=features_dict["speechiness"],
            tempo=features_dict["tempo"],
            time_signature=features_dict["time_signature"],
            valence=features_dict["valence"],
        )


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
