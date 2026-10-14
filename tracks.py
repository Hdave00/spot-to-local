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

    