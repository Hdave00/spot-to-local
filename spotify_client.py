# thin wrapper: list_playlists(), get_tracks(playlist_id) this replaces the need for users to go to Exportify manually

"""Thin wrapper over spotipy calls. Spotify metadata retrieval, paginated. This is the piece that replaces
Exportify but has similar underlying endpoints, called directly instead of via a browser tool that outputs a CSV."""

from spotipy import Spotify

# function to get playlists of the user
def list_playlists(sp: Spotify) -> list[dict]:

    """ Returns every playlist the logged in user owns or follows """

    # store the playlists in a list, and save the results by using spotipy to get all current playlists and make a limit of 50
    playlists = []
    results = sp.current_user_playlists(limit=50)

    # if results exist, while iterating over them, append the k:v pairs dict to the results list of dicts
    while results:
        for item in results["items"]:
            playlists.append({
                "id": item["id"],
                "name": item["name"],
                "owner": item["owner"]["display_name"],
                "track_count": item["tracks"]["total"],
                "image_url": item["images"][0]["url"] if item["images"] else None,
            })

        # set results as the next bunch of items else none
        results = sp.next(results) if results["next"] else None

    return playlists


def get_tracks(sp: Spotify, playlist_id: str) -> list[dict]:

    """ Returns all tracks in a playlist, normalized to the same shape
    download_spotify_song() in functions.py expects. """

    # same as before, store a list of tracks to be returned at the end, store results with their id and limit to 100 at a time
    tracks = []
    results = sp.playlist_tracks(playlist_id, limit=100)

    # now, for each item in results method, set track to the item and if no track items, continue on
    while results:
        for item in results["item"]:
            track = item.get("track")

            if track is None:
                continue # local files / removed tracks show up as None

            # now, get the tracks in an album, to ultimately append to the tracks list of dicts
            album = track.get("album", {})

            tracks.append({
                "track_name": track["name"],
                "artist_names": [a["name"] for a in track["artists"]],
                "album_name": album.get("name"),
                "album_artist_names": [a["name"] for a in album.get("artists", [])],
                "album_release_date": album.get("release_date"),
                "album_image_url": album["images"][0]["url"] if album.get("images") else None,
                "track_number": track.get("track_number"),
                "disc_number": track.get("disc_number"),
                "duration_ms": track.get("duration_ms"),
                "spotify_uri": track.get("uri"),
                "isrc": track.get("external_ids", {}).get("isrc"),

            })

        results = sp.next(results) if results["next"] else None

    return tracks