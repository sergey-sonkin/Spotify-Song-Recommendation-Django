import datetime
from operator import attrgetter
from typing import Optional

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
        db_artist = Artist.objects.import_spotify_artist(  # pyright: ignore
            spotify_artist
        )
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


def get_max_keys(input_dict: dict):
    max_value = max(input_dict.values())
    keys = [key for key, value in input_dict.items() if value == max_value]
    return keys, max_value


def group_albums(input_albums: list[SpotifyAlbum]) -> dict[str, list[SpotifyAlbum]]:
    names: dict[str, list[SpotifyAlbum]] = {}
    ## TODO: Create a better system than just filtering on album name
    for album in input_albums:
        names[album.name] = [*names.get(album.name, []), album]
    return names


def filter_on_explicit_values(
    spotify_albums: list[SpotifyAlbum],
) -> tuple[Optional[SpotifyAlbum], list[SpotifyAlbum]]:
    ids = [album.id for album in spotify_albums]
    tracks_dict = SpotifyClient().get_multiple_albums_tracks(album_ids=ids)
    explicit_albums = [
        album
        for album, tracks in zip(spotify_albums, tracks_dict.values())
        if tracks[0].is_explicit
    ]
    match len(explicit_albums):
        case 1:
            return explicit_albums[0], []
        case 0:
            return None, spotify_albums  ## if none are explicit, we just continue
        case _:
            return None, explicit_albums


def filter_duplicate_albums(spotify_albums: list[SpotifyAlbum]) -> list[SpotifyAlbum]:
    grouped_albums = group_albums(input_albums=spotify_albums)

    singleton_albums = []
    for album_name, duplicate_albums in grouped_albums.items():
        if len(duplicate_albums) == 1:
            singleton_albums.append(duplicate_albums[0])
            continue

        ## First - filter on explicit values
        one_explicit_album, remaining_albums_1 = filter_on_explicit_values(
            duplicate_albums
        )
        if one_explicit_album:
            singleton_albums.append(one_explicit_album)

        ## Second - filter on more recently released
        most_recent_album = max(remaining_albums_1, key=attrgetter("release_date"))
        most_recent_albums = [
            album
            for album in remaining_albums_1
            if album.release_date == most_recent_album.release_date
        ]
        if len(most_recent_albums) == 1:
            singleton_albums.append(most_recent_albums[0])
            continue
        remaining_albums_2 = most_recent_albums

        ## Third - filter on number of tracks (more is better)

    return singleton_albums


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
