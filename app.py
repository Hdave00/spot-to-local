""" Main application entry point for Lsave Textual TUI. """

from textual.app import App
from hub_screen import HubScreen

class LsaveApp(App):
    
    # shared monotone CSS globally across the app
    CSS = """
    Screen {
        background: #111111;
        color: #e0e0e0;
    }
    Header {
        dock: top;
        background: #1c1c1c;
        color: #ffffff;
        text-style: bold;
    }
    Footer {
        dock: bottom;
        background: #1c1c1c;
        color: #888888;
    }
    Button {
        background: #2a2a2a;
        color: #ffffff;
        border: none;
        padding: 1 2;
    }
    Button:hover {
        background: #444444;
        color: #ffffff;
    }
    Button.-primary {
        background: #ffffff;
        color: #111111;
        text-style: bold;
    }
    Input {
        background: #1c1c1c;
        border: solid #444444;
        color: #ffffff;
    }
    Input:focus {
        border: solid #ffffff;
    }
    DataTable {
        background: #111111;
        color: #e0e0e0;
        border: solid #333333;
    }
    DataTable > .datatable--header {
        background: #1c1c1c;
        color: #ffffff;
        text-style: bold;
    }
    DataTable > .datatable--cursor {
        background: #333333;
        color: #ffffff;
    }
    Static {
        color: #e0e0e0;
    }
    """

    def __init__(self):
        super().__init__()

        # initialize global app state 
        self.settings = {
            'format': 'mp3',
            'output_path': '.',
            'cookie_file': None,
            'platform': 'ytmusic'
        }
        self.csv_folder = None
        self.selected_csv_path = None
        self.selected_playlist_name = None
        self.selected_tracks: list[dict] = []

    def on_mount(self):

        # push the central navigation hub on startup instead of Rich menu
        self.push_screen(HubScreen())

if __name__ == "__main__":
    app = LsaveApp()
    app.run()