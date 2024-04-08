from rest_framework import serializers

from songs.models import Song, SongFeatures


class SongSerializer(serializers.Serializer):
    spotify_id = serializers.CharField(primary_key=True, max_length=50)
    track_name = serializers.CharField(max_length=50)
    question_text = serializers.CharField(max_length=200)
    duration_ms = serializers.IntegerField()
    release_date = serializers.DateField()
    popularity = serializers.IntegerField()
    is_explicit = serializers.BooleanField(default=True)
    date_published = serializers.DateTimeField()

    def create(self, validated_data):
        return Song.objects.create(**validated_data)
