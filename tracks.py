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
# NOTE -- 1. "self" here is THE SCREENS OWN STATE SO USE '_' FOR INTERNAL HELPERS FFS
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
        Binding("space", "toggle", "Toggle"),
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

