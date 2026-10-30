""" Tracks screen, auto-fetches the selected playlist's tracks, lets the user search/filter, toggle individual tracks, and hand the selection to queue.py. 
    Selection is stored as a set of indices, not row state, so it doesnt get lost in filtering. """
 
from rich.text import Text
from textual import work
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Input, LoadingIndicator, Static
 
import spotify_client

# global toggle indicator
CHECKED = "●"
UNCHECKED = "○"


# screen tracking class under which, all functionality for the Screen object can be manipulated
# NOTE -- 1. "self" here is THE SCREENS OWN STATE SO USE '_' FOR INTERNAL HELPERS
# -- 2. "compose()" DECLARES THE WIDGETS
# -- 3. "on_<something>" and "action_<something>" METHODS ARE TEXTUAL'S OWN EVENT HANDLERS 
class TrackScreen(Screen):
        
    CSS = """
    TracksScreen {
        align: center middle;
    }
    #status {
        text-align: center;
        margin: 1;
    }
    #search {
        margin: 0 1;
    }
    """

    # set a list of instantiated Binding objects that maps a key to an action
    BINDINGS = [
        Binding("space", "toggle_track", "Toggle"),
        Binding("a", "select_all", "All (shown)"),
        Binding("n", "select_none", "None"),
        Binding("slash", "focus_search", "Search"),
        Binding("d", "download", "Download"),
        Binding("escape", "back", "Back"),

    ]

    # intialise the keys and values that will be kept track of ie, list of dicts of tracks, a set of indices of how many are selected and a "filter-by" string
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._tracks: list[dict] = []
        self._selected: set[int] = set()  # indices into self._tracks
        self._filter: str = ""


    # create a vertical widget with placeholders for laoding tracks, searching stuff as input and a DataTable object with selectable rows anda Footer for listing active
    # keys automatically
    def compose(self):

        yield Vertical(
            Static("Loading tracks...", id="status"),
            Input(placeholder="Search title / artist / album  (press /)", id="search"),
            LoadingIndicator(id="spinner"),
            DataTable(id="track_table", cursor_type="row"),
        )
        yield Footer()


    # show data table on mount with the columns of title, artist and album
    def on_mount(self):

        table = self.query_one("#track_table", DataTable)
        table.add_column("", key="sel", width=3)
        table.add_column("Title", key="title")
        table.add_column("Artist", key="artist")
        table.add_column("Album", key="album")
        table.display = False
        self.query_one("#search", Input).display = False
        self.load_tracks()

    # NOTE - Loading Section -

    # create a thread for loading tracks, acount for errors, load the tracks, and show the relevant animations
    @work(thread=True, exclusive=True)
    def load_tracks(self):
        self.app.call_from_thread(self._set_loading, True)

        try: 
            tracks = spotify_client.get_tracks(
                self.app.sp, self.app.selected_playlist_id
            )
        except Exception as e:
            self.app.call_from_thread(self._on_error, str(e))
            return

        self.app.call_from_thread(self._on_loaded, tracks)

    # during laoding show the spinners and loading
    def _set_loading(self, loading: bool):

        # show spinner for page loading only
        self.query_one("#spinner", LoadingIndicator).display = loading
        self.query_one("#track_table", DataTable).display = not loading
        self.query_one("#search", Input).display = not loading

    # error handler function
    def _on_error(self, message: str):

        # remove loading but NOTE -- useing Text() so brackets in the error message aren't parsed as markup, because "somg [remastered]" will be parsed as markup
        self._set_loading(False)

        self.query_one("#status", Static).update(
            Text(f"Failed to load tracks: {message}", style="red")
        )


    # when loaded, show tracks as list of dicts and populate DataTable
    def _on_loaded(self, tracks: list[dict]):
        
        # save tracks object, use the selected tracks as a set (avoid duplication), and filter is empty to start
        self._tracks = tracks
        self._selected = set()
        self._filter = ""
        self._set_loading(False)
        self._render_table()
        self.query_one("#track_table", DataTable).focus()


    # NOTE - Rendering Section -

    # Rendering the datatable and the playlists, tracks and songs therein.
    def _visible_indices(self) -> list[int]:

        """returns a filtered list of track names, artist names and album names for the filter query"""

        # normalise the filter params, if no results found, return a list of all existing tracks
        results = self._filter.lower()
        if not results:
            return list(range(len(self._tracks)))

        # save the output in a list, enumerate the tracks so far and iterate over indices in list of dicts(for tracks) and if they exist after filtering, append them to final list
        # here, 'i' gives us the the position of the track and 't' is the track dict at that position, then we get the track name at that index, join it with artist names and
        # album name and append to new list as a list of dicts (to preserv data struct) which we can then, read its field with to populate data table.
        output = [] 
        for i, t in enumerate(self._tracks):
            unfiltered = " ".join(
                [t["track_name"], ", ".join(t["artist_names"]), t.get("album_name") or ""]
            ).lower()

            if results in unfiltered:
                output.append(i)

        return output

    # render the table with the right data
    def _render_table(self):

        table = self.query_one("#track_table", DataTable)
        table.clear()
        visible = self._visible_indices

        # for each result that was returned in filtered tracks, get the ith index of the track and add it to the table rows
        for i in visible:
            t = self._tracks[i]
            # using "Text()" to avoid Song [Remastered] being treated as markup tags, just need plain text. Use UNCHECKED and CHECKED global variables to enable marking.
            table.add_row(
                Text(CHECKED if i in self._selected else UNCHECKED),
                Text(t["track_name"]),
                Text(", ".join(t["artist_names"])),
                Text(t.get("album_name") or ""),
                key=str(i),

            )
        self._update_status(len(visible))


    # now update the status of the widget to show changes
    def _update_status(self, shown: int | None = None):

        # if the number of rows to add is none(no CHECKED or UNCHECKED), then just return the previous rows 
        if shown is None:
            shown = len(self._visible_indices())

        # else we update the Datatable status and prompt user for further action 
        self.query_one("#status", Static).update(
                        Text(f"{len(self._selected)} selected · showing {shown}/{len(self._tracks)}"
                                "   (space toggle, / search, d download, esc back)")
        )


    # NOTE - Actions Section -

    # actions for buttons pressed next, start with getting the index of current selection
    def _current_index(self) -> int | None:

        # query the table and if no rows exist (data isnt populated) return None
        table = self.query_one("#track_table", DataTable)
        if table.row_count == 0:
            return None

        # now for each row and key in row, we need to get coordinates and map to cell key, and return the that index row_key's value as int
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        return int(row_key.value)


    # set the toggle function that should get current id, from the current index (get the track details where the user is at to enable CHECKED or UNCHECKED)
    def action_toggle_track(self):

        idx = self._current_index()
        if idx is None:
            return

        # xor the values of different selected indexes using built in function to update the all selected indexes and update the overall selected/unselected status
        # of the DataTable object
        self._selected.symmetric_difference_update({idx})
        table = self.query_one("#track_table", DataTable)
        table.update_cell(
            str(idx), 'sel', Text(CHECKED if idx in self._selected else UNCHECKED)
        )
        
        self._update_status()


    # when selected called prev func
    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        # let Enter button enable selection
        self.action_toggle_track()


    # show all visible incides ie, show all selected options
    def action_select_all(self):

        # function only affects currently shown
        self._selected.update(self._visible_indices())
        self._render_table()


    # if nothing selected, clear selected and render table
    def action_selected_none(self):
        self._selected.clear()
        self._render_table()


    def action_focus_search(self):
        self.query_one('#search', Input).focus()


    # handle changes to search input, strip string and render matches
    def on_input_changed(self, event: Input.Changed):

        if event.input.id == "search":
            self._filter = event.value.strip()
            self._render_table()


    # after search, return focus to track table
    def on_input_submitted(self, event: Input.Submitted):

        self.query_one("#track_table", DataTable).focus()


    # download selected tracks
    def action_download(self):

        # if nothing selected, show message and stop
        if not self._selected:
            self.query_one('#status', Static).update(
                Text("Nothing selected, toggle/select tracks with space first.", style="yellow")
            )
            return

        # if there are tracks, then for all tracks in the selections, push the tracks, so the queue keeps the selection intact
        self.app.selected_tracks = [self._tracks[i] for i in sorted(self.selected)]
        self.app.push_screen("queue")


    # finally, switch the screen to to the "playlists" from the track table selection. Only do this if focus is not on the search input, if it does, show track table and stop
    def action_back(self):

        search = self.query_one("#search", Input)
        if search.has_focus:
            self.query_one("#track_table", DataTable).focus()
            return

        self.app.switch_screen("playlists")
