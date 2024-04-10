from django.db import models

from songs.spotify.spotify_serializer import SpotifyArtist, SpotifyTrack

SPOTIFY_UUID_LENGTH = 22
ARBITRARY_LENGTH = 50


class Song(models.Model):
    id = models.CharField(primary_key=True, max_length=SPOTIFY_UUID_LENGTH)
    track_name = models.CharField(max_length=ARBITRARY_LENGTH)
    duration_ms = models.IntegerField()
    release_date = models.DateField()
    popularity = models.IntegerField()
    is_explicit = models.BooleanField(default=True)


# Create your models here.
class SongManager(models.Manager):
    def create_song(self, track: SpotifyTrack) -> Song:
        song = self.create(id=track.spotify_id, track_name=track.name)
        return song


class SongFeatures(models.Model):
    id = models.OneToOneField(Song, primary_key=True, on_delete=models.CASCADE)
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


class Album(models.Model):
    id = models.CharField(primary_key=True, max_length=SPOTIFY_UUID_LENGTH)
    name = models.CharField(max_length=ARBITRARY_LENGTH)


class Artist(models.Model):
    id = models.CharField(primary_key=True, max_length=SPOTIFY_UUID_LENGTH)
    name = models.CharField(max_length=ARBITRARY_LENGTH)
    is_updating = models.BooleanField(default=False)


class ArtistManager(models.Manager):
    def create_from_spotifyartist(self, spotify_artist: SpotifyArtist) -> Artist:
        return Artist(id=spotify_artist.spotify_id, name=spotify_artist.name)
