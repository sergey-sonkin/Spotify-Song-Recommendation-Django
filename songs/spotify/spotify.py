from songs.models import Album, Artist, Song, SongFeatures
from songs.spotify.spotify_client import SpotifyClient
from songs.spotify.spotify_client_constants import SpotifyAlbumType
from songs.spotify.spotify_serializer import SpotifyAlbum

client = SpotifyClient()


def get_or_create_artist(artist_id: str) -> tuple[Artist, bool]:
    try:
        return Artist.objects.get(id=artist_id), True
    except Artist.DoesNotExist:
        spotify_artist = client.get_artist(artist_id=artist_id)
        db_artist = Artist.objects.import_spotify_artist(
            spotify_artist
        )  # pyright: ignore
        db_artist.save()
        return db_artist, False


def get_artists_albums(db_artist: Artist):
    if db_artist.recently_updated:
        return
    db_album_ids = Album.objects.filter(artists=db_artist.id).values_list("id")
    spotify_albums = client.get_all_artist_albums(artist_id=db_artist.id)
    for spotify_album in spotify_albums:
        if spotify_album.id in db_album_ids:
            continue


def filter_duplicate_albums(spotify_albums: list[SpotifyAlbum]) -> list[SpotifyAlbum]:
    names: dict[str, list[SpotifyAlbum]] = {}

    ## TODO: Create a better system than just filtering on album name
    for album in spotify_albums:
        names[album.name] = [*names.get(album.name, []), album]

    singleton_albums = []
    for album_name, duplicate_albums in names.items():
        if len(duplicate_albums) == 1:
            singleton_albums.append(duplicate_albums[0])
            continue
        ## First - filter on explicit values
        ids = [album.id for album in duplicate_albums]
        tracks_dict = SpotifyClient().get_multiple_albums_tracks(album_ids=ids)
        explicit_album_names = [
            album_name
            for album_name, tracks in tracks_dict.items()
            if tracks[0].is_explicit
        ]
        if len(explicit_album_names) == 1:
            singleton_albums.append(explicit_album_names[0])
            continue

    return names


## Steps for new artist
## Get list of all albums from Spotify
## Get list of all tracks for those albums from Spotify
## First resolve albums - which need to go in
## Then go through singles - resolve which need to go in
## Then get song features for all tracks
def import_new_artist_albums(db_artist: Artist):
    all_spotify_albums = client.get_all_artist_albums(
        artist_id=db_artist.id, include_groups=[SpotifyAlbumType.ALBUM]
    )
    db_albums = [
        Album.objects.import_spotify_album(album=spotify_album)  # pyright: ignore
        for spotify_album in all_spotify_albums
    ]
    return db_albums


def get_artist_track_features(artist_id: str) -> list[SongFeatures]:
    db_artist, is_existing = get_or_create_artist(artist_id=artist_id)

    ## If artist was existing and was recently updated, we can just grab their tracks
    if is_existing and db_artist.recently_updated:
        db_song_ids = Song.objects.filter(artist_id=artist_id).values_list("id")
        db_song_features = SongFeatures.objects.filter(pk__in=db_song_ids)
        ret = list(db_song_features)
        return ret
    elif is_existing:
        raise Exception("Todo!")

    return import_new_artist(artist_id)

    ## If artist was not existing, we can just grab their tracks


def get_non_existing_artist_track_features(artist_id: str) -> list[SongFeatures]:
    albums = client.get_all_artist_albums(artist_id=artist_id)


## Steps for returning artist
## Get current list of albums
## Get total list of albums
## Find albums that need to be updated
## If list is zero, return
## Within these albums, find duplicates. Resolve whether we should keep old or new
## If

## Get all new songs across those albums
## For each of those songs, find duplicates
