""" Playlists screen: lists the logged-in user's playlists in a DataTable.
Selecting one stores its id on the app and advances to tracks.py. """

from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Static, DataTable, LoadingIndicator
from textual import work

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
    BINDINGS = [("r", "refresh", "Refresh")]

    # create prototypes for showing users playlists, show a loading indicatior and a table populated with data rows
    def compose(self):
        yield Vertical(
            Static("Your Playlists", id="status"),
            LoadingIndicator(id="spinner"),
            DataTable(id="playlist_table", cursor_type="row"),
        )


    # then render the table with relevant details
    def on_mount(self):
        table = self.query_one("#playlist_table", DataTable)
        table.add_columns("Name", "Owner", "Tracks")
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
        for p in playlists:
            # row_key = playlist id, so on selection we can map right back 
            table.add_row(p["name"], p["owner"], str(p["track_count"]), key=p["id"])


        # no loading indicators and bring autofocus to table
        self.set_loading(False)
        table.focus()


    # when the user actually selects a playlist (by hitting enter key or or cliking the row) we can cache the chosen playlist_id on the app and switch screen to tracks.py
    def on_data_table_row_selected(self, event: DataTable.RowLabelSelected):
        # save playlist_id when a row is clicked, save that as the actual "playlist_id", and switch screens
        playlist_id = event.row_key.value
        self.app.selected_playlist_id = playlist_id
        self.app.switch_screen("tracks")
