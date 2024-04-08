from django.db import models


# Create your models here.
class Song(models.Model):
    spotify_id = models.CharField(primary_key=True, max_length=50)
    track_name = models.CharField(max_length=50)
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
    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=50)


class Artist(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=50)
