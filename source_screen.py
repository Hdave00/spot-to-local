"""Entry screen, user authenticates in exportify inside Exportify itself, in their own browser.
This screen only opens Exportify and then takes the folder where the exported CSV(s) landed."""

import os
import webbrowser

from rich.text import Text
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static, Header, Footer
from textual.binding import Binding
from functions import ConfigStatusBanner


EXPORTIFY_URL = "https://exportify.net"


class SourceScreen(Screen):

    CSS = """
    SourceScreen {
        align: center middle;
    }

    #container {
        width: 65;
        height: auto;
        border: solid #333333;
        background: #1c1c1c;
        padding: 2 4;
    }

    #banner {
        text-align: center;
        color: #ffffff;
        text-style: bold;
        margin-bottom: 1;
    }

    #status {
        text-align: center;
        color: #888888;
        margin-bottom: 1;
    }

    #url {
        text-align: center;
        margin: 1 0;
        color: #e0e0e0;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }

    Input {
        margin-bottom: 1;
    }

    #error {
        color: #ff5555;
        text-align: center;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back to Main Menu", "Back"),
        Binding("o", "open_exportify_browser", "Open Exportify"),
        Binding("q", "quit_app", "Quit"),

    ]

    def compose(self):

        yield Header()
        yield ConfigStatusBanner()
        yield Vertical(
            Static("LSAVE", id="banner"),
            Static(
                "Export your playlist(s) from Exportify, save the CSV(s) "
                "somewhere, then point this at that folder.",
                id="status",
            ),
            Static(Text(EXPORTIFY_URL, style="underline"), id="url"),
            Button("1. Open Exportify in Browser", variant="primary", id="open_exportify"),
            Input(placeholder="Path to folder with your CSV(s)", id="folder"),
            Button("Continue to Playlists", id="continue", variant="default"),
            Button("Back to Main Menu", id="btn_back"),
            Static("", id="error"),
            id="container"
        )
        yield Footer()

    def on_mount(self):
        # user can trigger it explicitly via button or 'o' key.
        pass


    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "open_exportify":
            self.action_open_exportify_browser()
        elif event.button.id == "continue":
            self.try_continue()
        elif event.button.id == "btn_back":
            self.action_back()


    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "folder":
            self.try_continue()


    def action_open_exportify_browser(self):

        """Explicitly opens Exportify in the default system web browser."""
        try:
            webbrowser.open(EXPORTIFY_URL)
        except webbrowser.Error:
            pass
    

    def try_continue(self):

        # check for folders update with any errors
        folder = self.query_one("#folder", Input).value.strip()
        error = self.query_one("#error", Static)

        if not folder or not os.path.isdir(folder):
            error.update("That folder doesn't exist.")
            return

        # check for csv's in provided folder
        has_csv = any(f.lower().endswith(".csv") for f in os.listdir(folder))
        if not has_csv:
            error.update("No .csv files found in that folder.")
            return

        # update with error if found and switch to playlists screen
        error.update("")
        self.app.csv_folder = folder
        from playlists import PlaylistsScreen
        self.app.switch_screen(PlaylistsScreen())


    def action_back(self):
        from hub_screen import HubScreen
        if isinstance(self, HubScreen):
            self.app.exit(message="Thank you for using Lsave. Goodbye!")
        else:
            self.app.switch_screen(HubScreen())


    def action_quit_app(self):
        self.app.exit(message="Thank you for using Lsave. Goodbye!")