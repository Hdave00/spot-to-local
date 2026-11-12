""" SearchScreen: Search and download individual tracks by track and artist name. """

from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Header, Footer, Button, Input, Static, LoadingIndicator
from textual.binding import Binding
from textual import work
import functions
from functions import ConfigStatusBanner


class SearchScreen(Screen):

    CSS = """
    SearchScreen {
        align: center middle;
    }

    #container {
        width: 65;
        height: auto;
        border: solid $border;
        background: $panel;
        padding: 2 4;
    }

    .title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    Input {
        margin-bottom: 1;
    }

    #status {
        margin-top: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back to Hub", "Back"),
        Binding("q", "quit_app", "Quit"),
    ]

    def compose(self):
        yield Header()
        yield ConfigStatusBanner()
        yield Vertical(
            Static("Search & Download Track", classes="title"),
            Input(placeholder="Track name...", id="track_input"),
            Input(placeholder="Artist name...", id="artist_input"),
            Button("Search & Download", variant="primary", id="btn_search"),
            LoadingIndicator(id="spinner"),
            Static("", id="status"),
            Button("Back to Hub", id="btn_back"),
            id="container"
        )
        yield Footer()

    def on_mount(self):
        self.query_one("#spinner", LoadingIndicator).display = False

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_search":
            self.start_search()
        elif event.button.id == "btn_back":
            self.action_back()

    def start_search(self):
        track = self.query_one("#track_input", Input).value.strip()
        artist = self.query_one("#artist_input", Input).value.strip()
        status = self.query_one("#status", Static)

        if not track or not artist:
            status.update("[red]Please enter both track and artist name.[/red]")
            return

        status.update("Searching and downloading...")
        self.query_one("#spinner", LoadingIndicator).display = True
        self.query_one("#btn_search", Button).disabled = True

        song = {
            'track_name': track,
            'artist_name': artist
        }
        
        settings = self.app.settings
        self.run_search_download(
            song,
            settings["format"],
            settings["output_path"],
            settings["cookie_file"],
            settings["platform"]
        )

    @work(thread=True, exclusive=True)
    def run_search_download(self, song, fmt, out_path, cookie, platform):
        try:
            functions.download_from_query(song, fmt, out_path, cookie, platform)
            self.app.call_from_thread(self.search_complete, True, "Successfully downloaded!")
        except Exception as e:
            self.app.call_from_thread(self.search_complete, False, f"Error: {e}")

    def search_complete(self, success: bool, message: str):
        self.query_one("#spinner", LoadingIndicator).display = False
        self.query_one("#btn_search", Button).disabled = False
        status = self.query_one("#status", Static)
        
        if success:
            status.update(f"[green]{message}[/green]")
        else:
            status.update(f"[red]{message}[/red]")

    def action_back(self):
        from hub_screen import HubScreen
        if isinstance(self, HubScreen):
            self.app.exit(message="Thank you for using Lsave. Goodbye!")
        else:
            self.app.switch_screen(HubScreen())

    def action_quit_app(self):
        self.app.exit(message="Thank you for using Lsave. Goodbye!")