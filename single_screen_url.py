""" SingleUrlScreen: Download audio from a direct URL (YouTube video or playlist). """

from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Header, Footer, Button, Input, Static, LoadingIndicator
from textual.binding import Binding
from textual import work
import functions
from functions import ConfigStatusBanner


class SingleUrlScreen(Screen):

    CSS = """
    SingleUrlScreen {
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

    LoadingIndicator {
        height: 3;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back to Main Menu", "Back"),
        Binding("q", "quit_app", "Quit"),
    ]

    def compose(self):
        yield Header()
        yield ConfigStatusBanner()
        yield Vertical(
            Static("Download from Single URL", classes="title"),
            Input(placeholder="Paste YouTube video or playlist URL...", id="url_input"),
            Button("Download", variant="primary", id="btn_download"),
            LoadingIndicator(id="spinner"),
            Static("", id="status"),
            Button("Back to Main Menu", id="btn_back"),
            id="container"
        )
        yield Footer()

    def on_mount(self):
        self.query_one("#spinner", LoadingIndicator).display = False

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_download":
            self.start_download()
        elif event.button.id == "btn_back":
            self.action_back()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "url_input":
            self.start_download()

    def start_download(self):
        url = self.query_one("#url_input", Input).value.strip()
        status = self.query_one("#status", Static)

        if not url:
            status.update("[red]Please enter a valid URL.[/red]")
            return

        status.update("Downloading...")
        self.query_one("#spinner", LoadingIndicator).display = True
        self.query_one("#btn_download", Button).disabled = True

        settings = self.app.settings
        self.run_download(
            url,
            settings["format"],
            settings["output_path"],
            settings["cookie_file"]
        )

    @work(thread=True, exclusive=True)
    def run_download(self, url, fmt, out_path, cookie):
        try:
            functions.download_from_url(url, fmt, out_path, cookie)
            self.app.call_from_thread(self.download_complete, True, "Successfully downloaded!")
        except Exception as e:
            self.app.call_from_thread(self.download_complete, False, f"Error: {e}")

    def download_complete(self, success: bool, message: str):
        self.query_one("#spinner", LoadingIndicator).display = False
        self.query_one("#btn_download", Button).disabled = False
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