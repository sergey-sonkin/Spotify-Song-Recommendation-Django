from django.db import models

SPOTIFY_UUID_LENGTH = 22


# Create your models here.
class Song(models.Model):
    id = models.CharField(primary_key=True, max_length=SPOTIFY_UUID_LENGTH)
    track_name = models.CharField()
    duration_ms = models.IntegerField()
    release_date = models.DateField()
    popularity = models.IntegerField()
    is_explicit = models.BooleanField(default=True)


class SongFeatures(models.Model):
    id = models.ForeignKey(Song, primary_key=True, on_delete=models.CASCADE)
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
    name = models.CharField()


class Artist(models.Model):
    id = models.CharField(primary_key=True, max_length=SPOTIFY_UUID_LENGTH)
    name = models.CharField()
