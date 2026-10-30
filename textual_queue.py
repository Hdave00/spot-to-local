""" Download progress, calls functions from functions.py and batch_download.py as Workers """

import spotify_client, spotipy, yt_dlp

from rich.text import Text
from textual import work
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, LoadingIndicator, Static, ProgressBar

from functions import download_spotify_song


class QueueScreen(Screen):

    def compose(self):
        
        yield Vertical(
            Static("Downloading Songs...", id="status"),
            ProgressBar(total=len(self.app.selected_tracks), show_eta=True, id="overall"),
            DataTable(id="queue_table", cursor_type="row"),
        )
        yield Footer()


    def on_mount(self):

        # create table and 
        table = self.query_one("#queue_table", DataTable)
        table.add_column("Title", key="title")
        table.add_column("Artist", key="artist")
        table.add_column("Album", key="album")

        # from tracks.py, in the action_download func, we have the "selected_tracks" variable that is a set of playlists, unpack, enum and add metadata to each track
        for i, t in enumerate(self.app.selected_tracks):
            table.add_row(
                Text(t["track_name"]),
                Text(", ".join(t["artist_names"],)),
                Text("queued"),
                key=str(i),
            )

        self.run_queue() # NOTE make this function


    #