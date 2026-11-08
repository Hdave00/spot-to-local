""" Playlists screen that lists the logged-in user's playlists in a DataTable. Selecting one stores its id on the app and advances to tracks.py. """

from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Static, DataTable, LoadingIndicator
from textual.binding import Binding
from textual import work
from rich.text import Text

import spotify_client

# playlist screen class within which all functions to fetch playlists, render the datatable, map each table row to its playlist_id, on row selection stash the chosen...
# playlist_id on app and switch to tracks.py

class PlaylistsScreen(Screen):

    CSS = """
        PlaylistsScreen {
            align: center middle;
        }
        #status {
            text-align: center;
            margin: 1;
        }
        
    """
    # if playlist changes between sessions dont restart app
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        Binding("space", "toggle_playlist", "Toggle"),
        Binding("a", "select_all", "All"),
        Binding("n", "select_none", "None"),
        Binding("d", "download_selected", "Download selected"),
    ]

    # new init for keeping track and mapping playlist names to a dict and also mapping checked to a set
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        # id -> name
        self.playlist_names: dict[str, str] = {}
        # ids of checked playlists
        self.checked: set[str] = set()


    # create prototypes for showing users playlists, show a loading indicatior and a table populated with data rows
    def compose(self):
        yield Vertical(
            Static("Your Playlists", id="status"),
            LoadingIndicator(id="spinner"),
            DataTable(id="playlist_table", cursor_type="row"),
        )


    # then render the table with relevant details, we also ned keyed columns so a single cell can be updated
    def on_mount(self):
        table = self.query_one("#playlist_table", DataTable)
        table.add_column("", key="sel", width=3)
        table.add_column("Name", key="name")
        table.add_column("Owner", key="owner")
        table.add_column("Tracks", key="tracks")
        table.display = False
        self.load_playlists()


    def action_refresh(self):
        self.load_playlists()


    # create an exclusive (not async) worker thread to load the user's playlists incase of changes or refresh, we dont want multiple threads trying to do the same thing
    @work(thread=True, exclusive=True)
    def load_playlists(self):
        self.app.call_from_thread(self.set_loading, True)

        try:
            playlists = spotify_client.list_playlists(self.app.sp)
        except Exception as e:
            self.app.call_from_thread(self.on_error, str(e))
            return

        # then populate the table with playlists we got from the task running on the thread
        self.app.call_from_thread(self.populate_table, playlists)


    # loading animations while table is being populated
    def set_loading(self, loading: bool):
        self.query_one("#spinner", LoadingIndicator).display = loading
        self.query_one("#playlist_table", DataTable).display = not loading


    
    # function to raise display error by updating status of the static page
    def on_error(self, message: str):
        self.set_loading(False)
        self.query_one("#status", Static).update(f"[red]Failed to load playlists: {message}[/red]")


    # populate the actual playlists table as a list of dict objects
    def populate_table(self, playlists: list[dict]):

        # start with a clean table 
        table = self.query_one("#playlist_table", DataTable)
        table.clear()

        # if no playlists, tell the user
        if not playlists:
            self.query_one("#status", Static).update("No playlists found.")
            self.set_loading = False
            return

        # show the user's playlists by updatung the status of the static page and what to do after (open or refresh)
        self.query_one("#status", Static).update(
            f"Your Playlists ({len(playlists)}) - Enter to open, r to refresh"
        )

        # now for each each playlist, we want to add the row for each data column, and add them
        # NOTE Textual lets you attach an arbitrary key to each row, so you don't need a separate lookup dict mapping displayed row index ie, playlist ID 
        # event.row_key.value in the selection handler hands that exact playlist_id string back, so we dont guess row position and we dont need a lookup dict
        # the p["owner"] or "" is needed because spotify can return None for display_name, for some reason.
        for p in playlists:
            self.playlist_names[p["id"]] = p["name"]
            table.add_row(
                Text("●" if p["id"] in self.checked else "○"),
                Text(p["name"]), Text(p["owner"] or ""), Text(str(p["track_count"])),
                key=p["id"],
            )

        # no loading indicators and bring autofocus to table
        self.set_loading(False)
        table.focus()


    # when the user actually selects a playlist (by hitting enter key or or cliking the row) we can cache the chosen playlist_id on the app and switch screen to tracks.py
    def on_data_table_row_selected(self, event: DataTable.RowLabelSelected):
        # save playlist_id when a row is clicked, save that as the actual "playlist_id", and switch screens
        playlist_id = event.row_key.value
        self.app.selected_playlist_id = playlist_id
        self.app.selected_playlist_name = self.playlist_names[playlist_id]

        # NOTE potential circular import issue, TEST IT - 06.11.2026
        from tracks import TrackScreen
        self.app.switch_screen(TrackScreen())


    def action_toggle_playlist(self):

        table = self.query_one("#playlist_screen", DataTable)
        if table.row_count == 0:
            return 

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        pid = row_key.value
        self.checked.symmetric_difference_update({pid})
        table.update_cell(pid, "sel", Text("●" if pid in self.checked else "○"))
        self.show_selection_status()


    def action_select_all(self):
        self.checked.update(self.playlist_names)
        self.refresh_marks()


    def action_select_none(self):
        self.checked.clear()
        self.refresh_marks()


    def refresh_marks(self):

        table = self.query_one("#playlist_tbale", DataTable)
        for pid in self.playlist_names:
            table.update_cell(pid, "sel", Text("●" if pid in self.checked else "○"))
        self.show_selection_status()


    def show_selection_status(self):
        self.query_one("#status", Static).update(Text(f"{len(self.checked)} playlist(s) selected - d to download, Enter to pick tracks"))


    def action_download_selected(self):

        if not self.checked:
            self.query_one("#status", Static).update(Text("Nothing selected, toggle playlists with space first.", style="yellow"))
            return

        self.fetch_selected(sorted(self.checked))


    @work(thread=True, exclusive=True, group="fetch")
    def fetch_selected(self, playlist_ids: list[str]):

        # create a list, then for each numbered playlsit in there, and its id from 1, show the number and the name of the playlist and append to the list
        items = []
        try:
            for n, pid in enumerate(playlist_ids, 1):
                name = self.playlist_names[pid]
                self.app.call_from_thread(self.query_one("#status", Static).update(
                    Text(f"Fetching tracks in {n}/{len(playlist_ids)}: {name}")
                ))

                # then for each track in playlist, create a folder with the name of playlist and add tracks in there
                for track in spotify_client.get_tracks(self.app.sp, pid):
                    items.append({**track, "folder": name})
        # catch error and call open_queue function to switch to queue screen for items list
        except Exception as e:
            self.app.call_from_thread(self._on_error, str(e))
            return
        self.app.call_from_thread(self.open_queue, items)


    # the items list is now a bunch of dicts with playlist and name, map the func as such and switch to queuescreen
    def open_queue(self, items: list[dict]):

        self.app.seleted_tracks = items
        from textual_queue import QueueScreen
        self.app.push_screen(QueueScreen())