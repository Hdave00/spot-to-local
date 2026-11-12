""" HubScreen: Central navigation hub for SpotFetch Textual TUI. """

from textual.screen import Screen
from textual.containers import Vertical, Center
from textual.widgets import Header, Footer, Button, Static
from textual.binding import Binding
from functions import ConfigStatusBanner


class HubScreen(Screen):
    
    CSS = """
    HubScreen {
        align: center middle;
    }
    
    #hub-container {
        width: 60;
        height: auto;
        border: solid $border;
        background: $panel;
        padding: 2 4;
        align: center middle;
    }

    .title-banner {
        text-align: center;
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    .subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    # Add bindings for number keys 1 through 5 and quit
    BINDINGS = [
        Binding("1", "goto_exportify", "Exportify CSV"),
        Binding("2", "goto_single_url", "Single URL"),
        Binding("3", "goto_search", "Search"),
        Binding("4", "goto_custom_csv", "Custom CSV"),
        Binding("5", "goto_settings", "Settings"),
        Binding("escape", "back", "Back"),
        Binding("q", "quit_app", "Quit"),
    ]

    def compose(self):
        yield Header()
        yield ConfigStatusBanner()
        yield Center(
            Vertical(
                Static("LSAVE TUI", classes="title-banner"),
                Static("Select a download mode or configure settings", classes="subtitle"),
                Button("1. Exportify CSV Playlists", id="btn_exportify", variant="primary"),
                Button("2. Single URL Download", id="btn_single_url"),
                Button("3. Search & Download", id="btn_search"),
                Button("4. Custom CSV / TuneMyMusic", id="btn_custom_csv"),
                Button("5. Settings", id="btn_settings"),
                id="hub-container"
            )
        )
        yield Footer()

    # Action handlers linked to number key bindings
    def action_goto_exportify(self):
        self.handle_navigation("btn_exportify")

    def action_goto_single_url(self):
        self.handle_navigation("btn_single_url")

    def action_goto_search(self):
        self.handle_navigation("btn_search")

    def action_goto_custom_csv(self):
        self.handle_navigation("btn_custom_csv")

    def action_goto_settings(self):
        self.handle_navigation("btn_settings")

    def handle_navigation(self, btn_id: str):
        if btn_id == "btn_exportify":
            from source_screen import SourceScreen
            self.app.switch_screen(SourceScreen())
        elif btn_id == "btn_single_url":
            from single_screen_url import SingleUrlScreen
            self.app.switch_screen(SingleUrlScreen())
        elif btn_id == "btn_search":
            from search_screen import SearchScreen
            self.app.switch_screen(SearchScreen())
        elif btn_id == "btn_custom_csv":
            # TODO Hook up when ready
            pass
        elif btn_id == "btn_settings":
            from settings_screen import SettingsScreen
            self.app.switch_screen(SettingsScreen())

    def action_quit_app(self):
        self.app.exit(message="Thank you for using Lsave. Goodbye!")