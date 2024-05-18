from django.http import HttpResponse

# Create your views here.


def detail(request, song_id):
    return HttpResponse(f"You're looking at song_id {song_id}")
