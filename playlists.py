""" Playlists screen that lists the logged-in user's playlists in a DataTable. Selecting one stores its id on the app and advances to tracks.py. """

from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Static, DataTable, LoadingIndicator
from textual.binding import Binding
from textual import work
from rich.text import Text

import batch_download, functions

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
        Binding("a", "select_all", "Select All"),
        Binding("n", "select_none", "Select None"),
        Binding("i", "invert_selection", "Invert"),
        Binding("d", "download_selected", "Download Selected"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit_app", "Quit"),
    ]

    # new init for keying off the filename, not API ids
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        # name -> path
        self.csv_paths: dict[str, str] = {}
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
        table.display = False
        self.load_playlists()


    def action_refresh(self):
        self.load_playlists()


    # create an exclusive (not async) worker thread to load the user's playlists incase of changes or refresh, we dont want multiple threads trying to do the same thing
    @work(thread=True, exclusive=True)
    def load_playlists(self):
        self.app.call_from_thread(self.set_loading, True)

        try:
            files = batch_download.list_csv_files(self.app.csv_folder)
        except Exception as e:
            self.app.call_from_thread(self.on_error, str(e))
            return

        # then populate the table with playlists we got from the task running on the thread
        self.app.call_from_thread(self.populate_table, files)


    # loading animations while table is being populated
    def set_loading(self, loading: bool):
        self.query_one("#spinner", LoadingIndicator).display = loading
        self.query_one("#playlist_table", DataTable).display = not loading


    
    # function to raise display error by updating status of the static page
    def on_error(self, message: str):
        self.set_loading(False)
        self.query_one("#status", Static).update(Text(f"Failed to load playlists: {message}", style="red"))


    # populate the actual playlists table as a list of dict objects
    def populate_table(self, files: list[dict]):

        # start with a clean table 
        table = self.query_one("#playlist_table", DataTable)
        table.clear()

        # if no CSVs, tell the user
        if not files:
            self.query_one("#status", Static).update("No CSVs found.")
            self.set_loading(False)
            return

        # show the user's playlists by updatung the status of the static page and what to do after (open or refresh)
        self.query_one("#status", Static).update(
            Text(f"Your CSVs ({len(files)}) - Enter to open, space to select, d to download selected"))       

        # NOTE Row key is now the (cleaned) filename
        for f in files:
            self.csv_paths[f["name"]] = f["path"]
            table.add_row(
                Text("●" if f["name"] in self.checked else "○"),
                Text(f["name"]),
                key=f["name"],
            )

        # no loading indicators and bring autofocus to table
        self.set_loading(False)
        table.focus()


    # on_data_table_row_selected, runs off the method name, its a different event and it only fires when a row label is clicked, which this table doesn’t use   
    def on_data_table_row_selected(self, event: DataTable.RowLabelSelected):

        # set the name to the row chosen, and get the path tied to the CSV name, then once its selected, take the user to the tracks therein
        name = event.row_key.value
        self.app.selected_csv_path = self.csv_paths[name]
        self.app.selected_playlist_name = name
        from tracks import TrackScreen
        self.app.switch_screen(TrackScreen())


    def action_toggle_playlist(self):

        table = self.query_one("#playlist_table", DataTable)
        if table.row_count == 0:
            return 

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        pid = row_key.value
        self.checked.symmetric_difference_update({pid})
        table.update_cell(pid, "sel", Text("●" if pid in self.checked else "○"))
        self.show_selection_status()


    def action_select_all(self):
        self.checked.update(self.csv_paths)
        self.refresh_marks()


    def action_invert_selection(self):
        all_pids = set(self.csv_paths.keys())
        self.checked = all_pids - self.checked
        self.refresh_marks()


    def action_back(self):
        from source_screen import SourceScreen
        self.app.switch_screen(SourceScreen())


    def action_quit_app(self):
        self.app.exit(message="Thank you for using Lsave. Goodbye!")


    def action_select_none(self):
        self.checked.clear()
        self.refresh_marks()


    def refresh_marks(self):

        table = self.query_one("#playlist_table", DataTable)
        for pid in self.csv_paths:
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
    def fetch_selected(self, names: list[str]):

        # create a list, then for each numbered name in there, and its id from 1, show the number and the name of the csv and append to the list
        items = []
        try:
            for n, name in enumerate(names, 1):
                path = self.csv_paths[name]
                self.app.call_from_thread(
                    self.query_one("#status", Static).update,
                    Text(f"Reading {n}/{len(names)}: {name}"),
                )

                # then for each track in csv, create a folder with the name of csv playlist and add tracks in there
                for track in functions.read_exportify_csv_file(path):
                    items.append({**track, "folder": name})
        # catch error and call open_queue function to switch to queue screen for items list
        except Exception as e:
            self.app.call_from_thread(self.on_error, str(e))
            return
        self.app.call_from_thread(self.open_queue, items)


    # the items list is now a bunch of dicts with playlist and name, map the func as such and switch to queuescreen
    def open_queue(self, items: list[dict]):

        self.app.selected_tracks = items
        from textual_queue import QueueScreen
        self.app.push_screen(QueueScreen())