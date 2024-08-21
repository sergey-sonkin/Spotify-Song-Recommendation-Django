from datetime import datetime, timedelta

from django.db import models

from songs.spotify.spotify_serializer import (
    SpotifyAlbum,
    SpotifyArtist,
    SpotifyTrack,
    SpotifyTrackFeatures,
)

SPOTIFY_UUID_LENGTH = 22
ARBITRARY_LENGTH = 50


class ArtistManager(models.Manager):
    def import_spotify_artist(
        self, spotify_artist: SpotifyArtist, is_updating: bool = True
    ):
        return self.create(
            id=spotify_artist.id,
            name=spotify_artist.name,
            is_updating=is_updating,
        )

    def get_or_import(self, spotify_artist: SpotifyArtist):
        try:
            return self.get(id=spotify_artist.id)
        except Artist.DoesNotExist:
            return self.import_spotify_artist(spotify_artist=spotify_artist)


class Artist(models.Model):
    id = models.CharField(primary_key=True, max_length=SPOTIFY_UUID_LENGTH)
    name = models.CharField(max_length=ARBITRARY_LENGTH)
    is_updating = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    most_recently_updated = models.DateTimeField(auto_now_add=True)
    objects = ArtistManager()

    @property
    def recently_updated(self):
        return self.most_recently_updated > datetime.now() - timedelta(hours=48)


class AlbumManager(models.Manager):
    def import_spotify_album(self, album: SpotifyAlbum):
        spotify_artists = album.base.artists
        db_artists: list[Artist] = [
            Artist.objects.get_or_import(spotify_artist=spotify_artist)  # type: ignore
            for spotify_artist in spotify_artists
        ]
        db_album = self.create(id=album.base.id, name=album.base.name)
        db_album.artists.set(db_artists)
        return db_album


class Album(models.Model):
    id = models.CharField(primary_key=True, max_length=SPOTIFY_UUID_LENGTH)
    name = models.CharField(max_length=ARBITRARY_LENGTH)
    artists = models.ManyToManyField(Artist)
    objects = AlbumManager()


class SongManager(models.Manager):
    def import_spotify_track(self, track: SpotifyTrack, album: Album):
        db_track = self.create(
            id=track.id,
            track_name=track.name,
            duration_ms=track.duration_ms,
            popularity=track.popularity,
            is_explicit=track.is_explicit,
            album=album,
        )
        db_artists: list[Artist] = [
            Artist.objects.get_or_import(spotify_artist=spotify_artist)  # type: ignore
            for spotify_artist in track.artists
        ]
        db_track.artists.set(db_artists)
        return db_track


class Song(models.Model):
    id = models.CharField(primary_key=True, max_length=SPOTIFY_UUID_LENGTH)
    track_name = models.CharField(max_length=ARBITRARY_LENGTH)
    duration_ms = models.IntegerField()
    release_date = models.DateField(auto_now_add=True)  # very temporary workaround
    popularity = models.IntegerField()
    is_explicit = models.BooleanField(default=True)
    artists = models.ManyToManyField(Artist)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)

    objects = SongManager()


class SongFeaturesManager(models.Manager):
    def get_song_features_by_artist(self, artist: SpotifyArtist):
        db_songs = Song.objects.filter(artists=artist)
        db_song_features = self.filter(song_id=db_songs)
        return db_song_features

    def import_song_features(self, features: SpotifyTrackFeatures):
        return self.create(
            id=features.id,
            acousticness=features.acousticness,
            danceability=features.danceability,
            energy=features.energy,
            instrumentalness=features.instrumentalness,
            key=features.key,
            liveness=features.liveness,
            loudness=features.loudness,
            mode=1 if features.is_major else 0,
            speechiness=features.speechiness,
            tempo=features.tempo,
            time_signature=features.time_signature,
            valence=features.valence,
        )


class SongFeatures(models.Model):
    id = models.CharField(primary_key=True, max_length=SPOTIFY_UUID_LENGTH)
    acousticness = models.FloatField()
    danceability = models.FloatField()
    energy = models.FloatField()
    instrumentalness = models.FloatField()
    key = models.FloatField()
    liveness = models.FloatField()
    loudness = models.FloatField()
    mode = models.IntegerField()
    speechiness = models.FloatField()
    tempo = models.FloatField()
    time_signature = models.FloatField()
    valence = models.FloatField()

    objects = SongFeaturesManager()
