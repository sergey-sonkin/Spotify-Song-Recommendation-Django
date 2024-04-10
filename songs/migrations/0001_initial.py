# Generated by Django 5.0.4 on 2024-04-09 21:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Album",
            fields=[
                (
                    "id",
                    models.CharField(max_length=22, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="Artist",
            fields=[
                (
                    "id",
                    models.CharField(max_length=22, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=50)),
                ("is_updating", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Song",
            fields=[
                (
                    "id",
                    models.CharField(max_length=22, primary_key=True, serialize=False),
                ),
                ("track_name", models.CharField(max_length=50)),
                ("duration_ms", models.IntegerField()),
                ("release_date", models.DateField()),
                ("popularity", models.IntegerField()),
                ("is_explicit", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="SongFeatures",
            fields=[
                (
                    "id",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="songs.song",
                    ),
                ),
                ("acousticness", models.FloatField()),
                ("danceability", models.FloatField()),
                ("energy", models.FloatField()),
                ("instrumentalness", models.FloatField()),
                ("key", models.FloatField()),
                ("liveness", models.FloatField()),
                ("loudness", models.FloatField()),
                ("mode", models.IntegerField()),
                ("speechiness", models.FloatField()),
                ("tempo", models.FloatField()),
                ("time_signature", models.FloatField()),
                ("valence", models.FloatField()),
            ],
        ),
    ]
