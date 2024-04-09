from songs.models import Artist
from songs.spotify.spotify_client import SpotifyClient


def step_one(artist_id: str):
    try:
        artist = Artist.objects.get(id=artist_id)
    except Artist.DoesNotExist:
        print("uh oh")

    print("hiii")


def get_import_artist_tracks(artist_id):
    return
    ## Step 1: Check if artist already exists and recent, otherwise get artist
    ## Step 2: Get artists albums
    ## Step 3: Filter duplicate albums
    ## Step 4: From each album, import songs
    ## Step 5: For each song, get song features
    ## Step 6: Get single albums
    ## Step 7: Filter duplicate singles
    ##
    ## Step 8: Retrieve singes' features
    return
