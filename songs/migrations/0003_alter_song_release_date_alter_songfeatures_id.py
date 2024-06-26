# Generated by Django 5.0.4 on 2024-05-05 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0002_album_artists_artist_date_added_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='release_date',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='songfeatures',
            name='id',
            field=models.CharField(max_length=22, primary_key=True, serialize=False),
        ),
    ]
