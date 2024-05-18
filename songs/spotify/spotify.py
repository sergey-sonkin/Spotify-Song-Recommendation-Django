import logging
from operator import attrgetter
from typing import Optional

from songs.models import Album, Artist, Song, SongFeatures
from songs.spotify.spotify_client import SpotifyClient
from songs.spotify.spotify_client_constants import SpotifyAlbumType
from songs.spotify.spotify_serializer import (
    SpotifyAlbumBase,
    SpotifyAlbumPartial,
)

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


def parse_album_name(album_name: str) -> str:
    return (
        album_name.strip()
        .lower()
        .removesuffix(" (deluxe)")
        .removesuffix(" (expanded edition)")
        .removesuffix(" deluxe edition")
    )


def group_albums(
    input_albums: list[SpotifyAlbumPartial],
) -> dict[str, list[SpotifyAlbumPartial]]:
    names: dict[str, list[SpotifyAlbumPartial]] = {}
    for album in input_albums:
        parsed_name = parse_album_name(album_name=album.base.name)
        names[parsed_name] = [*names.get(parsed_name, []), album]
    return names


def filter_on_explicit_values(
    spotify_albums: list[SpotifyAlbumPartial],
) -> tuple[Optional[SpotifyAlbumPartial], list[SpotifyAlbumPartial]]:
    id_tracks_tuple_list = [(album, album.tracks) for album in spotify_albums]
    explicit_albums = [
        album for album, tracks in id_tracks_tuple_list if tracks[0].is_explicit
    ]

    match len(explicit_albums):
        case 1:
            return explicit_albums[0], []
        case 0:
            return None, spotify_albums  # if none are explicit, just continue
        case _:
            return None, explicit_albums


def filter_duplicate_albums(
    spotify_albums: list[SpotifyAlbumBase],
) -> list[SpotifyAlbumPartial]:
    spotify_album_partials = SpotifyClient().get_album_partials(
        albums_list=spotify_albums
    )
    grouped_albums = group_albums(input_albums=spotify_album_partials)
    singleton_albums: list[SpotifyAlbumPartial] = []

    for album_name, duplicate_albums in grouped_albums.items():
        if len(duplicate_albums) == 1:
            singleton_albums.append(duplicate_albums[0])
            continue

        # First - filter on explicit values
        one_explicit_album, remaining_albums_1 = filter_on_explicit_values(
            duplicate_albums
        )
        if one_explicit_album:
            singleton_albums.append(one_explicit_album)
            continue

        # Second - filter on more recently released
        most_recent_album = max(
            [album.base for album in remaining_albums_1], key=attrgetter("release_date")
        )
        most_recent_albums = [
            album
            for album in remaining_albums_1
            if album.base.release_date == most_recent_album.release_date
        ]
        if len(most_recent_albums) == 1:
            singleton_albums.append(most_recent_albums[0])
            continue
        remaining_albums_2 = most_recent_albums

        # Third - filter on number of tracks (more is better)
        album_lengths_tuple = [
            (album, album.total_tracks) for album in remaining_albums_2
        ]
        max_len = max(album_lengths_tuple, key=lambda x: x[1])[1]
        max_length_albums = [
            album for album, length in album_lengths_tuple if length == max_len
        ]
        if True:
            singleton_albums.append(max_length_albums[0])
            continue

    diff = len(spotify_albums) - len(singleton_albums)
    logging.info(f"We removed {diff} albums")
    return singleton_albums


def import_artist_unique_albums(artist_id: str) -> list[Album]:
    client = SpotifyClient()
    all_spotify_albums = client.get_all_artist_albums(
        artist_id=artist_id, include_groups=[SpotifyAlbumType.ALBUM]
    )
    album_partials_to_import = filter_duplicate_albums(all_spotify_albums)
    albums_to_import = [
        client.get_complete_album_from_partial(album_partial=partial)
        for partial in album_partials_to_import
    ]
    db_albums = [
        Album.objects.import_spotify_album(album=spotify_album)  # type: ignore
        for spotify_album in albums_to_import
    ]
    return db_albums


def import_album_songs(db_albums: list[Album]):
    album_ids = [db_album.id for db_album in db_albums]
    spotify_tracks_dict = SpotifyClient().get_multiple_albums_tracks(album_ids)
    ret = []
    for db_album, spotify_tracks_list in zip(db_albums, spotify_tracks_dict.values()):
        for spotify_track in spotify_tracks_list:
            song = Song.objects.import_spotify_track(  # type: ignore
                track=spotify_track, album=db_album
            )
            ret.append(song)
    return ret


def import_song_features(db_songs: list[Song]) -> list[SongFeatures]:
    song_ids = [song.id for song in db_songs]
    song_features = SpotifyClient().get_multiple_track_features(track_ids=song_ids)
    return [
        SongFeatures.objects.import_song_features(song_feature)  # type: ignore
        for song_feature in song_features
    ]


# Steps for new artist
# Get list of all albums from Spotify
# Get list of all tracks for those albums from Spotify
# First resolve albums - which need to go in
# Then go through singles - resolve which need to go in
# Then get song features for all tracks
def import_artist_albums_songs(artist_id):
    db_albums = import_artist_unique_albums(artist_id)
    db_songs = import_album_songs(db_albums)
    db_song_features = import_song_features(db_songs)

    return db_song_features


def get_artist_track_features(artist_id: str) -> list[SongFeatures]:
    db_artist, is_existing = get_or_create_artist(artist_id=artist_id)

    # If artist was existing and was recently updated, we can just grab their tracks
    if is_existing and db_artist.recently_updated:
        albums = Album.objects.filter(artist_id=artist_id)
        track_ids = Song.objects.filter(album=albums).values_list("id")
        features = SongFeatures.objects.filter(id=track_ids)
        return list(features)

    else:
        return import_artist_albums_songs(artist_id)

    ## If artist was not existing, we can just grab their tracks


# def get_non_existing_artist_track_features(artist_id: str) -> list[SongFeatures]:
#     albums = client.get_all_artist_albums(artist_id=artist_id)


## Steps for returning artist
## Get current list of albums
## Get total list of albums
## Find albums that need to be updated
## If list is zero, return
## Within these albums, find duplicates. Resolve whether we should keep old or new
## If

## Get all new songs across those albums
## For each of those songs, find duplicates
